"""Structural validation of the bundled Semgrep taint rule pack.

We can't run Semgrep here (offline), but we can assert the rule files are
well-formed taint rules with the fields airlock relies on. PyYAML is a declared dev
dependency, so a missing install fails loudly instead of quietly skipping these checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

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
    # `semgrep --validate` rejects a YAML alias used as a rule-list item (under
    # pattern-sources or pattern-sinks), while `semgrep scan` and PyYAML both resolve
    # it - so an aliased pack passes every other test here and still fails Semgrep's own
    # validator. Repeat shared blocks instead. This bans anchors and aliases outright,
    # which is stricter than --validate on purpose: one rule beats tracking which
    # placements Semgrep happens to reject. (yaml.compose can't see aliases - it expands
    # them - but the token stream can.)
    used = [
        token
        for token in yaml.scan(path.read_text(encoding="utf-8"))
        if isinstance(token, (yaml.AnchorToken, yaml.AliasToken))
    ]
    assert not used, (
        f"{path.name}:{used[0].start_mark.line + 1} uses a YAML anchor/alias; "
        "`semgrep --validate` rejects them as rule-list items - inline the shared block."
    )


def _mentions(node, needle: str) -> bool:
    """Whether any string anywhere under `node` contains `needle`."""
    if isinstance(node, str):
        return needle in node
    if isinstance(node, dict):
        return any(_mentions(value, needle) for value in node.values())
    if isinstance(node, list):
        return any(_mentions(value, needle) for value in node)
    return False


def test_fs_readfile_callback_source_is_identical_across_rules():
    # Aliases can't share this block (see test_rule_files_use_no_yaml_aliases), so it is
    # copied into every rule that uses it, and nothing else would notice one copy
    # drifting: each rule only ever has to match its own fixtures.
    text = (_RULES_DIR / "injection-taint-javascript.yaml").read_text(encoding="utf-8")
    blocks = {}
    for rule in yaml.safe_load(text)["rules"]:
        found = [src for src in rule["pattern-sources"] if _mentions(src, "fs.readFile(")]
        assert len(found) <= 1, f"{rule['id']} has {len(found)} fs.readFile(...) source blocks"
        if found:
            blocks[rule["id"]] = found[0]
    assert len(blocks) > 1, "expected the fs.readFile callback source in more than one rule"

    (first_id, first), *rest = blocks.items()
    for rule_id, block in rest:
        assert block == first, (
            f"the fs.readFile callback source differs between {first_id} and {rule_id} - "
            "keep the copies identical."
        )
