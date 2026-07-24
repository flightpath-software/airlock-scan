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


def _short_rule(rule_id: str | None, *, maxlen: int = 40) -> str:
    """Shorten noisy rule IDs for display.

    Registry rules can be long and even repeat their tail
    (e.g. ``...dynamic-urllib-use-detected.dynamic-urllib-use-detected``). We
    drop consecutive duplicate dotted segments, keep the last two, and cap length.
    """
    if not rule_id:
        return "-"
    rid = rule_id
    if "." in rid:
        parts = rid.split(".")
        deduped: list[str] = []
        for p in parts:
            if not deduped or deduped[-1] != p:
                deduped.append(p)
        rid = ".".join(deduped[-2:])
    if len(rid) > maxlen:
        rid = "…" + rid[-(maxlen - 1):]
    return rid


def _md_cell(value: object) -> str:
    """Escape a value for a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip() or "-"


def render_markdown(
    report: Report,
    *,
    target: str = "",
    verdict_label: str = "",
    generated: str = "",
    file_verdicts: list[dict] | None = None,
    canary_events: list[dict] | None = None,
) -> str:
    """Render a durable, human-readable Markdown report.

    Tier-1 ``report.findings`` are always shown. When ``canary_events`` or
    ``file_verdicts`` are supplied (the unified ``vet`` run), they get their own
    sections — canary fires first, as the highest-signal evidence.
    """
    canary_events = canary_events or []
    file_verdicts = file_verdicts or []

    lines = ["# cscan report", ""]
    if target:
        lines.append(f"- **Target:** `{target}`")
    if generated:
        lines.append(f"- **Generated:** {generated}")
    if verdict_label:
        lines.append(f"- **Verdict:** {verdict_label}")
    lines.append(f"- **Gate:** {report.gate.label}")
    lines.append("")
    lines.append(f"**{report.summary_line()}**")
    lines.append("")

    # Canary tripwires first — a fire is the highest-signal evidence.
    if canary_events:
        lines.append("## ⚠ Canary tripwires (attempted prompt injection)")
        lines.append("")
        lines.append("| Tool | File | Harness | Span | Captured args |")
        lines.append("| --- | --- | --- | --- | --- |")
        for ev in canary_events:
            span = ev.get("localized_span") or {}
            span_txt = (
                f"L{span['start_line']}-{span['end_line']}"
                if span.get("start_line")
                else "-"
            )
            args_txt = _md_cell(ev.get("tool_input"))[:120]
            lines.append(
                f"| {_md_cell(ev.get('tool'))} | {_md_cell(ev.get('file_path'))} "
                f"| {_md_cell(ev.get('harness') or '-')} | {span_txt} | {args_txt} |"
            )
        lines.append("")

    # Tier-1 deterministic findings.
    lines.append("## Tier-1 findings (deterministic)")
    lines.append("")
    if report.findings:
        lines.append("| Severity | Tool | Rule | Location | Message |")
        lines.append("| --- | --- | --- | --- | --- |")
        for f in sorted(report.findings, key=lambda x: x.severity, reverse=True):
            lines.append(
                f"| {f.severity.label} | {_md_cell(f.tool)} | {_md_cell(_short_rule(f.rule_id))} "
                f"| {_md_cell(f.location)} | {_md_cell(f.message or '-')} |"
            )
    else:
        lines.append("_No findings._")

    # Tier-2 advisory flags (only the files that need a human look).
    if file_verdicts:
        flagged = [
            v
            for v in file_verdicts
            if v.get("contains_injection") or str(v.get("status", "")) in {"HUMAN_REVIEW", "NEEDS_REVIEW"}
        ]
        lines.append("")
        lines.append(
            f"## Tier-2 reviewer (advisory) — {len(flagged)} flagged of {len(file_verdicts)} file(s)"
        )
        lines.append("")
        if flagged:
            lines.append("| File | Status | Injection | Confidence | Summary |")
            lines.append("| --- | --- | --- | --- | --- |")
            for v in flagged:
                lines.append(
                    f"| {_md_cell(v.get('file_path'))} | {_md_cell(v.get('status'))} "
                    f"| {'yes' if v.get('contains_injection') else 'no'} "
                    f"| {_md_cell(v.get('confidence'))} | {_md_cell(v.get('summary'))} |"
                )
        else:
            lines.append("_Nothing flagged._")

    for warning in report.warnings:
        lines.append(f"\n> warning: {_md_cell(warning)}")
    return "\n".join(lines) + "\n"


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
        table.add_column("Rule", max_width=40, overflow="fold")
        table.add_column("Location", max_width=30, overflow="fold")
        table.add_column("Message", max_width=60, overflow="fold")
        for f in sorted(report.findings, key=lambda x: x.severity, reverse=True):
            style = _SEVERITY_STYLE.get(f.severity, "")
            table.add_row(
                f"[{style}]{f.severity.label}[/]" if style else f.severity.label,
                f.tool,
                _short_rule(f.rule_id),
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
            f"{f.severity.label:<8} {f.tool:<18} {f.location:<32} "
            f"{_short_rule(f.rule_id):<40} {f.message}"
        )
    for warning in report.warnings:
        lines.append(f"warning: {warning}")
    lines.append(report.summary_line())
    return "\n".join(lines)
