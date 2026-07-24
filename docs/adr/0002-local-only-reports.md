---
id: ADR-0002
title: Reports stay local; nothing leaves the machine except a configured Tier-2 call or explicit export
date: 2026-07-21
decider: Sean Howard
status: accepted
---

# ADR-0002 — Local-only reports

## Context

`cscan` is run against repositories a user does not trust — often before deciding
whether the code is safe to install or to expose to an agent. Its output (findings,
ingested bytes, canary events) can itself be sensitive: it may contain secrets the
scanners detected, or excerpts of proprietary code under review. Writing results into
the scanned repo, or shipping them off-machine by default, would leak that data and
could tip off an attacker that their payload was caught.

## Decision

**Reports stay local to the user.** Artifacts are written to a user-local store
(default `~/cscan/<run-id>/`) — never into the scanned repository. The human-readable
files (`report.json` / `report.md` / `canary-events.jsonl` / ingested bytes) are the
portable source of truth; the SQLite database is a *derived index*, fully rebuildable
from those files. The **only** data that leaves the machine is:

1. a deliberately-configured **Tier-2 cloud LLM call** (avoidable entirely with the
   local backend, `provider = "local"`), with Tier-1-detected secrets **redacted
   before send**; or
2. an **explicit** user-initiated export.

## Alternatives considered

- **Write a report file into the scanned repo** (next to the code). Rejected — pollutes
  the target, risks committing sensitive findings, and is visible to the untrusted code.
- **Send results to a central service by default.** Rejected — off-machine exfiltration
  of potentially-sensitive findings must be an opt-in, not a default.

## Consequences

- A run is self-contained and shareable on the user's terms: hand someone the run
  directory and `cscan index rebuild` reconstructs an identical queryable index.
- Offline operation is possible end-to-end (local Tier-2 backend + local store).
- Enforced/exercised by tests: `tests/test_store_database.py::test_rebuild_is_byte_identical`,
  `::test_create_open_roundtrip`, `tests/test_vet.py::test_ingest_writes_run_to_store`,
  and secret redaction before any send in `tests/test_quarantine.py::test_redact_masks_secrets`.
