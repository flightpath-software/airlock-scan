---
name: release
description: Cut a release of code-scanner — compile the Towncrier changelog, bump the version per Conventional Commits, and tag. Use when asked to cut, tag, or ship a release, bump the version, or prepare release notes for this repo.
---

# Cut a release (code-scanner)

The maintainer runbook for turning merged work into a tagged release. Fragments
accumulate in [`changelog.d/`](../../../changelog.d/) as PRs merge (see the
`changelog-fragment` skill); this skill turns them into a version.

**Division of labor:** Towncrier owns `CHANGELOG.md`; commitizen owns
versioning/tagging. `pyproject.toml` sets `update_changelog_on_bump = false` and
`version_provider = "uv"`, so the version stays in sync across
`pyproject.toml`, `src/code_scanner/__init__.py`, and `uv.lock`.

## 0 · Preconditions

- Releases are cut from **`main`** (the production branch). Make sure the work you
  intend to ship has been promoted `develop → staging → main` and the tree is clean
  (uncommitted changes get swept into the bump commit).
- There is at least one version-bumping commit (`feat` / `fix` / …) since the last
  tag — otherwise `cz bump` has nothing to do.
- Pre-1.0, `major_version_zero = true`, so the largest automatic bump is a **minor**
  (e.g. `0.4.0 → 0.5.0`) even for breaking changes. The first stable `1.0.0` is a
  deliberate, separate step (drop `major_version_zero`) — see
  [`docs/project-plan.md`](../../../docs/project-plan.md) §8.1.

## 1 · Guided release (recommended)

```bash
cscan release            # interactive — confirms each step
cscan release --yes      # non-interactive (CI)
git push --follow-tags   # publish the bump commit + tag
```

## 2 · Equivalent manual steps

```bash
next="$(uv run cz bump --get-next)"              # next version from Conventional Commits
uv run towncrier build --yes --version "$next"   # compile fragments into CHANGELOG.md, delete them
uv run cz bump --yes                             # bump version + uv.lock, commit, tag vX.Y.Z
git push --follow-tags
```

## 3 · Preview without changing anything

```bash
cscan changelog preview      # the unreleased CHANGELOG section
uv run cz bump --dry-run     # the version that would be chosen
```

## Notes

- Never hand-edit `CHANGELOG.md` or hand-write a version into `pyproject.toml` —
  both are generated.
- The tag format is `vX.Y.Z` (`tag_format = "v$version"`).
- Publishing signed/provenance-backed artifacts to PyPI is future work (see
  `SECURITY.md`); today a release is the changelog + version bump + git tag.
