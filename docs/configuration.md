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
2. **Project config** — a `[tool.airlock]` table in the project's `pyproject.toml`
   (repo-level defaults, committed with the project).
3. **User config** — `~/airlock/config.toml` (your machine-wide preferences).
4. **Environment variables** — `AIRLOCK_*` (per-shell / CI; highest priority).

So an `AIRLOCK_*` env var beats your `~/airlock/config.toml`, which beats a
project's `pyproject.toml`, which beats the built-in default.

> The user config lives under the **store root**, which defaults to `~/airlock`.
> Because the store-root location is needed to *find* the user config, set
> `store_root` itself via `AIRLOCK_STORE_ROOT` or `pyproject.toml`, not inside
> `~/airlock/config.toml`.

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
> *name*, not the key. Airlock validates it and rejects a secret-shaped value at
> startup (it must match `^[A-Za-z_][A-Za-z0-9_]*$`), so a mistaken paste fails
> fast instead of leaking.

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

Everything below is **commented out** — copy the file and uncomment only the
lines you actually want to change (uncommenting a line that already matches the
default just pins it, so leave those alone):

```toml
# ~/airlock/config.toml
# [llm]
# provider      = "openai"                      # label only; "local" switches to the local preset
# base_url      = "https://api.openai.com/v1"
# model         = "gpt-4o-mini"
# api_key_env   = "OPENAI_API_KEY"              # NAME of the env var holding the key
# local_base_url = "http://localhost:11434/v1"  # used when provider = "local"
# local_model    = "qwen2.5-coder"              # used when provider = "local"
# redact_tier1_secrets = true                   # mask Tier-1 secrets before any Tier-2 call
# temperature    = 0.0
# request_timeout = 60
# max_file_bytes  = 200000                       # skip/chunk files larger than this
# max_files       = 5                            # per-run cost/safety cap
# gate_only_on_suspicious = true

# [persistence]
# ingested_bytes_ttl_days = 30

# [canary]
# harness_sets = ["claude_code", "codex_cli", "gemini_cli", "cursor", "opencode", "zed", "cline", "warp"]
# agnostic_set = true
# bisect_on_fire = true
```

## Environment variables

A **curated subset** of settings can also be set via `AIRLOCK_*` (handy for CI
or one-off runs). The config file can set *any* field; these env vars cover the
common ones and take top priority:

| Env var | Overrides | Default |
|---|---|---|
| `AIRLOCK_STORE_ROOT` | `store_root` | `~/airlock` |
| `AIRLOCK_WRITE_INTO_TARGET` | `write_into_target` | `false` |
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
echo $GROQ_API_KEY            # confirms the shell has the secret
airlock-helper quarantine <some-dir>   # or: airlock  → runs a Tier-2 review
```
If the key isn't set you'll see `error: no API key in $GROQ_API_KEY` — that
message prints the variable's *name*, never a value.
