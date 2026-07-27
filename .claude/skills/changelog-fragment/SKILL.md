---
name: changelog-fragment
description: Add a Towncrier changelog fragment when preparing a pull request in airlock-scan. Use whenever a PR changes user-facing behavior (a new scanner, a feature, a fix, a CLI/config change, deprecation, removal, or security fix), or when deciding whether a PR needs one.
---

# Add a changelog fragment (airlock-scan)

`CHANGELOG.md` is compiled by [Towncrier](https://towncrier.readthedocs.io) from
small per-change news fragments in [`changelog.d/`](../../../changelog.d/) —
**never edit `CHANGELOG.md` by hand.** CI (`towncrier check` in `.github/workflows/ci.yml`)
fails a PR that changes user-facing behavior but adds no fragment, unless the PR
carries the `skip-changelog` label.

## Does this PR need a fragment?

**Yes** if it changes anything a user or operator can observe: a new/changed
scanner adapter, a CLI or config change, a new feature, a bug fix, a deprecation
or removal, or a security fix.

**No** (apply the `skip-changelog` label instead) if it is docs-only, CI/tooling
only, an internal refactor with no behavior change, or test-only.

## Create the fragment

Guided (recommended):

```bash
airlock changelog            # pick a type, write a one-line summary
airlock changelog preview    # preview the assembled unreleased section
```

Or directly with Towncrier:

```bash
uv run towncrier create -c "Add the yara scanner adapter" +yara-adapter.scanner.md
```

## Naming & types

Fragment file name: `+<slug>.<type>.md` — always an **orphan** slug (put any
Linear/issue link in the *content*, not the filename).

Types map to `CHANGELOG.md` sections (defined in `pyproject.toml` `[tool.towncrier]`):

| Type | Use for |
|---|---|
| `security` | A security-relevant fix or hardening. |
| `added` | A new capability. |
| `changed` | A change to existing behavior. |
| `fixed` | A bug fix. |
| `scanner` | Adding or materially changing a scanner adapter. |
| `deprecated` | Something now discouraged and slated for removal. |
| `removed` | Something taken out. |
| `docs` | Notable documentation changes worth surfacing to readers. |
| `misc` | Trivial/no-content entries (not shown with content). |

## Write it for readers

One line, present tense, describing the effect on the user — not the commit
subject. Good: *"Redact Tier-1-detected secrets before any Tier-2 LLM call."*
Avoid internal IDs and roadmap talk in the text.

## Verify

```bash
uv run towncrier check --compare-with origin/develop   # what CI runs on a PR
airlock changelog preview
```
