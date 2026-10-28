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

import pytest

from _semgrep_support import (
    RULES_DIR,
    load_labels,
    matches_path,
    requires_uvx,
    run_semgrep_over_fixtures,
)
from airlock_scan.parsers import parse_sarif

pytestmark = requires_uvx


@pytest.fixture(scope="module")
def findings_by_file(tmp_path_factory):
    """One live semgrep run (module-scoped), shared across every parametrized test."""
    out_file = tmp_path_factory.mktemp("semgrep-live") / "results.sarif"
    sarif = run_semgrep_over_fixtures(RULES_DIR, out_file)
    by_file: dict[str, list] = {}
    for finding in parse_sarif(sarif, tool="semgrep"):
        if not finding.file:
            continue
        by_file.setdefault(finding.file, []).append(finding)
    return by_file


def _findings_for(by_file: dict, rel_path: str) -> list:
    return [
        finding
        for reported, findings in by_file.items()
        if matches_path(reported, rel_path)
        for finding in findings
    ]


@pytest.mark.parametrize("item", load_labels(), ids=lambda it: it["path"])
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
