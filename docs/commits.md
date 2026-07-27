# Making commits

This project uses [**Conventional Commits**](https://www.conventionalcommits.org).
Commit messages drive automated version bumps (via `commitizen`) and are validated
in CI, so the format matters.

## Format

```
<type>(<optional scope>): <short summary>

<optional body — what & why, wrapped ~72 cols>

<optional footer — BREAKING CHANGE: …, Refs: #123>
```

- **summary**: imperative mood, ~50 chars, no trailing period.
- **scope** (optional): the area touched, e.g. `scanners`, `report`, `cli`, `ci`.

### Types

| Type | Use for | Version effect |
| --- | --- | --- |
| `feat` | a new capability | MINOR |
| `fix` | a bug fix | PATCH |
| `perf` | performance improvement | PATCH |
| `refactor` | internal change, no behavior change | PATCH |
| `docs` | documentation only | none |
| `test` | tests only | none |
| `build` | build system / dependencies | none |
| `ci` | CI configuration | none |
| `chore` | maintenance | none |
| `revert` | revert a previous commit | none |

> `security` and `scanner` are **not** commit types (the validator rejects them).
> Use a standard type with a scope instead — `fix(security): …`, `feat(scanners): …`.
> The *changelog* still gets dedicated **Security** and **Scanners** sections,
> chosen by the fragment type when you run `airlock changelog` (see [changelog.md](changelog.md)).

### Breaking changes

Add `!` after the type/scope **or** a `BREAKING CHANGE:` footer:

```
feat(cli)!: rename `airlock scan` flags

BREAKING CHANGE: `--only` replaced by positional scanner ids.
```

> Pre-1.0 (we're at 0.x): breaking changes bump the **minor** version, not major
> (`major_version_zero = true`).

### Examples

```
feat(scanners): add osv-scanner adapter
fix(report): treat unknown SARIF level as medium
fix(security): refuse install of OSV-flagged versions
docs(commits): document the Tower workflow
build(deps): add towncrier and commitizen (dev)
```

## Three ways to write a compliant commit

### 1. Commit template (works everywhere, including Tower)

Enable the repo's template once; your editor/GUI will pre-fill the guidance:

```bash
git config commit.template .gitmessage.txt
```

The template lives at [`.gitmessage.txt`](../.gitmessage.txt) and lists the types
and rules as comments (comment lines are stripped from the final message).

### 2. Interactive composer (`commitizen`)

```bash
uv run cz commit      # prompts for type, scope, summary, body, breaking change
# shortcut: uv run cz c
```

This guarantees a valid message and is the easiest path on the command line.

### 3. Using the Tower Git client

If you commit with [Tower](https://www.git-tower.com/):

1. **Use the shared template.** After running
   `git config commit.template .gitmessage.txt` in the repo, Tower honors Git's
   `commit.template` and shows it in the commit-message box. You can also store a
   reusable snippet via Tower's **Commit Message Templates** (Tower ▸ Settings ▸
   *Git Config* / *Templates*).
2. **Type the header yourself** in Conventional Commits form, e.g.
   `fix(report): handle empty SARIF runs`. Tower won't enforce the format — CI
   (`cz check`) will, so follow the template.
3. **Add a changelog fragment** before (or with) the commit — Tower won't do this
   for you. Two options:
   - **CLI:** run `airlock changelog` in a terminal; it prompts for the type,
     summary, and an optional Linear ticket ID + title, then writes the fragment.
     Stage the resulting `changelog.d/+<slug>.<type>.md` in Tower alongside your
     changes.
   - **Manual:** create `changelog.d/+<slug>.<type>.md` directly in your editor.
     If the change is tracked in Linear, start the content with the link:
     `[FP-123: Ticket title](https://linear.app/flightpath/issue/FP-123) — summary.`

   See [changelog.md](changelog.md).

> Tip: keep a terminal open for `airlock changelog`; do staging/committing in Tower
> if you prefer the GUI. Both paths produce the same result.

## Validation

- **Locally (optional pre-commit hook):**

  ```bash
  uvx pre-commit install --hook-type commit-msg
  ```

  with a `.pre-commit-config.yaml` using the `commitizen` `commit-msg` hook.
- **In CI:** the `guards` job runs
  `cz check --rev-range origin/<base>..HEAD`, failing the PR on any
  non-conforming commit message.

## Don't forget the changelog

Every user-facing change needs a news fragment. The CI `guards` job also runs
`towncrier check` and will fail a PR that doesn't add one. The fastest way:

```bash
airlock changelog
```
