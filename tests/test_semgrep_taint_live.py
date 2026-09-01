"""Live validation of the bundled Semgrep taint pack against labeled fixtures.

Runs the actual `uvx semgrep` binary against fixtures/semgrep/ and checks the
pack fires (or doesn't) exactly where labels.json says it should. This is the
"prove it, don't just assert it's well-formed" counterpart to
test_semgrep_rules.py, which only checks the rule YAML shape and needs no
external binary.

The fixtures live under a top-level fixtures/ dir rather than tests/fixtures/
because Semgrep's own default ignore rules blanket-exclude any path with a
`tests/` segment (confirmed empirically; there's no documented flag to lift
just that exclusion without also disabling all other .semgrepignore handling
via the internal, unstable --x-ignore-semgrepignore-files).

Skips cleanly when `uvx` isn't on PATH (e.g. a machine without uv installed)
so the rest of the suite is unaffected; CI has uv/uvx available via
astral-sh/setup-uv and runs this for real.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from airlock_scan.parsers import parse_sarif

_ROOT = Path(__file__).resolve().parents[1]
_RULES_DIR = _ROOT / "config" / "semgrep"
_FIXTURES_DIR = _ROOT / "fixtures" / "semgrep"
_LABELS_FILE = _FIXTURES_DIR / "labels.json"

pytestmark = pytest.mark.skipif(
    shutil.which("uvx") is None,
    reason="uvx not on PATH; skipping live Semgrep validation",
)


def _load_labels() -> list[dict]:
    return json.loads(_LABELS_FILE.read_text(encoding="utf-8"))["items"]


def _run_semgrep(tmp_path: Path) -> dict:
    """Run only the bundled pack, as SARIF — the format production's own `parse_sarif` expects."""
    out_file = tmp_path / "results.sarif"
    result = subprocess.run(
        [
            "uvx",
            "semgrep",
            "scan",
            "--config",
            str(_RULES_DIR),
            "--sarif",
            "--output",
            str(out_file),
            "--quiet",
            "--disable-version-check",
            # Unlike scanners/semgrep.sh (which scans real, checked-out target
            # repos), Semgrep's default --use-git-ignore mode restricts
            # scanning to git-tracked files. A freshly added fixture that
            # hasn't been `git add`-ed yet would then silently score 0
            # findings and look like a broken rule. Fixture validation must
            # not depend on git index state.
            "--no-git-ignore",
            # Semgrep's default --rewrite-rule-ids prefixes each rule id with
            # its --config directory path (e.g. "config.semgrep.airlock-...").
            # Nothing downstream in airlock_scan relies on that prefix (the
            # gate keys off SARIF severity, not rule id), so disable it here
            # to keep this test's ids matching labels.json exactly.
            "--no-rewrite-rule-ids",
            str(_FIXTURES_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if not out_file.exists():
        pytest.fail(
            f"semgrep produced no SARIF output (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(out_file.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def findings_by_file(tmp_path_factory):
    """One live semgrep run (module-scoped), shared across every parametrized test."""
    tmp_path = tmp_path_factory.mktemp("semgrep-live")
    sarif = _run_semgrep(tmp_path)
    findings = parse_sarif(sarif, tool="semgrep")
    by_file: dict[str, list] = {}
    for finding in findings:
        if not finding.file:
            continue
        by_file.setdefault(Path(finding.file).as_posix(), []).append(finding)
    return by_file


def _findings_for(by_file: dict, rel_path: str) -> list:
    # SARIF artifact URIs may be relative to the scan target or to the
    # invocation cwd depending on semgrep version/platform, so match on the
    # normalized suffix rather than requiring exact equality.
    target = Path(rel_path).as_posix()
    matches = []
    for key, findings in by_file.items():
        if key == target or key.endswith("/" + target):
            matches.extend(findings)
    return matches


@pytest.mark.parametrize("item", _load_labels(), ids=lambda it: it["path"])
def test_fixture_matches_expected_findings(item, findings_by_file):
    hits = _findings_for(findings_by_file, item["path"])
    fired_rules = {f.rule_id for f in hits}

    for expected_rule in item["expect_fires"]:
        assert expected_rule in fired_rules, (
            f"{item['path']}: expected {expected_rule!r} to fire, "
            f"but got {sorted(r for r in fired_rules if r)}"
        )
        if item.get("sink_line") is not None:
            lines = {f.line for f in hits if f.rule_id == expected_rule}
            assert item["sink_line"] in lines, (
                f"{item['path']}: {expected_rule!r} fired but not at line "
                f"{item['sink_line']} (got {sorted(lines)})"
            )

    if not item["expect_fires"]:
        airlock_rules = {r for r in fired_rules if r and r.startswith("airlock-")}
        assert not airlock_rules, (
            f"{item['path']}: expected no airlock findings, got {sorted(airlock_rules)}"
        )
