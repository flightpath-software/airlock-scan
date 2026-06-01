"""User-local run store — the file-primary, portable source of truth.

Every pipeline invocation gets a directory under the configured store root
(default ``~/cscan/<run-id>/``) containing only human-readable / inspectable
files:

    <store_root>/<run-id>/
      manifest.json          run metadata (target, time, gate, backend, model)
      report.json            static_findings[] + file_verdicts[]
      canary-events.jsonl    one canary (injection-attempt) event per line
      ingested/
        index.jsonl          {request_id, file_path, sha256, size} per line
        <request_id>         exact bytes sent to the model (for traceback)
      index.db               DERIVED SQLite index (rebuildable from the above)

The SQLite index is *derived* and never authoritative: it can be deleted and
rebuilt from these files alone (see :mod:`code_scanner.database`). Nothing here
is ever written into the scanned repo.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "report.json"
CANARY_EVENTS_NAME = "canary-events.jsonl"
INGESTED_DIRNAME = "ingested"
INGESTED_INDEX_NAME = "index.jsonl"
INDEX_DB_NAME = "index.db"


def new_run_id(now: datetime | None = None) -> str:
    """Sortable run id: ``YYYYMMDDTHHMMSSZ-<rand6>`` (UTC + short random suffix)."""
    now = now or datetime.now(timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = os.urandom(3).hex()
    return f"{stamp}-{suffix}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json_atomic(path: Path, obj: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    tmp.replace(path)


class RunStore:
    """Read/write access to a single run directory."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    # --- construction ------------------------------------------------------

    @classmethod
    def create(
        cls,
        store_root: Path,
        *,
        target: str,
        gate: str = "high",
        backend: str = "anthropic",
        model: str = "",
        cscan_version: str = "",
        run_id: str | None = None,
        now: datetime | None = None,
    ) -> "RunStore":
        run_id = run_id or new_run_id(now)
        run_dir = store_root.expanduser() / run_id
        (run_dir / INGESTED_DIRNAME).mkdir(parents=True, exist_ok=True)
        store = cls(run_dir)
        store.write_manifest(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "target": target,
                "started_at": (now or datetime.now(timezone.utc))
                .astimezone(timezone.utc)
                .isoformat(),
                "gate": gate,
                "backend": backend,
                "model": model,
                "cscan_version": cscan_version,
            }
        )
        return store

    @classmethod
    def open(cls, run_dir: Path) -> "RunStore":
        run_dir = run_dir.expanduser()
        if not (run_dir / MANIFEST_NAME).is_file():
            raise FileNotFoundError(f"not a cscan run directory (no manifest): {run_dir}")
        return cls(run_dir)

    # --- paths -------------------------------------------------------------

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / MANIFEST_NAME

    @property
    def report_path(self) -> Path:
        return self.run_dir / REPORT_NAME

    @property
    def canary_events_path(self) -> Path:
        return self.run_dir / CANARY_EVENTS_NAME

    @property
    def ingested_dir(self) -> Path:
        return self.run_dir / INGESTED_DIRNAME

    @property
    def ingested_index_path(self) -> Path:
        return self.ingested_dir / INGESTED_INDEX_NAME

    @property
    def index_db_path(self) -> Path:
        return self.run_dir / INDEX_DB_NAME

    # --- manifest ----------------------------------------------------------

    def write_manifest(self, manifest: dict) -> None:
        _write_json_atomic(self.manifest_path, manifest)

    def read_manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    # --- ingested content (traceback source) -------------------------------

    def record_ingested(self, request_id: str, file_path: str, content: bytes) -> str:
        """Persist the exact bytes sent to the model; return their sha256."""
        self.ingested_dir.mkdir(parents=True, exist_ok=True)
        (self.ingested_dir / request_id).write_bytes(content)
        digest = sha256_bytes(content)
        record = {
            "request_id": request_id,
            "file_path": file_path,
            "sha256": digest,
            "size": len(content),
        }
        with self.ingested_index_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=False) + "\n")
        return digest

    def iter_ingested(self) -> list[dict]:
        return _read_jsonl(self.ingested_index_path)

    def read_ingested_bytes(self, request_id: str) -> bytes:
        return (self.ingested_dir / request_id).read_bytes()

    # --- canary events (highest-signal) ------------------------------------

    def append_canary_event(self, event: dict) -> None:
        with self.canary_events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=False) + "\n")

    def iter_canary_events(self) -> list[dict]:
        return _read_jsonl(self.canary_events_path)

    # --- report (findings + verdicts) --------------------------------------

    def write_report(
        self,
        *,
        static_findings: list[dict] | None = None,
        file_verdicts: list[dict] | None = None,
    ) -> None:
        _write_json_atomic(
            self.report_path,
            {
                "static_findings": static_findings or [],
                "file_verdicts": file_verdicts or [],
            },
        )

    def read_report(self) -> dict:
        if not self.report_path.is_file():
            return {"static_findings": [], "file_verdicts": []}
        return json.loads(self.report_path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out
