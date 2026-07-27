"""Tests for the canary decoy registry and harness fingerprinting."""

from __future__ import annotations

from airlock_scan.canary import attribute, build_canary_set, load_signatures


def test_dataset_loads():
    sigs = load_signatures()
    ids = {h["id"] for h in sigs["harnesses"]}
    assert {"claude_code", "codex_cli", "cursor", "cline"} <= ids


def test_build_set_includes_harness_and_agnostic():
    tools = build_canary_set(("claude_code",), include_agnostic=True)
    names = {t.name for t in tools}
    assert "Bash" in names          # claude_code distinctive tool
    assert "execute_shell" in names  # agnostic decoy
    # agnostic-sourced tool is tagged as such
    shell = next(t for t in tools if t.name == "execute_shell")
    assert shell.source == "agnostic"
    assert shell.action_class == "execute"


def test_no_agnostic_excludes_generic_set():
    tools = build_canary_set(("claude_code",), include_agnostic=False)
    names = {t.name for t in tools}
    assert "send_email" not in names


def test_attribute_harness_specific():
    # run_terminal_cmd is a Cursor fingerprint tool.
    attr = attribute("run_terminal_cmd")
    assert attr.specificity == "harness-specific"
    assert attr.fingerprints == "cursor"
    assert attr.action_class == "execute"


def test_attribute_codex_apply_patch():
    attr = attribute("apply_patch")
    assert attr.fingerprints == "codex_cli"


def test_attribute_pascalcase_claude():
    attr = attribute("Bash")
    assert attr.fingerprints == "claude_code"


def test_attribute_agnostic_name():
    # read_file is exposed by many harnesses → not a fingerprint.
    attr = attribute("read_file")
    assert attr.specificity == "harness-agnostic"
    assert attr.fingerprints is None
    assert len(attr.harnesses_exposing) > 1


def test_attribute_unknown_name():
    attr = attribute("totally_made_up_tool")
    assert attr.specificity == "unknown"
    assert attr.fingerprints is None
