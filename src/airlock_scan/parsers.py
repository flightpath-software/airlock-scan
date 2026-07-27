"""Convert heterogeneous scanner output (SARIF, tool JSON) into unified findings.

Parsing is intentionally defensive: a malformed or unexpected file never raises out of
:func:`load_results_dir`; it is skipped and recorded in the returned ``warnings`` list so
the caller can surface it without aborting the whole report.
"""

from __future__ import annotations

import json
from pathlib import Path

from airlock_scan.findings import Finding, Severity


def _sarif_rule_levels(driver: dict) -> dict[str, object]:
    """Map ruleId -> level/severity declared in a SARIF tool driver."""
    levels: dict[str, object] = {}
    for rule in driver.get("rules", []) or []:
        rid = rule.get("id")
        if not rid:
            continue
        props = rule.get("properties", {}) or {}
        level = (
            (rule.get("defaultConfiguration", {}) or {}).get("level")
            or props.get("security-severity")
            or props.get("severity")
        )
        if level is not None:
            levels[rid] = level
    return levels


def parse_sarif(data: dict, *, tool: str | None = None) -> list[Finding]:
    """Parse a SARIF document into findings.

    ``tool`` overrides the tool name; otherwise it is taken from each run's driver.
    """
    findings: list[Finding] = []
    for run in data.get("runs", []) or []:
        driver = (run.get("tool", {}) or {}).get("driver", {}) or {}
        run_tool = tool or driver.get("name") or "sarif"
        rule_levels = _sarif_rule_levels(driver)

        for result in run.get("results", []) or []:
            rule_id = result.get("ruleId")
            props = result.get("properties", {}) or {}
            raw_level = (
                result.get("level")
                or props.get("security-severity")
                or rule_levels.get(rule_id)
            )
            message = (result.get("message", {}) or {}).get("text", "") or ""

            file_uri: str | None = None
            line: int | None = None
            locations = result.get("locations") or []
            if locations:
                phys = (locations[0] or {}).get("physicalLocation", {}) or {}
                file_uri = (phys.get("artifactLocation", {}) or {}).get("uri")
                line = (phys.get("region", {}) or {}).get("startLine")

            findings.append(
                Finding(
                    tool=run_tool,
                    severity=Severity.parse(raw_level),
                    message=message.strip(),
                    rule_id=rule_id,
                    file=file_uri,
                    line=line,
                )
            )
    return findings


def parse_anti_trojan_source(data: list, *, tool: str = "anti-trojan-source") -> list[Finding]:
    """Parse ``anti-trojan-source --json`` output (list of files with findings)."""
    findings: list[Finding] = []
    for entry in data or []:
        file_path = (entry or {}).get("file")
        for hit in (entry or {}).get("findings", []) or []:
            code_point = hit.get("codePoint", "?")
            name = hit.get("name", "confusable character")
            findings.append(
                Finding(
                    tool=tool,
                    # Invisible/bidi/confusable characters in source are high risk.
                    severity=Severity.HIGH,
                    message=f"{code_point} {name}",
                    rule_id=hit.get("category"),
                    file=file_path,
                    line=hit.get("line"),
                    extra={"column": hit.get("column"), "snippet": hit.get("snippet")},
                )
            )
    return findings


def parse_file(path: Path) -> list[Finding]:
    """Parse a single result file, dispatching by filename/content shape."""
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    stem = path.name.lower()

    if isinstance(data, list):
        # The only list-shaped format we currently emit is anti-trojan-source.
        return parse_anti_trojan_source(data)

    if isinstance(data, dict) and "runs" in data:
        # Prefer the SARIF driver name; fall back to the filename stem only when no
        # run declares one (so e.g. `gitleaks.sarif` -> "gitleaks").
        has_driver_name = any(
            ((run.get("tool", {}) or {}).get("driver", {}) or {}).get("name")
            for run in data.get("runs", []) or []
        )
        tool_hint = None if has_driver_name else (path.stem.replace(".sarif", "") or None)
        return parse_sarif(data, tool=tool_hint)

    raise ValueError(f"unrecognized result format: {stem}")


def load_results_dir(results_dir: Path) -> tuple[list[Finding], list[str]]:
    """Load and merge every result file in ``results_dir``.

    Returns ``(findings, warnings)``. Never raises for per-file problems.
    """
    findings: list[Finding] = []
    warnings: list[str] = []

    if not results_dir.is_dir():
        return findings, [f"results directory not found: {results_dir}"]

    patterns = ("*.sarif", "*.sarif.json", "*.json")
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(results_dir.glob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            try:
                findings.extend(parse_file(path))
            except Exception as exc:  # noqa: BLE001 - keep reporting resilient
                warnings.append(f"{path.name}: {exc}")
    return findings, warnings
