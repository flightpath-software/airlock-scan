"""Structural validation of the bundled Semgrep taint rule pack.

We can't run Semgrep here (offline), but we can assert the rule files are
well-formed taint rules with the fields airlock relies on. Skipped without PyYAML.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_RULES_DIR = Path(__file__).resolve().parents[1] / "config" / "semgrep"
_RULE_FILES = sorted(_RULES_DIR.glob("*.yaml"))


def test_rule_files_present():
    names = {p.name for p in _RULE_FILES}
    assert "injection-taint-python.yaml" in names
    assert "injection-taint-javascript.yaml" in names


@pytest.mark.parametrize("path", _RULE_FILES, ids=lambda p: p.name)
def test_rules_are_well_formed_taint_rules(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "rules" in doc and doc["rules"], f"{path.name} has no rules"
    ids = set()
    for rule in doc["rules"]:
        assert rule["id"].startswith("airlock-"), "rule ids should be namespaced"
        assert rule["id"] not in ids, "duplicate rule id"
        ids.add(rule["id"])
        assert rule["mode"] == "taint"
        assert rule["languages"]
        assert rule["severity"] == "ERROR"  # -> HIGH in the finding model
        assert rule["pattern-sources"]
        assert rule["pattern-sinks"]
        assert rule.get("metadata", {}).get("airlock") == "taint"


@pytest.mark.parametrize("path", _RULE_FILES, ids=lambda p: p.name)
def test_rule_files_use_no_yaml_aliases(path):
    # `semgrep --validate` rejects YAML anchors/aliases in a rule file, while
    # `semgrep scan` and PyYAML both resolve them - so an aliased pack passes every
    # other test here and still fails Semgrep's own validator. Repeat shared blocks
    # instead. (yaml.compose can't see this: it expands aliases; the token stream can.)
    used = [
        token
        for token in yaml.scan(path.read_text(encoding="utf-8"))
        if isinstance(token, (yaml.AnchorToken, yaml.AliasToken))
    ]
    assert not used, (
        f"{path.name}:{used[0].start_mark.line + 1} uses a YAML anchor/alias, which "
        "`semgrep --validate` rejects - inline the shared block instead."
    )
