# Configuration

Airlock works out of the box with sensible defaults — you only configure it when
you want to change something (point the Tier-2 reviewer at a different LLM
provider, use a local model, move the report store, …).

**You never edit the source.** Defaults live in `src/airlock_scan/config.py`;
you override them from a config file or environment variables. Editing
`config.py` would change the default for *everyone* — that's a maintainer action.

## Where settings come from (precedence)

Later sources win over earlier ones:

1. **Built-in defaults** — in `config.py` (`Config` / `LLMConfig` / …).
2. **Project config** — an explicit file passed with `--config <path>` (or the
   `AIRLOCK_CONFIG` env var); if neither is set, a `[tool.airlock]` table in a
   `pyproject.toml` found by walking up from the **current working directory**.
3. **User config** — `~/airlock/config.toml` (your machine-wide preferences).
4. **Environment variables** — `AIRLOCK_*` (per-shell / CI; highest priority).

So an `AIRLOCK_*` env var beats your `~/airlock/config.toml`, which beats the
project config (`--config` / `AIRLOCK_CONFIG` / a discovered `pyproject.toml`),
which beats the built-in default.

> The user config lives under the **store root**, which defaults to `~/airlock`.
> Because the store-root location is needed to *find* the user config, set
> `store_root` itself via `AIRLOCK_STORE_ROOT` or `pyproject.toml`, not inside
> `~/airlock/config.toml`.

> **Which `pyproject.toml` is discovered depends on the entry point.** `bin/airlock`
> and `scripts/vet.sh` `cd` into the airlock checkout before running the helper, so
> cwd discovery finds *airlock's own* `pyproject.toml` — not your project's. To load
> **your own** project defaults deliberately, pass `--config path/to/your.toml` (on
> `vet` / `quarantine`) or set `AIRLOCK_CONFIG` (works everywhere, ideal for CI);
> both take precedence over cwd discovery, and `--config` accepts either a bare
> airlock table or a `[tool.airlock]` pyproject. Under `bin/airlock` /
> `scripts/vet.sh`, give an **absolute** path — a relative one resolves against the
> airlock checkout, since the launcher changes directory first.
> Persistent machine-wide defaults still
> live in `~/airlock/config.toml`, which is always loaded regardless of cwd.
> Resolves [#45](https://github.com/flightpath-software/airlock-scan/issues/45).
>
> 🔒 The **scanned target's** config is never read: the project config is refused if
> it resolves inside the target tree — whether it was found by cwd discovery or
> pointed at explicitly with `--config` — so an untrusted repo can't reconfigure the
> scanner vetting it (a warning is printed when this happens).

## Your API key: the *name* vs the *value*

The Tier-2 (LLM) reviewer needs an API key. **The key itself never lives in
Airlock's config or the repo** — it lives in an environment variable on your
machine. The config only stores the **name** of that variable:

- `llm.api_key_env` = the *name*, e.g. `"OPENAI_API_KEY"` (safe to commit — it's
  just a label).
- The *secret* (e.g. `sk-…`) is what you `export` into that variable in your shell.

At runtime Airlock does `os.environ.get(<api_key_env>)` to read the key. Set it
in your shell profile:

```bash
# zsh (macOS default): ~/.zshrc     bash: ~/.bashrc (Linux) or ~/.bash_profile (macOS)
export OPENAI_API_KEY="sk-...your real key..."
```
Then `source ~/.zshrc` (or open a new terminal).

> **Don't paste the key into `api_key_env`.** That field is the variable's
> *name*, not the key. Airlock validates it at config load — the whole value must
> be an environment-variable identifier (letters, digits, underscores; no leading
> digit) — and rejects anything else with an error that doesn't print the value.
>
> That catches the common key formats, which contain characters a variable name
> can't hold (`sk-…`, `xoxb-…`, AWS secret keys). It does **not** catch tokens
> that happen to be identifier-shaped (`ghp_…`, `hf_…`, `AKIA…`): those pass
> validation and would still be echoed by the "no API key" message below. Treat
> the validation as a safety net, not a guarantee — the field is for the *name*.
> Tracked in [#41](https://github.com/flightpath-software/airlock-scan/issues/41).

No key at all? Use `--fake` (offline dummy backend) or `provider = "local"`
(a local OpenAI-compatible server such as Ollama) — neither needs a key.

## Creating your config file

Create `~/airlock/config.toml` and **add only the keys you want to override** —
do **not** copy every default in. Keeping the file to just your overrides means
you keep tracking Airlock's defaults as they improve; a file full of copied
defaults would silently pin you to old values. A user config uses bare tables
(no `[tool.airlock]` prefix):

```toml
# ~/airlock/config.toml — only what you override
[llm]
model = "gpt-4o"
```

A **project** config uses the `[tool.airlock]` prefix in `pyproject.toml`:

```toml
[tool.airlock.llm]
model = "gpt-4o"
```

### A commented reference template

Every *key* below is commented out — uncomment only the lines you actually want
to change (uncommenting a line that already matches the default just pins it, so
leave those alone).

**Leave the `[section]` headers uncommented.** A key without its header lands in
the top-level table, where it is silently ignored — no error, no effect:

```toml
# [llm]
model = "gpt-4o"    # ← ignored: the [llm] header is commented out
```

```toml
# ~/airlock/config.toml
# store_root = "~/airlock"                       # where runs and reports are written
# export_requires_optin = true

[llm]
# provider      = "openai"                      # label only; "local" switches to the local preset
# base_url      = "https://api.openai.com/v1"
# model         = "gpt-4o-mini"
# api_key_env   = "OPENAI_API_KEY"              # NAME of the env var holding the key
# local_base_url = "http://localhost:11434/v1"  # used when provider = "local"
# local_model    = "qwen2.5-coder"              # used when provider = "local"
# redact_tier1_secrets = true                   # NOT YET WIRED UP — see #42
# temperature    = 0.0
# request_timeout = 60
# max_file_bytes  = 200000                       # per-file review cap; larger files are truncated + flagged partially reviewed
# max_files       = 5                            # per-run cost/safety cap
# gate_only_on_suspicious = true

[persistence]
# files_are_source_of_truth = true               # SQLite is a derived index
# sqlite_index = true
# ingested_bytes_ttl_days = 30

[canary]
# harness_sets = ["claude_code", "codex_cli", "gemini_cli", "cursor", "opencode", "zed", "cline", "warp"]
# agnostic_set = true
# bisect_on_fire = true
```

One field above still doesn't do what its name suggests — tracked in
[#42](https://github.com/flightpath-software/airlock-scan/issues/42)
(`redact_tier1_secrets` has no consumer, so Tier-1 secrets are **not** masked
before a Tier-2 call). `max_file_bytes` does not chunk either: a file larger than
the cap is reviewed only up to it, but the run now flags any such file as **only
partially reviewed** in the report, so the coverage gap is visible rather than
silent (see [#44](https://github.com/flightpath-software/airlock-scan/issues/44)).

## Environment variables

A **curated subset** of settings can also be set via `AIRLOCK_*` (handy for CI
or one-off runs). The config file can set *any* field; these env vars cover the
common ones and take top priority:

| Env var | Overrides | Default |
|---|---|---|
| `AIRLOCK_STORE_ROOT` | `store_root` | `~/airlock` |
| `AIRLOCK_WRITE_INTO_TARGET` | `write_into_target` | `false` — parsed but **not yet read by any command** ([#43](https://github.com/flightpath-software/airlock-scan/issues/43)) |
| `AIRLOCK_LLM_PROVIDER` | `llm.provider` | `openai` |
| `AIRLOCK_LLM_BASE_URL` | `llm.base_url` | `https://api.openai.com/v1` |
| `AIRLOCK_LLM_MODEL` | `llm.model` | `gpt-4o-mini` |
| `AIRLOCK_LLM_API_KEY_ENV` | `llm.api_key_env` | `OPENAI_API_KEY` |
| `AIRLOCK_LLM_LOCAL_MODEL` | `llm.local_model` | `qwen2.5-coder` |
| `AIRLOCK_LLM_MAX_FILES` | `llm.max_files` | `5` |

(`AIRLOCK_LLM_API_KEY_ENV` sets the *name* of the key variable — not the key.)

## Recipes

### Switch the LLM provider (Groq, xAI, any OpenAI-compatible endpoint)

Airlock speaks the OpenAI-compatible Chat Completions API, so switching provider
is three settings + the key. **Leave `provider` at `openai`** — it's a label;
`base_url` does the routing (only the literal `"local"` is special-cased). Pick a
model with reliable **function/tool-calling**, since the canary tripwires depend
on it.

**Groq** — `~/airlock/config.toml`:
```toml
[llm]
base_url    = "https://api.groq.com/openai/v1"
model       = "llama-3.3-70b-versatile"   # pick a current Groq model
api_key_env = "GROQ_API_KEY"
```
…and in your shell profile: `export GROQ_API_KEY="gsk_..."`.

**xAI (Grok)** — same shape, different endpoint/key:
```toml
[llm]
base_url    = "https://api.x.ai/v1"
model       = "grok-2-latest"             # pick a current xAI model
api_key_env = "XAI_API_KEY"
```
…and `export XAI_API_KEY="xai-..."`.

Or do it entirely with env vars (nothing but the shell):
```bash
export AIRLOCK_LLM_BASE_URL="https://api.groq.com/openai/v1"
export AIRLOCK_LLM_MODEL="llama-3.3-70b-versatile"
export AIRLOCK_LLM_API_KEY_ENV="GROQ_API_KEY"
export GROQ_API_KEY="gsk_..."
```

> ⚠️ **Groq ≠ Grok.** Groq is the fast-inference provider (`GROQ_API_KEY`); Grok
> is xAI's model (`XAI_API_KEY`). Same setup shape, different endpoint and key.

### Run fully offline / local (no key, no network)

Point at a local OpenAI-compatible server (e.g. [Ollama](https://ollama.com)):
```toml
[llm]
provider   = "local"                      # switches to the local_* settings below
local_base_url = "http://localhost:11434/v1"
local_model    = "qwen2.5-coder"
```
Or, for a quick dry run with no model at all, pass `--fake` to the reviewer.

### Move the report store

```bash
export AIRLOCK_STORE_ROOT="/data/airlock-runs"
```

## Verify

```bash
[ -n "$GROQ_API_KEY" ] && echo "key is set"   # confirms without printing the secret
airlock-helper quarantine <some-dir>          # or: airlock  → runs a Tier-2 review
```
If the key isn't set you'll see an `error: no API key found ...` message. It does
**not** print your configured `api_key_env` value, so a mis-pasted secret can't
leak there ([#41](https://github.com/flightpath-software/airlock-scan/issues/41)).
The field must still hold the variable's *name* and never the key itself (see the
warning above).
