"""Aggregate findings into a summary, render it, and apply a severity gate."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from code_scanner.findings import Finding, Severity

_SEVERITY_STYLE = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "cyan",
    Severity.INFO: "dim",
    Severity.UNKNOWN: "dim",
}


@dataclass(slots=True)
class Report:
    """A merged set of findings plus a gate decision."""

    findings: list[Finding]
    gate: Severity
    warnings: list[str]

    @property
    def counts(self) -> Counter:
        return Counter(f.severity for f in self.findings)

    @property
    def max_severity(self) -> Severity:
        return max((f.severity for f in self.findings), default=Severity.UNKNOWN)

    @property
    def blocking(self) -> list[Finding]:
        return [f for f in self.findings if f.severity >= self.gate]

    @property
    def passed(self) -> bool:
        """True when nothing meets or exceeds the gate severity."""
        return not self.blocking

    def summary_line(self) -> str:
        c = self.counts
        parts = [
            f"{c[sev]} {sev.label.lower()}"
            for sev in (
                Severity.CRITICAL,
                Severity.HIGH,
                Severity.MEDIUM,
                Severity.LOW,
                Severity.INFO,
            )
            if c[sev]
        ]
        body = ", ".join(parts) if parts else "no findings"
        verdict = "PASS" if self.passed else "FAIL"
        return f"[{verdict}] {len(self.findings)} finding(s): {body} (gate: {self.gate.label})"


def build_report(
    findings: list[Finding],
    *,
    gate: Severity = Severity.HIGH,
    warnings: list[str] | None = None,
) -> Report:
    return Report(findings=findings, gate=gate, warnings=warnings or [])


def render(report: Report, *, as_json: bool = False) -> str:
    """Render the report to a string (JSON or human-readable)."""
    if as_json:
        import json

        return json.dumps(
            {
                "passed": report.passed,
                "gate": report.gate.label,
                "summary": {sev.label: report.counts[sev] for sev in Severity if report.counts[sev]},
                "findings": [f.as_dict() for f in report.findings],
                "warnings": report.warnings,
            },
            indent=2,
        )

    try:
        return _render_rich(report)
    except Exception:  # noqa: BLE001 - never let rendering crash the gate
        return _render_plain(report)


def _render_rich(report: Report) -> str:
    from io import StringIO

    from rich.console import Console
    from rich.table import Table

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=120)

    if report.findings:
        table = Table(title="code-scanner findings", show_lines=False, expand=False)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Tool", no_wrap=True)
        table.add_column("Rule", no_wrap=True)
        table.add_column("Location")
        table.add_column("Message")
        for f in sorted(report.findings, key=lambda x: x.severity, reverse=True):
            style = _SEVERITY_STYLE.get(f.severity, "")
            table.add_row(
                f"[{style}]{f.severity.label}[/]" if style else f.severity.label,
                f.tool,
                f.rule_id or "-",
                f.location,
                f.message or "-",
            )
        console.print(table)

    for warning in report.warnings:
        console.print(f"[yellow]warning:[/] {warning}")

    verdict_style = "bold green" if report.passed else "bold red"
    console.print(f"[{verdict_style}]{report.summary_line()}[/]")
    return buf.getvalue()


def _render_plain(report: Report) -> str:
    lines: list[str] = []
    for f in sorted(report.findings, key=lambda x: x.severity, reverse=True):
        lines.append(
            f"{f.severity.label:<8} {f.tool:<18} {f.location:<32} {f.rule_id or '-':<24} {f.message}"
        )
    for warning in report.warnings:
        lines.append(f"warning: {warning}")
    lines.append(report.summary_line())
    return "\n".join(lines)
