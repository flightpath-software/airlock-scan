# code-scanner docs

Project documentation. Start with the [README](../README.md) for what `cscan` is
and how to run it; this folder covers contributor workflows.

## Guides

- [Making commits](commits.md) — Conventional Commits, the commit-message
  template, `cz commit`, and how to do it from the **Tower** Git client.
- [Changelog & releases](changelog.md) — how to add a human-readable news
  fragment for every change, preview the draft, and cut a release.
- [Project plan](project-plan.md) — roadmap for the two-tier, injection-
  resistant repo/skill vetting pipeline (deterministic gate + Dual-LLM
  quarantine + canary tripwires).
- [Future work](future-work.md) — deferred backlog (YARA, dynamic-sandbox
  escalation, capability tracking, …) intentionally outside the committed
  milestones.

## Quick reference

```bash
cscan changelog          # add a news fragment (gum-guided)
cscan changelog preview  # preview the unreleased changelog
uv run cz commit         # compose a Conventional Commit interactively
cscan release            # build changelog + bump version + tag
```

## Conventions at a glance

- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org)
  (`feat:`, `fix:`, `refactor:`, …). Enforced in CI by `cz check`.
- **Every change ships a news fragment** in [`changelog.d/`](../changelog.d/).
  Enforced in CI by `towncrier check`.
- **Versioning** is SemVer; pre-1.0, breaking changes bump the *minor* version.
  `pyproject.toml` is the source of truth and is kept in sync with `uv.lock`.
- **Dependencies** are added with `uv add` and must clear the 3-day cooldown and
  the OSV check (see the README's supply-chain section).
