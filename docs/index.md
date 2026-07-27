# airlock-scan docs

Project documentation. Start with the [README](../README.md) for what `airlock` is
and how to run it; this folder covers contributor workflows.

## Guides

- [Configuration](configuration.md) — the four config sources and their
  precedence, how the API key works (the config holds the env-var *name*, never
  the secret), the full field reference, and recipes for switching LLM provider
  or running fully offline.
- [Making commits](commits.md) — Conventional Commits, the commit-message
  template, `cz commit`, and how to do it from the **Tower** Git client.
- [Changelog & releases](changelog.md) — how to add a human-readable news
  fragment for every change, preview the draft, and cut a release.
- [Project plan](project-plan.md) — roadmap for the two-tier, injection-
  resistant repo/skill vetting pipeline (deterministic gate + Dual-LLM
  quarantine + canary tripwires).
- [Canary tripwires](canary-tripwires.md) — what the canary sensors are, why a
  fire is high-signal, harness fingerprinting, and how the LLM review is kept
  from doing any damage (capability removal, not a sandbox).
- [Future work](future-work.md) — deferred backlog (YARA, dynamic-sandbox
  escalation, capability tracking, …) intentionally outside the committed
  milestones.

## Quick reference

```bash
airlock changelog          # add a news fragment (gum-guided)
airlock changelog preview  # preview the unreleased changelog
uv run cz commit         # compose a Conventional Commit interactively
airlock release            # build changelog + bump version + tag
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
