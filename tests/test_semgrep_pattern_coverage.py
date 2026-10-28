"""Coverage audit: every declared source/sink pattern must be exercised by a fixture.

tests/test_semgrep_taint_live.py proves the bundled fixtures fire correctly, but a
fixture pair only proves the one source/sink pair it exercises. A rule's
`pattern-either` list can (and does) declare more alternates than any single fixture
touches — a typo'd or dead alternate would pass that test, and this repo's CI,
silently, forever (see #75). This test closes that gap: it asserts every
`pattern`/`pattern-inside` alternate declared in config/semgrep/*.yaml is exercised by
at least one *positive* fixture labeled for its own rule.

This is necessarily a coverage proxy, not a taint-flow proof:
- Mechanism: each alternate becomes its own plain *search*-mode probe rule (no taint
  tracking), so "covered" means "this pattern shape appears in a fixture labeled
  positive for this rule" — not "this exact alternate is what made the real taint-mode
  rule fire." test_semgrep_taint_live.py is what proves real dataflow; this test only
  proves the shape isn't dead.
- Ambiguous bare forms: a few patterns are textual substrings of a more specific
  sibling in the same pattern-either (e.g. `process.env` vs `process.env.$X`), so a
  fixture using the specific form would spuriously "cover" the bare one too.
  `_BARE_FORM_EXCLUDES` lists the known cases and excludes the more-specific
  sibling's own occurrences via `pattern-not-inside`.
- `pattern-inside` alternates (introduced by the fs.readFile callback-parameter fix
  for the lexical-containment false positive) are treated the same as `pattern`
  alternates for this audit: both describe a code shape that should appear in some
  fixture, they just play different roles in the real taint-mode rule.
- Alternate kinds it can't turn into a probe (e.g. `pattern-regex`) raise instead of
  being skipped, so a new kind can't slip past the audit unchecked.

Skips cleanly when `uvx` isn't on PATH, mirroring test_semgrep_taint_live.py.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import uv_subprocess_env

yaml = pytest.importorskip("yaml")

_ROOT = Path(__file__).resolve().parents[1]
_RULES_DIR = _ROOT / "config" / "semgrep"
_FIXTURES_DIR = _ROOT / "fixtures" / "semgrep"
_LABELS_FILE = _FIXTURES_DIR / "labels.json"
_RULE_FILES = sorted(_RULES_DIR.glob("*.yaml"))

pytestmark = pytest.mark.skipif(
    shutil.which("uvx") is None,
    reason="uvx not on PATH; skipping live Semgrep pattern-coverage audit",
)

# A pattern that is a textual prefix/substring of a more specific sibling alternate
# in the same pattern-either would be spuriously "covered" by any fixture that
# actually exercises the specific form. List the specific sibling(s) to exclude via
# `pattern-not-inside` so the bare form only counts as covered when some fixture
# genuinely uses the bare shape on its own.
_BARE_FORM_EXCLUDES: dict[str, list[str]] = {
    "process.env": ["process.env.$X"],
    "os.environ": ["os.environ[...]", "os.environ.get(...)"],
}

# The keys _collect_patterns turns into probes, and the keys it can skip because they
# need no fixture of their own: containers, plus constraints/negations that narrow a
# match rather than add an alternate. Any other pattern-*/metavariable-* key raises.
_ALTERNATE_KEYS = {"pattern", "pattern-inside"}
_NON_ALTERNATE_KEYS = {
    "pattern-either",
    "patterns",
    "pattern-not",
    "pattern-not-inside",
    "focus-metavariable",
}


def _load_labels() -> list[dict]:
    return json.loads(_LABELS_FILE.read_text(encoding="utf-8"))["items"]


def _positive_paths_by_rule() -> dict[str, set[str]]:
    positives: dict[str, set[str]] = {}
    for item in _load_labels():
        for rule_id in item["expect_fires"]:
            positives.setdefault(rule_id, set()).add(item["path"])
    return positives


def _collect_patterns(node) -> list[str]:
    """Walk a pattern-sources/pattern-sinks subtree, returning every pattern/pattern-inside string.

    Raises on any other pattern-*/metavariable-* key (e.g. pattern-regex): the audit
    can't turn it into a probe, and skipping it quietly would let an alternate ship
    without a fixture - the exact gap this test exists to close.
    """
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _ALTERNATE_KEYS and isinstance(value, str):
                # YAML block-literal (`|`) values for pattern-inside carry a
                # trailing newline; strip it so probe text and error messages
                # match what a `pattern:` alternate would look like.
                found.append(value.strip())
            elif key.startswith(("pattern", "metavariable")) and key not in (
                _ALTERNATE_KEYS | _NON_ALTERNATE_KEYS
            ):
                raise ValueError(
                    f"unhandled alternate kind {key!r} in config/semgrep: the coverage audit "
                    "can't turn it into a probe, so it would go unchecked. Teach "
                    "_collect_patterns to handle it, or add it to _NON_ALTERNATE_KEYS if it "
                    "needs no fixture of its own."
                )
            else:
                found.extend(_collect_patterns(value))
    elif isinstance(node, list):
        for child in node:
            found.extend(_collect_patterns(child))
    return found


def _build_probes() -> tuple[list[dict], dict[str, tuple[str, str, str]]]:
    """One search-mode probe rule per declared alternate.

    Returns (probe_rules, meta), where meta maps probe id -> (rule_id, role, pattern).
    """
    meta: dict[str, tuple[str, str, str]] = {}
    probes: list[dict] = []
    for rules_file in _RULE_FILES:
        doc = yaml.safe_load(rules_file.read_text(encoding="utf-8"))
        for rule in doc["rules"]:
            for role, key in (("source", "pattern-sources"), ("sink", "pattern-sinks")):
                for pattern in _collect_patterns(rule[key]):
                    probe_id = f"cov-{len(meta)}"
                    meta[probe_id] = (rule["id"], role, pattern)
                    excludes = _BARE_FORM_EXCLUDES.get(pattern)
                    if excludes:
                        probe = {
                            "id": probe_id,
                            "languages": rule["languages"],
                            "severity": "INFO",
                            "message": "coverage probe",
                            "patterns": [{"pattern": pattern}]
                            + [{"pattern-not-inside": excl} for excl in excludes],
                        }
                    else:
                        probe = {
                            "id": probe_id,
                            "languages": rule["languages"],
                            "severity": "INFO",
                            "message": "coverage probe",
                            "pattern": pattern,
                        }
                    probes.append(probe)
    return probes, meta


_PROBES, _META = _build_probes()


def _run_probes(tmp_path: Path) -> dict:
    cfg_file = tmp_path / "probes.yaml"
    out_file = tmp_path / "coverage.sarif"
    cfg_file.write_text(yaml.safe_dump({"rules": _PROBES}), encoding="utf-8")
    result = subprocess.run(
        [
            "uvx",
            "semgrep",
            "scan",
            "--config",
            str(cfg_file),
            "--sarif",
            "--output",
            str(out_file),
            "--quiet",
            "--disable-version-check",
            # Same rationale as test_semgrep_taint_live.py: don't let git-index
            # state or rule-id rewriting affect which probes appear to match.
            "--no-git-ignore",
            "--no-rewrite-rule-ids",
            str(_FIXTURES_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        env=uv_subprocess_env(),
    )
    if not out_file.exists():
        pytest.fail(
            f"semgrep produced no SARIF output (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(out_file.read_text(encoding="utf-8"))


def _matches_path(uri: str, rel_path: str) -> bool:
    uri = uri.replace("\\", "/")
    return uri == rel_path or uri.endswith("/" + rel_path)


@pytest.fixture(scope="module")
def coverage_hits() -> dict[str, bool]:
    """One live semgrep run (module-scoped) covering every declared pattern as its own probe."""
    with tempfile.TemporaryDirectory() as tmp:
        sarif = _run_probes(Path(tmp))
    positives = _positive_paths_by_rule()

    hits: dict[str, bool] = dict.fromkeys(_META, False)
    for run in sarif["runs"]:
        for result in run["results"]:
            probe_id = result["ruleId"]
            if probe_id not in _META:
                continue
            rule_id, _role, _pattern = _META[probe_id]
            uri = result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            if any(_matches_path(uri, path) for path in positives.get(rule_id, set())):
                hits[probe_id] = True
    return hits


@pytest.mark.parametrize("probe_id", list(_META), ids=list(_META))
def test_pattern_is_exercised_by_a_fixture(probe_id, coverage_hits):
    rule_id, role, pattern = _META[probe_id]
    assert coverage_hits[probe_id], (
        f"{rule_id} {role} {pattern!r} is not exercised by any positive fixture "
        f"labeled for {rule_id} in fixtures/semgrep/labels.json - add one."
    )


def test_collect_patterns_rejects_alternate_kinds_it_cannot_probe():
    node = {"pattern-either": [{"pattern": "a(...)"}, {"pattern-regex": "b.*"}]}
    with pytest.raises(ValueError, match="pattern-regex"):
        _collect_patterns(node)


def test_collect_patterns_ignores_containers_and_constraints():
    node = {
        "patterns": [
            {"pattern-inside": "x(...)\n"},
            {"pattern-not": "y(...)"},
            {"focus-metavariable": "$X"},
        ]
    }
    assert _collect_patterns(node) == ["x(...)"]
