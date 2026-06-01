"""Derived SQLite index over a run directory.

The index is a *cache*, never the source of truth: it is built entirely from the
files written by :mod:`code_scanner.store`, and the contract (CI-tested) is that
deleting it and running :func:`rebuild_index` reproduces a **byte-identical**
database. That gives a clean sharing story — hand someone a run directory and
they reconstruct the queryable index locally with ``cscan index rebuild``.

Build determinism is achieved by: a fixed page size, a single write transaction,
no AUTOINCREMENT (so no ``sqlite_sequence``), and inserting every table's rows in
a stable sorted order independent of filesystem iteration.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from code_scanner.store import RunStore

SCHEMA = """
CREATE TABLE runs (
    run_id         TEXT PRIMARY KEY,
    schema_version TEXT,
    target         TEXT,
    started_at     TEXT,
    gate           TEXT,
    backend        TEXT,
    model          TEXT,
    cscan_version  TEXT
);
CREATE TABLE static_findings (
    id       INTEGER PRIMARY KEY,
    run_id   TEXT,
    tool     TEXT,
    severity TEXT,
    rule_id  TEXT,
    file     TEXT,
    line     INTEGER,
    message  TEXT
);
CREATE TABLE file_verdicts (
    id                INTEGER PRIMARY KEY,
    run_id            TEXT,
    file_path         TEXT,
    contains_injection INTEGER,
    confidence        REAL,
    status            TEXT,
    summary           TEXT,
    findings_json     TEXT
);
CREATE TABLE ingested_content (
    request_id TEXT PRIMARY KEY,
    run_id     TEXT,
    file_path  TEXT,
    sha256     TEXT,
    size       INTEGER,
    content    BLOB
);
CREATE TABLE canary_events (
    id              INTEGER PRIMARY KEY,
    run_id          TEXT,
    request_id      TEXT,
    file_path       TEXT,
    tool            TEXT,
    harness         TEXT,
    action_class    TEXT,
    tool_input_json TEXT,
    content_sha256  TEXT,
    ts              TEXT
);
"""


def build_index(store: RunStore, db_path: Path) -> Path:
    """Build the SQLite index for ``store`` at ``db_path`` (overwrites)."""
    manifest = store.read_manifest()
    report = store.read_report()
    run_id = manifest.get("run_id", "")

    # Stable orderings so the byte layout is reproducible.
    findings = sorted(
        report.get("static_findings", []),
        key=lambda f: (
            str(f.get("file") or ""),
            int(f.get("line") or 0),
            str(f.get("rule_id") or ""),
            str(f.get("tool") or ""),
            str(f.get("message") or ""),
        ),
    )
    verdicts = sorted(
        report.get("file_verdicts", []),
        key=lambda v: str(v.get("file_path") or ""),
    )
    ingested = sorted(store.iter_ingested(), key=lambda r: str(r.get("request_id") or ""))
    canary = sorted(
        store.iter_canary_events(),
        key=lambda e: (str(e.get("ts") or ""), str(e.get("request_id") or ""), str(e.get("tool") or "")),
    )

    for residue in (db_path, db_path.with_suffix(db_path.suffix + "-wal"),
                    db_path.with_suffix(db_path.suffix + "-journal")):
        residue.unlink(missing_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA page_size = 4096")
        conn.execute("PRAGMA journal_mode = MEMORY")
        conn.executescript(SCHEMA)
        with conn:  # single transaction
            conn.execute(
                "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    manifest.get("schema_version"),
                    manifest.get("target"),
                    manifest.get("started_at"),
                    manifest.get("gate"),
                    manifest.get("backend"),
                    manifest.get("model"),
                    manifest.get("cscan_version"),
                ),
            )
            conn.executemany(
                "INSERT INTO static_findings VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        i,
                        run_id,
                        f.get("tool"),
                        f.get("severity"),
                        f.get("rule_id"),
                        f.get("file"),
                        f.get("line"),
                        f.get("message"),
                    )
                    for i, f in enumerate(findings, start=1)
                ],
            )
            conn.executemany(
                "INSERT INTO file_verdicts VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        i,
                        run_id,
                        v.get("file_path"),
                        1 if v.get("contains_injection") else 0,
                        v.get("confidence"),
                        v.get("status"),
                        v.get("summary"),
                        json.dumps(v.get("findings", []), sort_keys=True),
                    )
                    for i, v in enumerate(verdicts, start=1)
                ],
            )
            conn.executemany(
                "INSERT INTO ingested_content VALUES (?,?,?,?,?,?)",
                [
                    (
                        r.get("request_id"),
                        run_id,
                        r.get("file_path"),
                        r.get("sha256"),
                        r.get("size"),
                        _safe_read_bytes(store, str(r.get("request_id") or "")),
                    )
                    for r in ingested
                ],
            )
            conn.executemany(
                "INSERT INTO canary_events VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    (
                        i,
                        run_id,
                        e.get("request_id"),
                        e.get("file_path"),
                        e.get("tool"),
                        e.get("harness"),
                        e.get("action_class"),
                        json.dumps(e.get("tool_input", {}), sort_keys=True),
                        e.get("content_sha256"),
                        e.get("ts"),
                    )
                    for i, e in enumerate(canary, start=1)
                ],
            )
    finally:
        conn.close()
    # Drop any residual journal so only the .db remains as the artifact.
    for residue in (db_path.with_suffix(db_path.suffix + "-wal"),
                    db_path.with_suffix(db_path.suffix + "-journal")):
        residue.unlink(missing_ok=True)
    return db_path


def rebuild_index(run_dir: Path) -> Path:
    """Rebuild ``<run-dir>/index.db`` from the run's files alone."""
    store = RunStore.open(run_dir)
    return build_index(store, store.index_db_path)


def _safe_read_bytes(store: RunStore, request_id: str) -> bytes:
    try:
        return store.read_ingested_bytes(request_id)
    except OSError:
        return b""
