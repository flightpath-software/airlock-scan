"""Test the `ingest` command: scanner output -> a user-local ~/cscan run."""

from __future__ import annotations

import json

from code_scanner.cli import main
from code_scanner.store import RunStore

SARIF = {
    "version": "2.1.0",
    "runs": [
        {
            "tool": {"driver": {"name": "semgrep"}},
            "results": [
                {
                    "ruleId": "python.lang.security.audit.dynamic-urllib-use-detected",
                    "level": "warning",
                    "message": {"text": "dynamic urllib use"},
                    "locations": [
                        {"physicalLocation": {"artifactLocation": {"uri": "app.py"},
                                              "region": {"startLine": 10}}}
                    ],
                }
            ],
        }
    ],
}


def test_ingest_writes_run_to_store(tmp_path, monkeypatch):
    # raw scanner output
    results = tmp_path / "results"
    results.mkdir()
    (results / "semgrep.sarif").write_text(json.dumps(SARIF), encoding="utf-8")

    # point the user-local store at a temp dir
    store_root = tmp_path / "cscan"
    monkeypatch.setenv("CSCAN_STORE_ROOT", str(store_root))

    rc = main(["ingest", str(results), "--target", "/tmp/suspicious-skill", "--gate", "high"])
    # one MEDIUM finding, gate=high -> WARN -> installable -> exit 0
    assert rc == 0

    runs = list(store_root.iterdir())
    assert len(runs) == 1
    store = RunStore.open(runs[0])

    # report.json captured the finding
    report = store.read_report()
    assert len(report["static_findings"]) == 1
    assert report["static_findings"][0]["tool"] == "semgrep"

    # readable report.md exists with a shortened rule id and the target
    md = store.report_md_path.read_text(encoding="utf-8")
    assert "/tmp/suspicious-skill" in md
    assert "audit.dynamic-urllib-use-detected" in md  # shortened
    assert "# cscan report" in md

    # manifest records the target; index db built
    assert store.read_manifest()["target"] == "/tmp/suspicious-skill"
    assert store.index_db_path.is_file()


def test_ingest_blocks_on_high(tmp_path, monkeypatch):
    high = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "gitleaks"}},
                "results": [
                    {"ruleId": "aws", "level": "error",
                     "message": {"text": "secret"}, "locations": []}
                ],
            }
        ],
    }
    results = tmp_path / "r"
    results.mkdir()
    (results / "gitleaks.sarif").write_text(json.dumps(high), encoding="utf-8")
    monkeypatch.setenv("CSCAN_STORE_ROOT", str(tmp_path / "cscan"))

    rc = main(["ingest", str(results), "--gate", "high"])
    assert rc == 1  # HIGH finding at the gate -> BLOCK -> exit 1
