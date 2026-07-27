---
name: release
description: Cut a release of airlock-scan — compile the Towncrier changelog, bump the version per Conventional Commits, and tag. Use when asked to cut, tag, or ship a release, bump the version, or prepare release notes for this repo.
---

# Cut a release (airlock-scan)

The maintainer runbook for turning merged work into a tagged release. Fragments
accumulate in [`changelog.d/`](../../../changelog.d/) as PRs merge (see the
`changelog-fragment` skill); this skill turns them into a version.

**Division of labor:** Towncrier owns `CHANGELOG.md`; commitizen owns
versioning/tagging. `pyproject.toml` sets `update_changelog_on_bump = false` and
`version_provider = "uv"`, so the version stays in sync across
`pyproject.toml`, `src/airlock_scan/__init__.py`, and `uv.lock`.

## The mental model — "release" ≠ "promotion"

Two distinct things get called "release"; keep them apart:

- **Promotion** moves code between branches (`feature → develop → staging → main`) via PRs.
- **Cutting a release** is the *version ceremony*: compile the `changelog.d/` fragments into
  `CHANGELOG.md`, bump the version in `pyproject.toml` / `__init__.py` / `uv.lock`, commit that
  bump, and tag `vX.Y.Z`. It stamps a version — it does not, by itself, move code onto `main`.

Because `main` is protected (no direct pushes, no bypass), **the release reaches `main` through a
PR, and that PR is how it lands there.** You do the ceremony on a short-lived `release/X.Y.Z`
branch, then merge it into `main`.

## 0 · Preconditions

- The work is QA'd on `staging`. Cut `release/X.Y.Z` **from `staging`** — don't run the ceremony
  on `main` (you can't push to it) or on `staging` directly (keep it a rolling QA branch).
- Clean working tree on the release branch (uncommitted changes get swept into the bump commit —
  `release.sh` warns but will proceed).
- At least one version-bumping commit (`feat` / `fix` / …) since the last tag — otherwise
  `cz bump` has nothing to do (`release.sh` aborts with that message).
- Pre-1.0, `major_version_zero = true`, so the largest automatic bump is a **minor**
  (e.g. `0.4.0 → 0.5.0`) even for breaking changes. The first stable `1.0.0` is a deliberate,
  separate step (drop `major_version_zero`) — see
  [`docs/project-plan.md`](../../../docs/project-plan.md) §8.1.

## 1 · Do the ceremony on a release branch

`airlock release` (i.e. `scripts/release.sh`) computes the next version, compiles the changelog, and
bumps + commits + tags **locally — it does not push.**

```bash
git switch -c release/X.Y.Z origin/staging   # freeze the QA'd candidate
airlock release                                # interactive: changelog → bump → commit → tag vX.Y.Z
airlock release --yes                          # non-interactive equivalent
git push -u origin release/X.Y.Z             # push the branch (tag waits until step 2)
```

Manual equivalent of `airlock release`:

```bash
next="$(uv run cz bump --get-next)"              # next version from Conventional Commits
uv run towncrier build --yes --version "$next"   # compile fragments into CHANGELOG.md, delete them
uv run cz bump --yes                             # bump version + uv.lock, commit, tag vX.Y.Z
```

## 2 · Land it on `main` via the release PR

1. Open a PR **`release/X.Y.Z → main`**. Merging it is the release arriving on `main`.
2. Merge with a **merge commit** (or fast-forward) — **not a squash.** Squash rewrites the bump
   commit's SHA, which would strand the `vX.Y.Z` tag on a commit that isn't on `main`. (Feature
   PRs into `develop` stay squash-only; this no-squash rule is specific to the release PR.)
3. Publish the tag now that its commit is on `main`:
   ```bash
   git fetch origin main
   git push origin vX.Y.Z          # or: git push --follow-tags from an up-to-date main
   ```

`main` now contains exactly the tagged release commit — nothing lands on `main` except through
this release PR.

## 3 · Preview without changing anything

```bash
airlock changelog preview      # the unreleased CHANGELOG section
uv run cz bump --dry-run     # the version that would be chosen
```

## Notes

- Never hand-edit `CHANGELOG.md` or hand-write a version into `pyproject.toml` —
  both are generated.
- The tag format is `vX.Y.Z` (`tag_format = "v$version"`).
- Publishing signed/provenance-backed artifacts to PyPI is future work (see
  `SECURITY.md`); today a release is the changelog + version bump + git tag.
