# Semgrep taint-pack fixtures

Labeled source→sink fixtures for validating `config/semgrep/injection-taint-*.yaml`
against a live Semgrep run (tracking issue: validate the taint pack with 0 FN on a
labeled set — see `docs/project-plan.md` §4 M1).

Ground truth lives in [`labels.json`](labels.json). Each entry names a fixture file,
the rule ID(s) it must fire (empty for negatives), and — for positives — the line
the sink call sits on, so a test can assert Semgrep fired the right rule at the
right place, not just "something fired."

| Folder | Contains |
|---|---|
| `python/` | Fixtures for `config/semgrep/injection-taint-python.yaml` |
| `javascript/` | Fixtures for `config/semgrep/injection-taint-javascript.yaml` (the `javascript` half) |
| `typescript/` | Fixtures for `config/semgrep/injection-taint-javascript.yaml` (the `typescript` half — same pack, split out to prove Semgrep's TS parser resolves the same source→sink flows) |

Each rule gets a pair of files:

- `*_positive.*` — a real source→sink dataflow the rule must catch.
- `*_negative.*` — a near-miss: the same source and sink functions appear in the
  file, but the tainted value never actually reaches the sink. These exist to
  catch rules that match on co-occurrence instead of true dataflow.

Unlike [`corpus/`](../../corpus), these are not prompt-injection payloads — just
small, intentionally-vulnerable code samples for Semgrep's static dataflow
engine, not for an LLM reviewer. Nothing here is ever executed; `tests/test_semgrep_taint_live.py`
only ever runs Semgrep's static analysis over the source text.
