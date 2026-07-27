# Changelog & releases

The changelog is **human-written** and assembled from small news fragments by
[*towncrier*](https://towncrier.readthedocs.io/); versioning and tagging are
handled by [*commitizen*](https://commitizen-tools.github.io/commitizen/). Both
are uv-managed dev tools.

Why fragments instead of generating from commit messages:

- Entries are written *for readers*, not parsed from terse commit subjects.
- Each change is its own file, so parallel branches **never conflict** on
  `CHANGELOG.md`.

## Add a fragment for every change

The guided way (recommended):

```bash
airlock changelog          # pick a type, enter a summary, optional Linear ticket
airlock changelog preview  # see how the unreleased section will render
```

The helper prompts for an optional Linear ticket ID (e.g. `FP-123`) and title,
then writes the link into the fragment content automatically:

```
[FP-123: Ticket title](https://linear.app/flightpath/issue/FP-123) — summary text.
```

**PyCharm / Tower users:** create the `.md` file directly in `changelog.d/` and
write the link by hand using the same format. The filename must match
`+<slug>.<type>.md` (e.g. `+osv-adapter.scanner.md`).

Or create one directly with towncrier (no Linear link):

```bash
uv run towncrier create -c "Handle empty SARIF runs" +empty-sarif.fixed.md
```

Fragments live in [`changelog.d/`](../changelog.d/) and are named
`+<slug>.<type>.md` (always orphan — the Linear link lives in the content, not
the filename).

### Fragment types

Defined in `[tool.towncrier]` (rendered top-to-bottom in this order):

| Type (file suffix) | Section heading |
| --- | --- |
| `security` | Security |
| `added` | Added |
| `changed` | Changed |
| `fixed` | Fixed |
| `scanner` | Scanners |
| `deprecated` | Deprecated |
| `removed` | Removed |
| `docs` | Documentation |
| `misc` | Misc (no body shown) |

> **Security & supply-chain entries.** Use `security` for hardening/fixes. When a
> dependency bump matters, note that it cleared the policy, e.g.
> `Bump rich 14 → 15 (OSV-clean, >3 days old).`

## Releasing

`airlock release` runs the whole flow with confirmations:

1. compute the next version from Conventional Commits — `cz bump --get-next`
2. compile fragments into `CHANGELOG.md` and remove them — `towncrier build`
3. bump `pyproject.toml` + `src/airlock_scan/__init__.py` + `uv.lock`, commit, and
   create a `vX.Y.Z` tag — `cz bump`

```bash
airlock release            # interactive
airlock release --yes      # non-interactive (CI / scripted)
git push --follow-tags   # publish the commit + tag
```

Equivalent manual steps:

```bash
next="$(uv run cz bump --get-next)"
uv run towncrier build --yes --version "$next"
uv run cz bump --yes
```

Notes:

- `commitizen` is configured with `update_changelog_on_bump = false` so it never
  fights towncrier over `CHANGELOG.md`.
- `version_provider = "uv"` keeps `pyproject.toml` and `uv.lock` versions in sync.
- Preview a release without changing anything: `airlock changelog preview` or
  `uv run cz bump --dry-run`.

## CI guard

The `guards` job (pull requests only) enforces this workflow:

- `towncrier check` — the PR must add a news fragment (auto-skipped on release
  branches that edit `CHANGELOG.md`).
- `cz check` — every commit message must be a valid Conventional Commit.
