# Validation — the promises `airlock` keeps, and the code that proves them

`airlock-scan` is a security tool, so its guarantees should be **checkable**, not
asserted. This file records the guarantees the public repo makes and, for each, the
running code that proves it. Lint and passing tests are necessary but not sufficient —
wherever possible a promise is proven by an executable check the CI in
[`.github/workflows/`](.github/workflows/) runs on every PR.

Run the core of the gate locally:

```bash
uv run ruff check .            # lint (line-length 100, py312)
uv run pytest -q               # the full helper test suite
uv build                       # a valid wheel + sdist
uvx bandit -r src -ll          # Python SAST (as CI runs it)
uvx pip-audit -r <(uv export --frozen --format requirements-txt --no-emit-project)
```

## 1 · Engineering hygiene
| Promise | Proof |
|---|---|
| Lint clean | `ruff check .` (`ci.yml` → *lint + test*) |
| Helper tests pass | `pytest -q` — currently 71 tests (`ci.yml`) |
| Shell entry points parse | `bash -n bin/airlock scripts/*.sh scripts/lib/*.sh scanners/*.sh` (`ci.yml`) |
| Lockfile matches the 3-day cooldown policy | `uv lock --locked` (`ci.yml`) |
| Valid wheel + sdist | `uv build` (run locally; a CI build/self-scan step is planned — see README TODO) |

## 2 · The cardinal rule — the deterministic tier is authoritative (ADR-0001)
| Promise | Proof |
|---|---|
| A Tier-1 finding blocks at the gate | `tests/test_gate.py::test_block_on_finding_at_gate` |
| The LLM verdict can never clear a finding or a canary | `tests/test_gate.py::test_canary_wins_even_if_verdict_also_present` |
| A fired canary blocks even with no findings | `tests/test_gate.py::test_block_on_canary_even_without_findings` |
| The gate threshold is honored deterministically | `tests/test_gate.py::test_gate_blocks_high_but_passes_when_threshold_is_critical` |
| End-to-end vet blocks on a high finding | `tests/test_vet.py::test_ingest_blocks_on_high` |

## 3 · Injection-resistant Tier-2 (ADR-0001)
| Promise | Proof |
|---|---|
| One isolated review per file; exactly one canary per tree | `tests/test_quarantine.py::test_review_tree_maps_over_files_and_fires_one_canary` |
| The model sees fenced bytes, not raw content | `tests/test_quarantine.py::test_ingested_bytes_include_the_fence_not_raw` |
| A fired canary forces human review + attributes the harness | `tests/test_canary.py::test_canary_fire_forces_human_review_and_attributes_harness` |
| Generated canary tool names are API-safe | `tests/test_quarantine.py::test_all_generated_tool_names_are_api_safe` |
| Works offline (no key) via the fake backend | `tests/test_llm_backend.py::test_fake_backend_records_calls_and_returns_default_clean` |

## 4 · Local-only, rebuildable output (ADR-0002)
| Promise | Proof |
|---|---|
| Runs are written to the user-local store, not the scanned repo | `tests/test_vet.py::test_ingest_writes_run_to_store` |
| Tier-1-detected secrets are redacted before any Tier-2 send | `tests/test_quarantine.py::test_redact_masks_secrets` |
| The SQLite index rebuilds byte-identically from a run's files | `tests/test_store_database.py::test_rebuild_is_byte_identical` |
| Run directories round-trip | `tests/test_store_database.py::test_create_open_roundtrip` |

## 5 · Supply-chain & data integrity
| Promise | Proof |
|---|---|
| Dependencies carry no known advisories | `pip-audit` (`security.yml`) |
| No Medium+ SAST findings (suppressions are inline `# nosec` + reason) | `bandit -r src -ll` (`security.yml`) |
| No secrets in the diff / history | `gitleaks` (`gitleaks.yml`) |
| Static analysis on every PR | CodeQL (`codeql.yml`) |
| The bundled Semgrep taint rules are well-formed | `tests/test_semgrep_rules.py::test_rules_are_well_formed_taint_rules` |
| The bundled taint pack fires on labeled source→sink fixtures with 0 FN | `tests/test_semgrep_taint_live.py::test_fixture_matches_expected_findings` |
| The packaged harness-signature dataset matches its YAML source | `tests/test_harness_dataset_sync.py::test_packaged_json_matches_yaml` |
