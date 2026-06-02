# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Changes for the upcoming release are kept as individual news fragments in
[`changelog.d/`](changelog.d/) and compiled into this file at release time by
[*towncrier*](https://towncrier.readthedocs.io/). See [docs/changelog.md](docs/changelog.md).

<!-- towncrier release notes start -->

## [0.4.0] - 2026-06-01

### Added

- Add `--localize` canary bisection: when a decoy fires, optionally re-run the inert reviewer over halves of the file to narrow the triggering span to a few lines (recorded as `localized_span` in the event and a `localized_span_json` column in the index, and shown in the `quarantine` summary). On by default when a canary fires; `quarantine --no-localize` skips the extra probe calls. Completes the M3 canary subsystem.
- Add `cscan-helper ingest`, which normalizes Tier-1 scanner output into a user-local `~/cscan/<run-id>/` run (manifest + `report.json` + a readable `report.md` + queryable index) and applies the gate. `scripts/scan.sh` now routes through it, so deterministic scans land in `~/cscan` alongside Tier-2 runs instead of only printing a table.

### Fixed

- Fix unreadable finding tables: long registry rule IDs (e.g. Semgrep's `...dynamic-urllib-use-detected.dynamic-urllib-use-detected`) no longer overflow — duplicate dotted segments are collapsed, the rule is shortened to its last meaningful segments, and the Rule/Location/Message columns now wrap instead of running off-screen.


## [0.3.0] - 2026-06-01

### Added

- Add Strategy-A (Tier-1) hardening: a bundled Semgrep taint-mode rule pack under `config/semgrep/` (untrusted source → shell/eval/exfiltration sinks, Python + JS/TS) that now always runs alongside the auto registry, and a gate-decision module that classifies a run as BLOCK / NEEDS_REVIEW / WARN / CLEAN while keeping Tier-1 authoritative (canary fires and at/above-gate findings BLOCK; the advisory Tier-2 reviewer can only raise to NEEDS_REVIEW, never clear a finding).
- Add Strategy-B (Tier-2) Dual-LLM quarantine reviewer: a per-file map-reduce classifier that spotlights untrusted content in a per-request nonce fence, offers only the sanctioned `submit_verdict` tool plus inert canary decoys, and treats a canary call as a high-signal injection attempt (records a forensic event with harness attribution, forces HUMAN_REVIEW, returns no tool result). Includes an OpenAI-compatible backend (stdlib HTTP — reaches OpenAI/DeepInfra/OpenRouter/Ollama/vLLM by `base_url`), an offline FakeBackend, Tier-1 secret redaction before any cloud call, and a `quarantine` CLI command that reviews a directory into a user-local run store and applies the gate.
- Add the M0 vetting-pipeline foundations: a `[tool.cscan]` configuration loader (defaults → pyproject → user config → env), a user-local run store under `~/cscan/<run-id>/` (file-primary artifacts: manifest, report, canary events, ingested bytes), a *derived but byte-identical-rebuildable* SQLite index (`cscan-helper index rebuild`), and the inert canary tripwire registry with harness fingerprinting from the vendored signature dataset (`cscan-helper canary list` / `canary attribute`).
- Add the gum-driven shell helper libraries (scripts/lib) sourced by the launcher and scanners

### Changed

- Default the Tier-2 file cap to 5 (was 400) as a conservative cost/safety guard — each reviewed file is a separate LLM call. When `CSCAN_LLM_MAX_FILES` is not set, `cscan-helper quarantine` now alerts that the default cap applies and how to raise it.

### Fixed

- Sanitize canary tool names for the OpenAI-compatible API (function names must match `^[a-zA-Z0-9_-]+$`), so decoys like Codex's `multi_tool_use.parallel` no longer cause an HTTP 400. The transform is reversible: a fired decoy still maps back to its canonical name for harness attribution, and names are de-duplicated to avoid collisions.
- Stop `.gitignore` from silently excluding the shell helper libraries: the unanchored `lib/` rule (meant for Python build dirs) also matched `scripts/lib/`. Anchored it to the repo root (`/lib/`, `/lib64/`) and made the CI shell-syntax check tolerant of an empty `scripts/lib/*.sh` glob (it was exiting 127 when the directory was absent).

### Documentation

- Add `docs/canary-tripwires.md` explaining the canary sensor approach (why a decoy fire is high-signal, harness fingerprinting) and how the LLM review is kept from doing any damage — capability removal rather than a sandbox (whitelist-only tools, provider built-in tools disabled, inert handlers).
- Add a short `CLAUDE.md` for AI agents working in the repo: layout, dev commands, the Conventional-Commits + towncrier changelog rules, and the automated release workflow (`cscan release`), pointing to `docs/` for deeper detail.
- Add the project plan and research-backed deferred-backlog docs for the two-tier, injection-resistant repo/skill vetting pipeline (authoritative deterministic gate + Dual-LLM quarantine + canary tripwires with harness fingerprinting), reconciled against the early SPEC: cloud-default-but-pluggable LLM backend, file-primary persistence under ~/cscan with a rebuildable SQLite index, an explicit execution & tool-isolation safety model (capability removal, whitelist-only tools, provider built-in tools disabled), YARA deferred, plus complementary detection approaches that stack with the canary (verdict-corruption probes, honeytokens, CodeQL, design-pattern hardening, cross-model ensemble).


## [0.2.0] - 2026-06-01

### Changed

- initial release
