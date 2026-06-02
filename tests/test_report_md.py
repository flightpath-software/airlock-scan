"""Tests for rule-shortening and the Markdown report renderer."""

from __future__ import annotations

from code_scanner.findings import Finding, Severity
from code_scanner.report import _short_rule, build_report, render_markdown


def test_short_rule_dedupes_and_truncates():
    rid = "python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected"
    out = _short_rule(rid)
    # consecutive duplicate tail collapsed, last two segments kept
    assert out == "audit.dynamic-urllib-use-detected"
    assert _short_rule(None) == "-"
    assert _short_rule("a" * 100).startswith("…")


def test_render_markdown_table_and_escaping():
    findings = [
        Finding(tool="semgrep", severity=Severity.HIGH, message="bad | thing\nnext",
                rule_id="a.b.c", file="x.py", line=3),
    ]
    report = build_report(findings, gate=Severity.HIGH)
    md = render_markdown(report, target="/tmp/repo", verdict_label="BLOCK", generated="now")

    assert md.startswith("# cscan report")
    assert "- **Target:** `/tmp/repo`" in md
    assert "- **Verdict:** BLOCK" in md
    assert "| Severity | Tool | Rule | Location | Message |" in md
    # pipe and newline escaped inside the cell
    assert "bad \\| thing next" in md
    assert "x.py:3" in md


def test_render_markdown_no_findings():
    report = build_report([], gate=Severity.HIGH)
    md = render_markdown(report)
    assert "_No findings._" in md
