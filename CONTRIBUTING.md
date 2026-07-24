# Contributing to code-scanner

Thanks for your interest! `code-scanner` (`cscan`) is in early development, so the
process below will firm up as the project stabilizes. If you're planning a
non-trivial change, please open an issue first so we can coordinate.

## Code of Conduct

This project follows the [Contributor Covenant](./CODE_OF_CONDUCT.md). By
participating, you're expected to uphold it.

## Reporting security issues

**Do not** open a public issue for a security vulnerability. Report it privately —
see [`SECURITY.md`](./SECURITY.md) for the process.

## AI-assisted contributions

AI assistants are part of how this project is built, and AI-assisted contributions are welcome —
but the bar is the same as for any change: **a human is accountable for it.** Any PR (AI-assisted
or not) must:

- be **reviewed and understood by its author** — you can explain why each line is correct;
- **include tests** for new or changed behavior (see the testing policy below);
- **add a changelog fragment** (or carry the `skip-changelog` label) — see below; and
- pass CI (lint, tests, shell-syntax, changelog + commit guards, and the security workflows)
  before it can merge.

The PR template asks you to attest to that verification. Mechanical or low-effort PRs that ignore
scope, skip tests, or can't be explained by their author will be closed without merge.

## License

`code-scanner` is licensed under **Apache-2.0** (see [`LICENSE`](./LICENSE)).
By contributing, you agree that your contributions are provided under that license.

## Branching model

`cscan` uses a three-branch promotion flow. Changes move **up** the chain via
reviewed pull requests; nothing is pushed directly to a protected branch.

```
feature/*  ──PR──▶  develop  ──PR──▶  staging  ──PR──▶  main
 (topic)          (integration,      (QA / release       (production /
                   default branch)    candidate)          tagged releases)
```

- **`develop` is the integration branch and the repository's default branch — base every
  feature branch and pull request off `develop`.** Day-to-day work lands here first. When GitHub
  offers a base branch for your PR it will already be `develop`.
- **`staging` is the QA / release-candidate branch.** A maintainer promotes a vetted set of
  changes from `develop` to `staging` for testing before release (and, in future, for the
  network-isolated dynamic-analysis suite — see `docs/project-plan-public.md` §4.3).
- **`main` is the protected production branch.** Nothing lands on `main` except a **release PR**
  (`release/X.Y.Z`, cut from `staging`) that carries the changelog-compile + version-bump commit;
  merging that PR *is* the release, and `vX.Y.Z` is tagged on the resulting `main` commit. Never
  target a feature or bug-fix PR at `main`. (The release PR is merged with a **merge commit, not a
  squash**, so the tag stays on `main` — see the Releasing section.)
- Cut branches from the current `develop`, named to match the commit convention below:
  `type/short-description` (e.g. `feat/yara-adapter`, `fix/canary-localize`, `docs/branching-model`).

All three branches are protected by rulesets (no direct push, no force-push, required CODEOWNERS
review, required status checks, no bypass).

## Working on the code

Use [`uv`](https://docs.astral.sh/uv/) — it manages Python and the project's dependencies.

```bash
uv sync                       # resolve deps under the 3-day supply-chain cooldown
uv run cscan-helper --help    # the Python helper CLI
uv run pytest -q              # tests
uv run ruff check .           # lint (line-length 100, py312)
```

- The primary UX is the shell launcher `bin/cscan` (needs [`gum`](https://github.com/charmbracelet/gum));
  the Python package `code_scanner` is a thin helper (parse/merge/gate). See the
  [README](./README.md) for the external scanners `cscan` orchestrates and how to install them.
- **Always** add dependencies with `uv add` / `uv add --dev` (never hand-edit `pyproject.toml` /
  `uv.lock`); they must clear the 3-day cooldown + OSV check. Target Python 3.12; prefer stdlib
  over new runtime deps.
- Keep PRs focused.

### Commits — Conventional Commits (enforced)

Write commit messages as [Conventional Commits](https://www.conventionalcommits.org/):
`type(scope): summary` — e.g. `feat(scanner): add yara adapter`, `fix(canary): …`,
`docs(adr): …`. CI runs `cz check` over the PR's commits and **fails the PR** on a
non-conforming message. The commit template pre-fills the guidance:

```bash
git config commit.template .gitmessage.txt   # one-time
uv run cz commit                             # guided commit (recommended)
```

Types: `feat` (MINOR), `fix`/`perf`/`refactor` (PATCH), `docs`, `test`, `build`, `ci`, `chore`.
Pre-1.0, breaking changes bump MINOR (`major_version_zero = true`). More in
[`docs/commits.md`](docs/commits.md).

### Testing policy

**New or changed functionality ships with automated tests.** A PR that adds a feature or fixes a
bug is expected to add or update tests that cover it, and the full suite must pass in CI. Bug fixes
should include a regression test that fails without the fix. Docs / CI / refactor-only changes are
exempt (use the `skip-changelog` label). Shell entry points must still parse — CI runs
`bash -n` over `bin/cscan`, `scripts/*.sh`, `scripts/lib/*.sh`, and `scanners/*.sh`.

## Changelog — a fragment for (almost) every change

`CHANGELOG.md` is compiled by [Towncrier](https://towncrier.readthedocs.io) from small news
fragments in [`changelog.d/`](changelog.d/) — never edit `CHANGELOG.md` by hand. If your PR changes
**user-facing behavior**, add one fragment:

```bash
cscan changelog                     # guided: pick a type, write a one-line summary
# or directly:
uv run towncrier create -c "Add osv-scanner adapter" +osv-adapter.scanner.md
```

Fragment name: `+<slug>.<type>.md`. Types (= changelog sections): `security`, `added`, `changed`,
`fixed`, `scanner`, `deprecated`, `removed`, `docs`, `misc`. Write entries **for readers**. CI
requires *either* a fragment *or* the `skip-changelog` label (for docs / CI / refactor-only PRs).
Preview the assembled notes with `cscan changelog preview`. More in
[`docs/changelog.md`](docs/changelog.md).

## Supply-chain: the `exclude-newer` delay

`pyproject.toml` sets `[tool.uv] exclude-newer = "3 days"`: dependency resolution ignores any
release published in the **last 3 days**, so a freshly-compromised package version can't be pulled
in before it's had time to be caught. Keep `uv.lock` in sync — CI runs `uv lock --locked`, which
**fails if the lockfile is out of sync** with `pyproject.toml`, so any dependency change lands as a
committed, reviewed lock update rather than a silent local resolve.

**Break-glass override** — when you must take a release younger than 3 days (e.g. a patch for an
actively-exploited CVE), grant a scoped exception for that one package and commit both files:

```toml
[tool.uv]
exclude-newer = "3 days"
exclude-newer-package = { somepkg = false }   # or a specific RFC 3339 timestamp
```

Because CI is `--locked`, the override lands as a reviewable diff — a deliberate, audited exception,
not a hidden flag. Drop it once the 3-day window covers the version anyway.

## Releasing

"Cutting a release" is a **version ceremony**, not a branch promotion: towncrier compiles the
`changelog.d/` fragments into `CHANGELOG.md`, and commitizen bumps + tags the version (keeping
`pyproject.toml`, `src/code_scanner/__init__.py`, and `uv.lock` in sync). A maintainer does it on a
`release/X.Y.Z` branch cut from `staging`, then merges that branch into `main` via a **merge-commit
PR** — the merge is how the release reaches the protected `main`:

```bash
git switch -c release/X.Y.Z origin/staging   # freeze the QA'd candidate
cscan release                                # changelog → bump → commit → tag vX.Y.Z (does NOT push)
git push -u origin release/X.Y.Z             # open a PR release/X.Y.Z -> main, merge (no squash)
git fetch origin main && git push origin vX.Y.Z   # publish the tag once its commit is on main
```

See the [`release` skill](.claude/skills/release/SKILL.md) and the "Releasing" section of
[`CLAUDE.md`](CLAUDE.md) for the full runbook.
