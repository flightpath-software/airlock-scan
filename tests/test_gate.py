"""Tests for the gate decision logic (Tier-1 authoritative, Tier-2 advisory)."""

from __future__ import annotations

from airlock_scan.findings import Finding, Severity
from airlock_scan.gate import GateVerdict, decide


def _finding(sev: Severity, tool: str = "semgrep") -> Finding:
    return Finding(tool=tool, severity=sev, message="m", rule_id="r")


def test_clean_when_nothing():
    d = decide([], gate=Severity.HIGH)
    assert d.verdict is GateVerdict.CLEAN
    assert d.installable


def test_block_on_finding_at_gate():
    d = decide([_finding(Severity.HIGH)], gate=Severity.HIGH)
    assert d.verdict is GateVerdict.BLOCK
    assert not d.installable


def test_block_on_canary_even_without_findings():
    d = decide([], gate=Severity.HIGH, canary_events=[{"tool": "run_terminal_cmd"}])
    assert d.verdict is GateVerdict.BLOCK
    assert "injection" in d.reasons[-1].lower()


def test_tier2_is_advisory_only_needs_review_not_block():
    d = decide(
        [],
        gate=Severity.HIGH,
        file_verdicts=[{"file_path": "x", "contains_injection": True}],
    )
    assert d.verdict is GateVerdict.NEEDS_REVIEW


def test_tier2_cannot_clear_tier1():
    # A "clean" LLM verdict must not override an authoritative HIGH finding.
    d = decide(
        [_finding(Severity.HIGH)],
        gate=Severity.HIGH,
        file_verdicts=[{"file_path": "x", "contains_injection": False, "status": "CLEAN"}],
    )
    assert d.verdict is GateVerdict.BLOCK


def test_warn_on_sub_gate_finding():
    d = decide([_finding(Severity.MEDIUM)], gate=Severity.HIGH)
    assert d.verdict is GateVerdict.WARN
    assert d.installable


def test_review_status_triggers_needs_review():
    d = decide(
        [],
        gate=Severity.HIGH,
        file_verdicts=[{"file_path": "x", "status": "HUMAN_REVIEW"}],
    )
    assert d.verdict is GateVerdict.NEEDS_REVIEW


def test_highest_precedence_wins():
    d = decide(
        [_finding(Severity.HIGH), _finding(Severity.MEDIUM)],
        gate=Severity.HIGH,
        canary_events=[{"tool": "execute_shell"}],
        file_verdicts=[{"file_path": "x", "contains_injection": True}],
    )
    assert d.verdict is GateVerdict.BLOCK
    # reasons accumulate across categories for the report
    assert len(d.reasons) >= 3
