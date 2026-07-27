"""Tests for the parsing + gating helper."""

from __future__ import annotations

import json

from airlock_scan.findings import Severity
from airlock_scan.parsers import (
    load_results_dir,
    parse_anti_trojan_source,
    parse_sarif,
)
from airlock_scan.report import build_report

SAMPLE_SARIF = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {"driver": {"name": "gitleaks"}},
            "results": [
                {
                    "ruleId": "aws-access-token",
                    "level": "error",
                    "message": {"text": "AWS access token detected"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": "src/config.py"},
                                "region": {"startLine": 42},
                            }
                        }
                    ],
                }
            ],
        }
    ],
}

SAMPLE_ATS = [
    {
        "file": "src/utils.js",
        "findings": [
            {
                "line": 12,
                "column": 34,
                "codePoint": "U+202E",
                "name": "RIGHT-TO-LEFT OVERRIDE",
                "category": "Cf (Format)",
                "snippet": "if (isAdmin) {",
            }
        ],
    }
]


def test_severity_parse_maps_sarif_and_named_levels():
    assert Severity.parse("error") is Severity.HIGH
    assert Severity.parse("warning") is Severity.MEDIUM
    assert Severity.parse("CRITICAL") is Severity.CRITICAL
    assert Severity.parse("9.1") is Severity.CRITICAL
    assert Severity.parse("garbage") is Severity.UNKNOWN


def test_parse_sarif_extracts_tool_and_location():
    findings = parse_sarif(SAMPLE_SARIF)
    assert len(findings) == 1
    f = findings[0]
    assert f.tool == "gitleaks"
    assert f.rule_id == "aws-access-token"
    assert f.severity is Severity.HIGH
    assert f.location == "src/config.py:42"


def test_parse_anti_trojan_source_is_high_severity():
    findings = parse_anti_trojan_source(SAMPLE_ATS)
    assert len(findings) == 1
    f = findings[0]
    assert f.tool == "anti-trojan-source"
    assert f.severity is Severity.HIGH
    assert "U+202E" in f.message
    assert f.file == "src/utils.js"


def test_load_results_dir_merges_and_warns(tmp_path):
    (tmp_path / "gitleaks.sarif").write_text(json.dumps(SAMPLE_SARIF), encoding="utf-8")
    (tmp_path / "anti-trojan-source.json").write_text(json.dumps(SAMPLE_ATS), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not valid", encoding="utf-8")

    findings, warnings = load_results_dir(tmp_path)
    assert len(findings) == 2
    assert any("broken.json" in w for w in warnings)


def test_gate_blocks_high_but_passes_when_threshold_is_critical():
    findings = parse_sarif(SAMPLE_SARIF)  # one HIGH finding

    failing = build_report(findings, gate=Severity.HIGH)
    assert not failing.passed
    assert failing.blocking

    passing = build_report(findings, gate=Severity.CRITICAL)
    assert passing.passed
    assert not passing.blocking


def test_missing_results_dir_returns_warning(tmp_path):
    findings, warnings = load_results_dir(tmp_path / "does-not-exist")
    assert findings == []
    assert warnings and "not found" in warnings[0]
