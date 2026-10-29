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

Each rule declares multiple source/sink patterns (`pattern-either` alternates); a
single fixture pair only proves the one pair it exercises, not that every declared
alternate is reachable. So each rule gets **one or more** pairs, named
`<rule>_<source>_to_<sink>_<polarity>.<ext>` (e.g. `shell_argv_to_ossystem_positive.py`
proves `sys.argv` reaching `os.system(...)` under `airlock-untrusted-input-to-shell`;
the tokens are listed [below](#tokens)):

- `*_positive.*` — a real source→sink dataflow the rule must catch.
- `*_negative.*` — a near-miss: the same source and sink functions appear in the
  file, but the tainted value never actually reaches the sink. These exist to
  catch rules that match on co-occurrence instead of true dataflow.

Every declared source *and* sink pattern needs at least one fixture pair, per rule —
not the full source×sink cross-product, which isn't worth the file count. A rule with
an untested `pattern-either` alternate is a rule that can silently stop firing (a
typo'd pattern) without any test noticing, so `tests/test_semgrep_pattern_coverage.py`
fails when a pattern in `config/semgrep/*.yaml` has no positive fixture for its own
rule (#75). Adding a pattern to a rule means adding its fixtures here.

## Tokens

Each `<source>` and `<sink>` stands for exactly one declared pattern, and each pattern
has exactly one token, so a name says what a fixture exercises without opening it.
Callees keep the module they are written with (`ossystem`, `subprocesscall`,
`requestsget`); a destructured import is named as written, so
`const { spawn } = require("child_process")` is `spawn`. A new pattern gets a new token
here, never a second spelling of an existing one.

**Python sources:** `argv` (`sys.argv`), `input` (`input(...)`), `stdin`
(`sys.stdin.read(...)`), `openread` (`open(...).read(...)`), `getenv` (`os.getenv(...)`),
`environget` (`os.environ.get(...)`), `environsubscript` (`os.environ[...]`), `environ`
(bare `os.environ`).

**Python sinks:** shell: `ossystem` (`os.system`), `ospopen` (`os.popen`),
`subprocessrun`, `subprocesscall`, `subprocesscheckoutput`, `subprocesspopen`
(`subprocess.*`). eval: `eval`, `exec`, `compile`, `import` (`__import__`). exfiltration:
`requestsget`, `requestsput`, `requestspost`, `httpxget`, `httpxpost`, `urlopen`
(`urllib.request.urlopen`), `socketsendall` (`socket.socket(...).sendall(...)`).

**JavaScript / TypeScript sources:** `argv` (`process.argv`), `env` (bare `process.env`),
`envfield` (`process.env.$X`), `readfilesync` (`fs.readFileSync(...)`), `readfilearrow` /
`readfilefunction` (`fs.readFile` with an arrow / `function` callback).

**JavaScript / TypeScript sinks:** exec: `childprocessexec` (`child_process.exec`),
`cpexec` (`cp.exec`), `exec`, `execsync`, `spawn`, `spawnsync`. eval: `eval`, `function`
(`Function(...)`), `newfunction` (`new Function(...)`). exfiltration: `fetch`,
`axiospost`, `axiosget`, `httprequest`, `httpsrequest`.

Unlike [`corpus/`](../../corpus), these are not prompt-injection payloads — just
small, intentionally-vulnerable code samples for Semgrep's static dataflow
engine, not for an LLM reviewer. Nothing here is ever executed; `tests/test_semgrep_taint_live.py`
only ever runs Semgrep's static analysis over the source text.
