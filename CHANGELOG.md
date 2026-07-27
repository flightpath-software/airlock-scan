# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Changes for the upcoming release are kept as individual news fragments in
[`changelog.d/`](changelog.d/) and compiled into this file at release time by
[*towncrier*](https://towncrier.readthedocs.io/). See [docs/changelog.md](docs/changelog.md).

<!-- towncrier release notes start -->

## [0.5.0] - 2026-07-27

### Security

- Add CI security scanning for the project's own supply chain: CodeQL (Python SAST), Bandit, `pip-audit` (OSV dependency audit), and a hardened, checksum-pinned gitleaks secret scan — running on pull requests, on pushes to `main`/`develop`/`staging`, and weekly. CI also now enforces `uv lock --locked` so the lockfile can't drift from the 3-day dependency cooldown.
- Guard the synthetic prompt-injection fixtures in `corpus/`: add a prominent agent-facing warning to `CLAUDE.md`, a new `AGENTS.md`, and `corpus/README.md` instructing any AI agent working in the repo to treat `corpus/adversarial/` and `corpus/targeted/` as inert, untrusted data — never instructions. Exfil targets use reserved `*.example` domains.

### Added

- Add the M5 evaluation harness: a labeled corpus under `corpus/` (clean / trigger-word-heavy clean / adversarial / harness-targeted) and `airlock-helper eval`, which runs the Tier-2 reviewer over the corpus and reports **detection rate**, the headline **canary false-positive rate** on clean/trigger files, and **harness attribution accuracy** (Markdown or `--json`). The backend is pluggable: a real model, an offline `--fake` baseline, or an offline `--heuristic` backend that fires on any tool-name mention to illustrate the over-defense failure mode.
- Add the unified `airlock-helper vet <target> --tier1-results <dir>` command (and `scripts/vet.sh`) that runs the deterministic Tier-1 scanners **and** the Tier-2 quarantined reviewer and merges both into a single `~/airlock/<run-id>/` run with one gated `report.md` — canary fires first, then Tier-1 findings, then Tier-2 advisory flags. Completes the M4 integration milestone.
- Publish `airlock-scan` under the **Apache-2.0** license (`LICENSE`, `pyproject.toml` `license = "Apache-2.0"`). The built wheel/sdist now carry the license and exclude agent-instruction files.
- Wire the pipeline commands into the `airlock` launcher: `airlock vet`, `airlock quarantine`, and `airlock eval` now work from the single launcher (and the interactive gum menu), so you no longer need to call `scripts/*.sh` or `airlock-helper` directly.

### Changed

- Make `~/airlock` run directory ids more human-readable: `YYYYMMDD-<rand6>` (e.g. `20260602-092b9b`) instead of the full timestamp `YYYYMMDDTHHMMSSZ-<rand6>`. Exact intra-day ordering is still available via `started_at` in each run's `manifest.json`.
- Rename the toolkit to **Airlock**. The command is now `airlock` (was `cscan`) with helper `airlock-helper`; the Python package is `airlock_scan` (distribution `airlock-scan`); the config table is `[tool.airlock]`; environment variables use the `AIRLOCK_*` prefix; and the user-local run store moved to `~/airlock/`. This is a breaking rename with no compatibility shim — done deliberately pre-1.0, before the first public release.
- `airlock changelog` now prompts for an optional Linear ticket ID and title, prepending a `[FP-XXX: Title](url)` link to the fragment content. GUI users (Tower, PyCharm) can write the same format by hand in `changelog.d/+slug.type.md`. Fragment filenames are always orphan slugs — the Linear link lives in the content, not the filename.

### Documentation

- Add `docs/project-plan-public.md` — a plan for taking `airlock-scan` public: governance/legal files, `.github` scaffolding, security workflows, Claude skills, a three-branch model (`develop` → `staging` → `main`) with future support for isolated test execution, the GitHub settings a maintainer must apply, and the procedure to flatten `main` into a single initial public-release commit.
- Add four Claude Code skills adapted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT, attributed in `.claude/skills/NOTICE.md`): `code-review` (two-axis Standards + Spec review), `domain-modeling`, `grilling`, and `grill-with-docs`. Also add `docs/CODING_STANDARDS.md` — the canonical coding conventions the `code-review` Standards axis checks against.
- Add public-repository governance and contributor docs: `SECURITY.md` (private vulnerability reporting + security posture), `CONTRIBUTING.md` (with the `develop` → `staging` → `main` branch model), `CODE_OF_CONDUCT.md`, `VALIDATION.md` (promises mapped to the tests that prove them), the first two ADRs, GitHub issue/PR templates + `CODEOWNERS` + Dependabot, and `.claude/skills/` for the changelog and release workflows.

### Misc

- Enable CodeQL result upload now that the repo is public (removed the interim `upload: false`), so code-scanning results populate the Security tab and gate PRs.


## [0.4.0] - 2026-06-01

### Added

- Add `--localize` canary bisection: when a decoy fires, optionally re-run the inert reviewer over halves of the file to narrow the triggering span to a few lines (recorded as `localized_span` in the event and a `localized_span_json` column in the index, and shown in the `quarantine` summary). On by default when a canary fires; `quarantine --no-localize` skips the extra probe calls. Completes the M3 canary subsystem.
- Add `airlock-helper ingest`, which normalizes Tier-1 scanner output into a user-local `~/airlock/<run-id>/` run (manifest + `report.json` + a readable `report.md` + queryable index) and applies the gate. `scripts/scan.sh` now routes through it, so deterministic scans land in `~/airlock` alongside Tier-2 runs instead of only printing a table.

### Fixed

- Fix unreadable finding tables: long registry rule IDs (e.g. Semgrep's `...dynamic-urllib-use-detected.dynamic-urllib-use-detected`) no longer overflow — duplicate dotted segments are collapsed, the rule is shortened to its last meaningful segments, and the Rule/Location/Message columns now wrap instead of running off-screen.


## [0.3.0] - 2026-06-01

### Added

- Add Strategy-A (Tier-1) hardening: a bundled Semgrep taint-mode rule pack under `config/semgrep/` (untrusted source → shell/eval/exfiltration sinks, Python + JS/TS) that now always runs alongside the auto registry, and a gate-decision module that classifies a run as BLOCK / NEEDS_REVIEW / WARN / CLEAN while keeping Tier-1 authoritative (canary fires and at/above-gate findings BLOCK; the advisory Tier-2 reviewer can only raise to NEEDS_REVIEW, never clear a finding).
- Add Strategy-B (Tier-2) Dual-LLM quarantine reviewer: a per-file map-reduce classifier that spotlights untrusted content in a per-request nonce fence, offers only the sanctioned `submit_verdict` tool plus inert canary decoys, and treats a canary call as a high-signal injection attempt (records a forensic event with harness attribution, forces HUMAN_REVIEW, returns no tool result). Includes an OpenAI-compatible backend (stdlib HTTP — reaches OpenAI/DeepInfra/OpenRouter/Ollama/vLLM by `base_url`), an offline FakeBackend, Tier-1 secret redaction before any cloud call, and a `quarantine` CLI command that reviews a directory into a user-local run store and applies the gate.
- Add the M0 vetting-pipeline foundations: a `[tool.airlock]` configuration loader (defaults → pyproject → user config → env), a user-local run store under `~/airlock/<run-id>/` (file-primary artifacts: manifest, report, canary events, ingested bytes), a *derived but byte-identical-rebuildable* SQLite index (`airlock-helper index rebuild`), and the inert canary tripwire registry with harness fingerprinting from the vendored signature dataset (`airlock-helper canary list` / `canary attribute`).
- Add the gum-driven shell helper libraries (scripts/lib) sourced by the launcher and scanners

### Changed

- Default the Tier-2 file cap to 5 (was 400) as a conservative cost/safety guard — each reviewed file is a separate LLM call. When `AIRLOCK_LLM_MAX_FILES` is not set, `airlock-helper quarantine` now alerts that the default cap applies and how to raise it.

### Fixed

- Sanitize canary tool names for the OpenAI-compatible API (function names must match `^[a-zA-Z0-9_-]+$`), so decoys like Codex's `multi_tool_use.parallel` no longer cause an HTTP 400. The transform is reversible: a fired decoy still maps back to its canonical name for harness attribution, and names are de-duplicated to avoid collisions.
- Stop `.gitignore` from silently excluding the shell helper libraries: the unanchored `lib/` rule (meant for Python build dirs) also matched `scripts/lib/`. Anchored it to the repo root (`/lib/`, `/lib64/`) and made the CI shell-syntax check tolerant of an empty `scripts/lib/*.sh` glob (it was exiting 127 when the directory was absent).

### Documentation

- Add `docs/canary-tripwires.md` explaining the canary sensor approach (why a decoy fire is high-signal, harness fingerprinting) and how the LLM review is kept from doing any damage — capability removal rather than a sandbox (whitelist-only tools, provider built-in tools disabled, inert handlers).
- Add a short `CLAUDE.md` for AI agents working in the repo: layout, dev commands, the Conventional-Commits + towncrier changelog rules, and the automated release workflow (`airlock release`), pointing to `docs/` for deeper detail.
- Add the project plan and research-backed deferred-backlog docs for the two-tier, injection-resistant repo/skill vetting pipeline (authoritative deterministic gate + Dual-LLM quarantine + canary tripwires with harness fingerprinting), reconciled against the early SPEC: cloud-default-but-pluggable LLM backend, file-primary persistence under ~/airlock with a rebuildable SQLite index, an explicit execution & tool-isolation safety model (capability removal, whitelist-only tools, provider built-in tools disabled), YARA deferred, plus complementary detection approaches that stack with the canary (verdict-corruption probes, honeytokens, CodeQL, design-pattern hardening, cross-model ensemble).


## [0.2.0] - 2026-06-01

### Changed

- initial release
