# CLAUDE.md

Guidance for AI agents working in this repo. Keep it short; deeper detail lives
in [`docs/`](docs/).

## What this is

`code-scanner` (`cscan`) is a **shell-first, `uv`-native** toolkit that vets an
untrusted repo/skill **before** you install it or point an LLM agent at it. It
orchestrates deterministic scanners (Tier 1) and is growing an injection-resistant
LLM review tier with canary tripwires (Tier 2). See
[`docs/project-plan.md`](docs/project-plan.md) for the architecture and status,
and [`docs/canary-tripwires.md`](docs/canary-tripwires.md) for the canary design.

## Layout

- `bin/cscan` — gum launcher (main entry point); `scripts/` — shell UX.
- `scanners/` — one adapter per external tool; `config/` — scanner registry + Semgrep rules.
- `src/code_scanner/` — Python helper: `config`, `store`, `database`, `canary`,
  `gate`, `llm_backend`, `quarantine`, `parsers`, `report`.
- `data/` — human source of the harness-signature dataset (packaged JSON lives in `src/`).
- `tests/` — pytest suite. `docs/` — all long-form docs.

## Dev commands

```bash
uv sync                       # resolve deps (under the 3-day supply-chain cooldown)
uv run pytest -q              # tests
uv run ruff check .           # lint (line-length 100, py312)
uv run cscan-helper --help    # the Python helper CLI
```

- **Always** add deps with `uv add` / `uv add --dev` (never hand-edit
  `pyproject.toml`/`uv.lock`); they must clear the 3-day cooldown + OSV check.
- Target Python 3.12; prefer stdlib over new runtime deps.
- Run the Tier-2 reviewer: `cscan-helper quarantine <dir>` (needs `OPENAI_API_KEY`,
  or `--fake` for offline). It reviews at most `CSCAN_LLM_MAX_FILES` files (default 5).

## Commits

Use **Conventional Commits** (enforced in CI by `cz check`). The commit template
is `.gitmessage.txt`:

```bash
git config commit.template .gitmessage.txt   # one-time
uv run cz commit                             # guided commit (recommended)
```

Types: `feat` (MINOR), `fix`/`perf`/`refactor` (PATCH), `docs`, `test`, `build`,
`ci`, `chore`. Pre-1.0, breaking changes bump MINOR (`major_version_zero = true`).
More: [`docs/commits.md`](docs/commits.md).

## Changelog — a fragment for EVERY change

`CHANGELOG.md` is compiled by **towncrier** from small news fragments in
[`changelog.d/`](changelog.d/) (never edit `CHANGELOG.md` by hand). CI
(`towncrier check`) fails a PR that adds no fragment.

```bash
cscan changelog            # guided: pick a type, write a one-line summary
cscan changelog preview    # preview the unreleased section
# or directly:
uv run towncrier create -c "Add osv-scanner adapter" 123.scanner.md   # tied to #123
uv run towncrier create -c "Handle empty SARIF" +empty-sarif.fixed.md # orphan
```

Fragment name: `<issue-or-+slug>.<type>.md`. Types (= changelog sections):
`security`, `added`, `changed`, `fixed`, `scanner`, `deprecated`, `removed`,
`docs`, `misc`. Write entries **for readers**, not as commit subjects. More:
[`docs/changelog.md`](docs/changelog.md).

## Releasing (the automated workflow)

A release: (1) computes the next version from Conventional Commits, (2) compiles
the fragments into `CHANGELOG.md` and deletes them, (3) bumps the version in
`pyproject.toml` + `src/code_scanner/__init__.py` + `uv.lock`, commits, and tags
`vX.Y.Z`. towncrier owns the changelog; commitizen owns versioning/tagging
(`update_changelog_on_bump = false`, `version_provider = "uv"`).

```bash
cscan release            # interactive (confirms each step)
cscan release --yes      # non-interactive (CI)
git push --follow-tags   # publish the bump commit + tag
```

Equivalent manual steps:

```bash
next="$(uv run cz bump --get-next)"          # fails if no feat/fix since last tag
uv run towncrier build --yes --version "$next"
uv run cz bump --yes
git push --follow-tags
```

Preview without changing anything: `cscan changelog preview` or
`uv run cz bump --dry-run`.

Notes:
- Releasing requires at least one version-bumping commit (`feat`/`fix`/…) since
  the last tag, and a clean working tree (uncommitted changes get swept into the
  bump commit).
- The first stable cut is planned as `1.0.0` (drop `major_version_zero`) — see
  [`docs/project-plan.md`](docs/project-plan.md) §8.1.

## House rules

- Develop on a feature branch; never force a push to `main`.
- Keep the deterministic tier **authoritative**; the LLM tier is advisory and
  must never clear a Tier-1 finding (see project plan §3, `gate.py`).
- Reports stay **local to the user** (`~/cscan/`), never written into the scanned
  repo and never sent off-machine except a configured Tier-2 LLM call.
