# Project Plan — Taking `code-scanner` Public

> Status: **DRAFT for review** · Owner: Sean Howard · Created: 2026-07-21 ·
> Target repo: `flightpath-software/code-scanner`
>
> This plan describes how to turn `code-scanner` (`cscan`) into a well-governed
> **public** repository, matching the patterns already established in
> [`memex-trust-layer`](https://github.com/flightpath-software/memex-trust-layer)
> (our reference implementation for a public Flightpath repo). It covers the
> files to add, the branch model (`develop` → `staging` → `main`), the GitHub
> settings a human must apply, and the final step of flattening `main` into a
> single clean initial public commit.
>
> **Nothing here is destructive-by-accident.** The repo-restructuring and
> history-flattening steps are called out explicitly and are meant to be run
> deliberately by the owner, not silently by tooling.

---

## 0. TL;DR — what "public-ready" means here

`code-scanner` is currently a private repo with a single `main` branch, a
minimal CI workflow, no license, and no public-facing governance files. To match
`memex-trust-layer` it needs, in four buckets:

1. **Governance & legal** — `LICENSE` (Apache-2.0), `SECURITY.md`,
   `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and a real `license` field in
   `pyproject.toml` (today it is literally `"TODO"`).
2. **`.github/` scaffolding** — `CODEOWNERS`, `dependabot.yml`, issue templates,
   a PR template, and split security workflows (CodeQL, pip-audit/Bandit,
   gitleaks) alongside the existing lint+test CI.
3. **Claude skills** — a `.claude/skills/` tree (with a third-party attribution
   `NOTICE.md`) so agents working in the public repo get the same guided
   changelog/release/review workflows memex has.
4. **Branch model + GitHub settings** — three protected branches
   (`develop`, `staging`, `main`), branch rulesets, secret scanning, private
   vulnerability reporting, and required status checks — all configured in the
   GitHub UI by an admin.

Then, as the launch step: **flatten `main`** to one squashed "Initial public
release" commit so the internal iteration history (PR merges, WIP commits, mixed
author identities) is not part of the public record.

---

## 1. Pattern reference — what `memex-trust-layer` does

This is the checklist we are matching. Each item links to the file in memex that
establishes the pattern; §3 maps each to a concrete action for `code-scanner`.

### 1.1 Governance & legal files (repo root)

| File | What it does in memex |
|---|---|
| `LICENSE` | Apache-2.0, `Copyright 2026 Flightpath Software`. |
| `SECURITY.md` | Private vuln reporting via GitHub advisories, published SLAs (3-business-day ack), a **"security posture"** section that documents branch protection, CodeQL/Bandit, pip-audit, gitleaks, dependency cooldown, least-privilege CI. |
| `CONTRIBUTING.md` | Code of Conduct link, AI-assisted-contribution bar (a human is accountable), license/CLA-DCO note, **branching model**, testing policy, changelog policy, supply-chain `exclude-newer` explanation. |
| `CODE_OF_CONDUCT.md` | Contributor Covenant. |
| `README.md` | Status banner, quickstart, clear "what this is." (cscan already has a strong README — it just needs the license TODO resolved.) |

memex also ships `GLOSSARY.md`, `VALIDATION.md`, and a `docs/adr/` tree. Those
are **valuable but optional** for cscan's first public cut — see §3.5.

### 1.2 `.github/` scaffolding

| Path | Purpose |
|---|---|
| `.github/CODEOWNERS` | Global default owners (`* @passitalong @snorith`); enables "require review from Code Owners." |
| `.github/dependabot.yml` | Weekly updates for the `uv` lockfile **and** `github-actions`, auto-labeled `dependencies` + `skip-changelog`. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Summary / Closes / Changelog / Verification checklist. |
| `.github/ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml` | Structured issue forms; `config.yml` disables blank issues and links the security-advisory contact. |
| `.github/workflows/codeql.yml` | CodeQL SAST (Python), on push/PR to `main`/`develop` + weekly cron. |
| `.github/workflows/security.yml` | `pip-audit` (OSV SCA) + `bandit` (Python SAST), same triggers. |
| `.github/workflows/gitleaks.yml` | Secret scan, pinned-by-SHA + checksum-verified binary, SARIF upload to the Security tab (same-repo only). |
| `.github/workflows/changelog.yml` | Fragment gate with a `skip-changelog` label escape hatch. |

### 1.3 Supply-chain & CI hygiene

- **Dependency cooldown** via `[tool.uv] exclude-newer` — memex uses `"5 days"`;
  cscan already uses `"3 days"` (keep as-is, it is stricter and intentional).
- **`uv lock --locked` in CI** so the lockfile can't drift from the cooldown
  policy (memex enforces this in its `fitness` job; cscan's CI should gain it).
- **Least-privilege CI** — `permissions: contents: read` at the top of every
  workflow, elevating only the specific job that needs `security-events: write`.
- **Actions triggers** fire on the integration branches (`[main, develop]`), not
  just `main`.

### 1.4 Claude skills (`.claude/skills/`)

memex ships a `.claude/skills/` tree adapted from
[`mattpocock/skills`](https://github.com/mattpocock/skills) (MIT), with:

- `NOTICE.md` — third-party attribution reproducing the MIT license (required).
- `shared/` — `ADR-FORMAT.md`, `CONTEXT-FORMAT.md` referenced by multiple skills.
- One directory per skill (`changelog-fragment`, `release`, `code-review`,
  `pr-building`, `grilling`, …), each a `SKILL.md` with `name`/`description`
  frontmatter.

### 1.5 sdist hygiene (important for a distributed package)

memex excludes agent-instruction files from the built sdist so a downstream
project that installs the wheel/sdist does **not** inherit our coding-agent
instructions:

```toml
# pyproject.toml (memex, hatchling)
[tool.hatch.build.targets.sdist]
exclude = ["/web/build", "/web/node_modules", "/AGENTS.md", "/CLAUDE.md"]
```

cscan uses the `uv_build` backend, so the equivalent is a
`[tool.uv.build-backend]` module/exclude configuration (see §3.6).

---

## 2. Gap analysis — `code-scanner` today vs. the target

| Pattern | memex has | code-scanner today | Action |
|---|---|---|---|
| `LICENSE` | ✅ Apache-2.0 | ❌ none (`pyproject` `license = "TODO"`) | **Add Apache-2.0** (§3.1) |
| `SECURITY.md` | ✅ | ❌ | Add (§3.2) |
| `CONTRIBUTING.md` | ✅ | ❌ (guidance lives only in README) | Add (§3.2) |
| `CODE_OF_CONDUCT.md` | ✅ Contributor Covenant | ❌ | Add (§3.2) |
| `.github/CODEOWNERS` | ✅ | ❌ | Add (§3.3) |
| `.github/dependabot.yml` | ✅ uv + actions | ❌ | Add (§3.3) |
| `.github/PULL_REQUEST_TEMPLATE.md` | ✅ | ❌ | Add (§3.3) |
| `.github/ISSUE_TEMPLATE/` | ✅ bug/feature/config | ❌ | Add (§3.3) |
| CodeQL workflow | ✅ | ❌ | Add (§3.4) |
| pip-audit + Bandit workflow | ✅ | ❌ | Add (§3.4) |
| gitleaks workflow | ✅ pinned+checksum | ❌ | Add (§3.4) |
| Changelog fragment gate | ✅ standalone `changelog.yml` | 🟡 folded into `ci.yml` guards | Keep or split (§3.4) |
| `uv lock --locked` in CI | ✅ | ❌ | Add to CI (§3.4) |
| Towncrier + Commitizen | ✅ | ✅ already configured | Keep as-is |
| Dependency cooldown | ✅ `5 days` | ✅ `3 days` | Keep (stricter) |
| `.claude/skills/` | ✅ (+`NOTICE.md`) | ❌ | Add (§3.7) |
| `.gitattributes` (eol norm) | ✅ | ❌ | Add (§3.6) |
| sdist excludes agent files | ✅ | ❌ (`CLAUDE.md` would ship) | Add (§3.6) |
| Branches | `main` + `develop` | `main` only | **Create `develop`, `staging`** (§4) |
| Branch protection / rulesets | ✅ | ❌ | Configure in GitHub (§5) |
| Flattened public history | n/a (born public) | ❌ 30 commits, 6 merges, 3 identities | **Flatten `main`** (§6) |

---

## 3. Repository scaffolding to add

All of the following are ordinary file additions and can be done on a normal
feature branch (e.g. this branch) and merged **before** the flatten step. Draft
content is provided or referenced; copy memex's files and re-word for cscan.

### 3.1 License (do this first — it unblocks distribution)

1. Add an `Apache-2.0` `LICENSE` at the repo root (copy memex's verbatim; it
   already reads `Copyright 2026 Flightpath Software`).
2. Fix `pyproject.toml`:
   ```toml
   license = "Apache-2.0"          # SPDX expression; replaces license = { text = "TODO" }
   ```
   and remove the `# distribution deferred; choose a license before publishing`
   comment. Optionally add `license-files = ["LICENSE"]`.
3. Remove the "Choose and add a `LICENSE`" bullet from the README **TODO**
   section.

> **Why Apache-2.0:** it matches memex exactly (consistency across Flightpath
> public repos), grants an explicit patent license, and is the permissive
> default for a security tool meant to be adopted widely. If the owner wants a
> different license this is the one decision to make before launch — everything
> else in this plan is license-agnostic.

### 3.2 Root governance docs

- **`SECURITY.md`** — copy memex's structure and swap the repo name/URL. Keep the
  two-part shape: (a) private reporting via
  `https://github.com/flightpath-software/code-scanner/security/advisories/new`
  with the same SLAs, and (b) a **"Security posture"** section. cscan's posture
  section is a natural fit — it can point at the deterministic Tier-1 scanners,
  the 3-day cooldown, the OSV pre-install check, gitleaks/CodeQL/Bandit in CI,
  and least-privilege workflows. Adjust the "supported versions" table for
  cscan's pre-1.0 status.
- **`CONTRIBUTING.md`** — adapt memex's. Sections to keep: Code of Conduct link,
  AI-assisted-contribution bar, license note, **the branching model** (§4 below,
  updated for the three-branch flow), testing policy, the changelog-fragment
  policy (cscan already has `cscan changelog`), and the `exclude-newer`
  supply-chain explanation (change `5 days` → `3 days`). Much of cscan's existing
  README "Contributing" section can move here.
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant; copy memex's verbatim (update
  the contact email to the security/abuse address you want).

### 3.3 `.github/` metadata

- **`CODEOWNERS`** — `*   @passitalong @snorith` (same owners as memex), so
  "require review from Code Owners" has someone to route to.
- **`dependabot.yml`** — copy memex's two-ecosystem config verbatim
  (`uv` + `github-actions`, weekly Mondays, `dependencies`/`skip-changelog`
  labels). This is what keeps pinned actions and the lockfile current.
- **`PULL_REQUEST_TEMPLATE.md`** — copy memex's (Summary / Closes / Changelog /
  Verification). Change the test command to cscan's
  (`uv run pytest -q` and `bash -n` shell checks).
- **`ISSUE_TEMPLATE/`** — `bug_report.yml`, `feature_request.yml`, and
  `config.yml`. In `config.yml`, set `blank_issues_enabled: false` and add the
  security-advisory contact link (pointing at cscan's advisories/new URL).

### 3.4 CI / security workflows

cscan's current `ci.yml` (lint + test + shell-syntax + changelog/commit guards)
is good and should stay. Add the security workflows memex has, and align triggers
to the new branch set. Two decisions:

- **Branch triggers:** change `push: branches: [main]` to
  `[main, develop, staging]` across workflows so integration and QA branches are
  gated too. (PR triggers already cover everything targeting those branches.)
- **Split vs. keep the changelog guard:** memex has a dedicated `changelog.yml`
  with a `skip-changelog` **label** escape hatch; cscan folds `towncrier check`
  into `ci.yml` with no label escape. Recommend adopting the label escape hatch
  (docs/CI/refactor-only PRs shouldn't need a fragment) — either by adding the
  label check to `ci.yml` or by splitting out `changelog.yml`. This also means
  creating a `skip-changelog` label (§5.6).

Workflows to add (copy from memex, they are Python-generic):

1. **`codeql.yml`** — languages: `python`; triggers push/PR on the three branches
   + weekly cron; `security-events: write` only on the analyze job.
2. **`security.yml`** — `pip-audit` over `uv export`ed requirements + `bandit -r
   src`. (cscan's `src/` is small; Bandit will be fast.)
3. **`gitleaks.yml`** — copy memex's hardened version (SHA-pinned checkout,
   checksum-verified gitleaks binary, PR scans `base..head`, SARIF upload guarded
   to same-repo push/schedule). Add a `.gitleaksignore` at the root (can start
   empty). **Note:** cscan's `corpus/` contains deliberate adversarial fixtures
   with trigger words — confirm none are literal secret patterns that would trip
   gitleaks; add ignores if so.
4. **Add `uv lock --locked`** as the first step of the test job in `ci.yml`, so
   the 3-day cooldown policy can't silently drift from the lockfile (memex
   enforces this).

Also raise the pinned action versions to match memex where sensible
(`actions/checkout@v7`, `astral-sh/setup-uv@v7`) — but let Dependabot own
ongoing bumps once §3.3 lands.

### 3.5 Optional: ADRs, GLOSSARY, VALIDATION (recommended, not blocking)

memex's `docs/adr/`, `GLOSSARY.md`, and `VALIDATION.md` are high-value but not
required for a first public cut. cscan already has an excellent
`docs/project-plan.md` that plays a similar role to a design spec. Recommended
lightweight adoption:

- **`VALIDATION.md`** — cscan has a natural fitness story (deterministic tier is
  authoritative, canary FP rate target, offline mode, rebuildable index — see
  `project-plan.md` §8 success metrics S1–S7). A short VALIDATION.md that maps
  each promise to the test that proves it would be a strong public signal.
- **ADRs** — capture the two load-bearing decisions cscan already made in prose:
  (1) *the deterministic Tier-1 gate is authoritative; the LLM tier is advisory
  and can never clear a Tier-1 finding* (from `CLAUDE.md` house rules /
  `gate.py`), and (2) *reports stay local to the user, never written into the
  scanned repo or sent off-machine except the configured Tier-2 call*. These are
  exactly the "hard to reverse, surprising, real trade-off" decisions ADRs exist
  for.
- **GLOSSARY** — lower priority; cscan's vocabulary (Finding, gate verdict,
  canary/tripwire, harness signature, Tier-1/Tier-2) is already defined in the
  docs.

### 3.6 sdist hygiene & `.gitattributes`

- **`.gitattributes`** — copy memex's (normalizes line endings to `lf`). Cheap,
  avoids CRLF churn from contributors on Windows.
- **Exclude agent-instruction files from the sdist.** cscan's `CLAUDE.md` should
  not ship inside the distributed package (a consuming project must not inherit
  our agent instructions). With the `uv_build` backend, configure the build
  target to exclude it — e.g.:
  ```toml
  [tool.uv.build-backend]
  # Ship only the helper package; keep agent/instruction files out of the sdist.
  source-exclude = ["CLAUDE.md", "AGENTS.md"]
  ```
  Verify with `uv build && tar tzf dist/*.tar.gz | grep -i claude` (should be
  empty). Adjust the key names to the `uv_build` schema in the uv version you
  pin; the goal is: **`CLAUDE.md` absent from `dist/*.tar.gz` and the wheel.**

### 3.7 Claude skills

Bring over a `.claude/skills/` tree so agents in the public repo get the same
guided workflows. Minimum useful set for cscan:

- `changelog-fragment/` — wraps `cscan changelog` / `towncrier create`.
- `release/` — wraps `cscan release` (towncrier build → `cz bump` → tag).
- `code-review/` and/or `pr-building/` — adapt memex's, minus the memex-specific
  ADR/Postgres axes.

Requirements when copying:

- Include **`.claude/skills/NOTICE.md`** reproducing the MIT license and the
  `source:`/`forked:` frontmatter, exactly as memex does, since these are adapted
  from `mattpocock/skills`.
- Add any `shared/` reference docs the copied skills cite.
- **Do not** let `.claude/` leak into the sdist (it won't by default with
  `uv_build`'s src-layout, but confirm in the §3.6 verification).

---

## 4. Branch & environment model

Target: three long-lived, protected branches with a linear promotion flow, plus a
**future** protected space to actually execute untrusted tests in isolation
(Docker/VMs). This extends memex's two-branch model (`develop` = integration,
`main` = production) with an explicit `staging` QA gate in between, as requested.

### 4.1 The three branches

```
feature/*  ──PR──▶  develop  ──PR──▶  staging  ──PR──▶  main
 (topic)          (integration)      (QA / release       (production /
                                      candidate)          tagged releases)
```

| Branch | Role | What merges in | Who/what gates it |
|---|---|---|---|
| **`develop`** | Integration. **Default branch** for day-to-day PRs; the base every `feature/*` branch is cut from and targets. | Squash-merged feature PRs. | Full CI (lint, test, shell, changelog/commit guards) + CodeQL/security/gitleaks; 1 CODEOWNERS review. |
| **`staging`** | QA / release-candidate. Where we test a promoted set of changes before production — and, in future, run the isolated/sandboxed test suites (§4.3). | `develop → staging` promotion PRs (release candidates). | Same required checks as `develop`, **plus** (future) the sandboxed-execution checks. |
| **`main`** | Production. Only tagged releases live here. | `staging → main` release PRs only (`release/X.Y.Z`). Never a feature PR. | Strictest ruleset; required review; linear history; the release tag is cut here. |

Notes:
- Set **`develop` as the repository default branch** (like memex), so new PRs and
  clones start there and `main` stays quiet between releases.
- Keep merges **squash-only** into `develop`/`staging` (one commit per PR) and use
  a release commit into `main`. This keeps history readable and makes the eventual
  state of `main` a clean sequence of release commits on top of the flattened base
  (§6).
- The changelog/release tooling already assumes `main` is the release/default
  branch in a couple of places (e.g. the `release` skill and the PR template's
  auto-close note). When adopting `develop` as default, update those references so
  "the default branch" consistently means `develop` and releases promote to
  `main`. Reconcile this in `CONTRIBUTING.md` and the release runbook.

### 4.2 Creating the branches (mechanics)

Once the scaffolding PR(s) are merged and `main` is flattened (§6), create the
integration/QA branches from the finished `main`:

```bash
git fetch origin
git checkout main && git pull                 # the flattened public main
git branch develop  main && git push -u origin develop
git branch staging  main && git push -u origin staging
```

Then set `develop` as the default branch in GitHub (§5.1). (You can create the
branches before flattening if you prefer to have CI wired up first — just re-point
them at the flattened `main` afterward, since flattening rewrites `main`.)

### 4.3 FUTURE — protected space to execute untrusted tests (Docker/VMs)

*Not now — captured so the branch model has somewhere to grow into.* cscan's whole
premise is vetting **untrusted** repos/skills, and the roadmap
(`docs/future-work.md` §2, "Dynamic-analysis escalation tier") already anticipates
running targets in a disposable, network-isolated sandbox. When that lands, the
`staging` branch is the natural gate for it:

- **Isolated CI runners.** Run the sandboxed/dynamic-analysis suite on `staging`
  (and release PRs) using ephemeral, **network-egress-restricted** runners —
  GitHub-hosted runners in a dedicated environment, or self-hosted runners inside
  a locked-down VM/Firecracker/gVisor sandbox. Never on `develop` PRs from forks.
- **GitHub Environments + required reviewers.** Define a `staging` (and later
  `sandbox`) **Environment** with protection rules (required reviewers, wait
  timer, restricted secrets) so the untrusted-execution job can only run after a
  human approves it. Secrets (e.g. an `OPENAI_API_KEY` for live Tier-2
  validation) live in the environment, not the repo, and are unavailable to
  fork PRs.
- **Fork-PR safety.** Keep `pull_request` (not `pull_request_target`) triggers so
  a fork PR never gets write tokens or secrets; gate any privileged/sandboxed job
  behind the Environment approval. This is the memex "least-privilege CI"
  principle extended to code execution.
- **Kill-switch & observability.** The sandbox job should enforce no-network
  egress by default, a hard timeout, and artifact capture (the canary-event log)
  so a fired tripwire during a test run is preserved.

Deliverable when this is scheduled: a `docs/adr/` entry ("dynamic-analysis
sandbox tier") plus a `sandbox.yml` workflow gated to `staging`/release PRs and a
protected Environment. Tracked as future work, **out of scope for the initial
public launch.**

---

## 5. GitHub configuration — steps the owner/admin must take

These are **UI/settings actions** (or `gh` API calls) a repo admin performs; they
cannot be committed to the repo. Do them **after** the scaffolding PRs merge and
the branches exist, and (for the rulesets) after the workflows have run at least
once so their check names are selectable.

### 5.1 Make the repo public & set the default branch
- **Settings → General → Danger Zone → Change visibility → Public.** Do this
  **only after** §6 (flatten) if you want the internal history gone from the
  public record — visibility change exposes whatever history exists at that
  moment. (Order: scaffold → flatten `main` → create `develop`/`staging` → set
  protections → *then* flip to public.)
- **Settings → General → Default branch → `develop`.**

### 5.2 Branch protection via **Rulesets** (Settings → Rules → Rulesets)
Create one ruleset per branch (or a single ruleset targeting all three with
branch-name conditions), matching memex's "no bypass for anyone" posture:

For **`main`**, **`staging`**, **`develop`** (tighten as you go up the chain):
- **Restrict deletions** and **Block force-pushes**: on.
- **Require a pull request before merging**: on.
  - Required approvals: **1** (raise for `main`).
  - **Require review from Code Owners**: on (needs §3.3 `CODEOWNERS`).
  - **Dismiss stale approvals on new commits**: on.
- **Require status checks to pass**: on — select the checks once they've run once:
  `lint + test`, `changelog + commit guard` (or the split `changelog` job),
  `analyze (python)` (CodeQL), `pip-audit`, `bandit`, `gitleaks scan`.
  - **Require branches to be up to date before merging**: on.
- **Require linear history**: on (pairs with squash-only merging).
- **Do not allow bypass** (no bypass actors) — matches memex's "no bypass for
  anyone, maintainers included."
- For **`main`** additionally consider **Require signed commits** and a tag
  ruleset protecting `v*` tags from deletion/force-update.

### 5.3 Merge settings (Settings → General → Pull Requests)
- **Allow squash merging**: on (make it the default). **Disable** merge commits
  and rebase merging to keep history linear and one-commit-per-PR.
- **Automatically delete head branches**: on.

### 5.4 Security features (Settings → Code security and analysis)
- **Private vulnerability reporting**: **Enable** (this is the
  `security/advisories/new` endpoint `SECURITY.md` and `ISSUE_TEMPLATE/config.yml`
  point at).
- **Dependabot**: enable **alerts** and **security updates** (the version-update
  PRs come from the committed `dependabot.yml`).
- **Secret scanning** + **Push protection**: enable (defense-in-depth alongside
  the gitleaks workflow).
- **Code scanning (CodeQL)**: the committed `codeql.yml` populates the
  Code-scanning tab; confirm default setup isn't also enabled (avoid duplicate
  analyses). **Interim while private:** uploading CodeQL results needs Advanced
  Security ("Code Security"), which is off on the private repo, so the analyze
  step in `codeql.yml` ships with `upload: false` — CodeQL still builds the DB and
  runs the queries, it just skips the results upload that would otherwise error.
  **Remove that line at go-public** (code scanning is free on public repos; the
  default is to upload) so CodeQL populates the Security tab and becomes a hard,
  required check.

### 5.5 Actions permissions (Settings → Actions → General)
- **Workflow permissions → Read repository contents** (least privilege); the two
  jobs that need more request `security-events: write` explicitly in-workflow.
- **Fork PRs:** "Require approval for first-time contributors" (at least). This is
  the guardrail the future sandbox tier (§4.3) depends on.

### 5.6 Labels & Environments
- Create the **`skip-changelog`** label (used by the changelog gate) and
  **`dependencies`** label (applied by Dependabot).
- (Future, §4.3) Create a **`staging`** Environment with required reviewers and
  scoped secrets before wiring any untrusted-execution job.

### 5.7 Community health (Settings → Insights → Community Standards)
- Verify GitHub's Community Standards checklist is green: README, LICENSE,
  CODE_OF_CONDUCT, CONTRIBUTING, SECURITY, issue templates, PR template — all
  added in §3.

---

## 6. Flatten `main` into a single clean public commit

Goal: **the public `main` begins as one commit** ("Initial public release"), so
the private iteration history (6 PR merge commits, WIP commits, and the mixed
author identities `Sean Howard`, `passitalong`, `Claude`) is not part of the
public record.

### 6.1 Pre-flatten review (do not skip)
1. **Content scrub.** Confirm nothing sensitive is tracked in the *current tree*
   (the flatten keeps the tree, drops the history). A scan showed no obviously
   named secret files; still, grep the tree for anything internal before the
   public flip. The `corpus/adversarial/*` and `corpus/targeted/*` files are
   **intentional benign test fixtures** — keep them, but sanity-check they carry
   no real tokens.
2. **Resolve the license & authorship.** Land §3.1 first so the flattened commit
   already has `LICENSE` + a real `pyproject` license, and decide the single
   author/identity the initial commit should carry.
3. **Land all scaffolding first.** Everything in §3 should be merged into `main`
   (or staged in the flatten source tree) so the one public commit is complete.

### 6.2 The flatten (orphan-commit method — cleanest)
Run against the fully-scaffolded `main`. This produces a repo whose `main` has
exactly one commit whose tree == current tree:

```bash
git checkout main && git pull                    # ensure up to date
git checkout --orphan public-main                # new branch, no parents
git add -A
git commit -m "chore: initial public release

code-scanner (cscan): shell-first, uv-native supply-chain & injection
vetting toolkit. See docs/project-plan.md for architecture and status."
# Review the tree one more time:
git log --oneline            # should be exactly ONE commit
git ls-files | wc -l         # sanity-check file count matches the old main
```

Then replace `main` with this orphan (force-update — deliberate, and only valid
because we intend to discard the old history):

```bash
git branch -M public-main main                   # rename orphan onto main locally
git push --force-with-lease origin main          # publish the flattened main
```

> **Ordering vs. branch protection:** you cannot force-push to a protected `main`.
> Do the flatten **before** applying the §5.2 ruleset to `main` (or temporarily
> allow yourself as a bypass actor, flatten, then remove the bypass). The clean
> order is: scaffold → flatten `main` → create `develop`/`staging` from the
> flattened `main` (§4.2) → apply rulesets (§5.2) → flip to public (§5.1).

### 6.3 After flattening
- Recreate/repoint `develop` and `staging` at the new `main` (§4.2) — if they
  were created earlier, reset them: `git checkout develop && git reset --hard
  main && git push --force-with-lease`.
- Old PR/merge references (`#1`–`#4`) will no longer resolve to commits in
  history; that's expected and fine for a fresh public start. The `CHANGELOG.md`
  already summarizes the pre-public work for readers.
- Tags: if any `vX.Y.Z` tags exist from internal releases, decide whether to keep
  them (they'll point into discarded history) or delete and re-tag the first
  public release from the flattened `main`. Recommend **deleting internal tags**
  and letting the first public release cut a fresh `v0.4.x`/`v1.0.0` tag via the
  normal `cscan release` flow.

---

## 7. Sequenced rollout checklist

Do it in this order — scaffolding is reversible; flatten and go-public are not.

**Phase A — Scaffolding (normal PRs into `main` while still private)**
- [ ] A1. Add `LICENSE` (Apache-2.0); fix `pyproject` `license`; drop README license TODO. (§3.1)
- [ ] A2. Add `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`. (§3.2)
- [ ] A3. Add `.github/` `CODEOWNERS`, `dependabot.yml`, `PULL_REQUEST_TEMPLATE.md`, `ISSUE_TEMPLATE/*`. (§3.3)
- [ ] A4. Add `codeql.yml`, `security.yml`, `gitleaks.yml` + `.gitleaksignore`; add `uv lock --locked` to CI; extend triggers to `develop`/`staging`; add `skip-changelog` escape hatch. (§3.4)
- [ ] A5. Add `.gitattributes`; exclude `CLAUDE.md`/`AGENTS.md` from the sdist; verify with `uv build`. (§3.6)
- [ ] A6. Add `.claude/skills/` (with `NOTICE.md` + `shared/`). (§3.7)
- [ ] A7. *(Recommended)* Add `VALIDATION.md` and the two ADRs (gate authority; local-only reports). (§3.5)
- [ ] A8. Reconcile release/PR docs so "default branch" = `develop`, releases promote to `main`. (§4.1)

**Phase B — History & branches**
- [ ] B1. Pre-flatten content/authorship review. (§6.1)
- [ ] B2. Flatten `main` to one "initial public release" commit. (§6.2)
- [ ] B3. Delete stale internal tags; plan the first public release tag. (§6.3)
- [ ] B4. Create `develop` and `staging` from the flattened `main`. (§4.2)

**Phase C — GitHub settings (admin)**
- [ ] C1. Set default branch to `develop`. (§5.1)
- [ ] C2. Configure merge settings: squash-only, auto-delete head branches. (§5.3)
- [ ] C3. Create rulesets for `main`/`staging`/`develop` (required checks, CODEOWNERS review, linear history, no bypass, block force-push). (§5.2)
- [ ] C4. Enable private vuln reporting, Dependabot alerts+updates, secret scanning + push protection, CodeQL tab. (§5.4)
- [ ] C5. Set Actions to least-privilege + fork-PR approval. (§5.5)
- [ ] C6. Create `skip-changelog` + `dependencies` labels. (§5.6)
- [ ] C7. Verify Community Standards checklist is green. (§5.7)

**Phase D — Go public**
- [ ] D1. Final review, then flip visibility to **Public**. (§5.1)
- [ ] D2. Announce; confirm the security-advisory link and issue forms work from a logged-out view.

**Future (not now)**
- [ ] F1. Dynamic-analysis sandbox tier gated on `staging` via a protected Environment + isolated runners. (§4.3, `future-work.md` §2)

---

## 8. Decisions for the owner

1. **License = Apache-2.0?** (Recommended — matches memex.) This is the one
   blocking choice; everything else is license-agnostic. *(§3.1)*
2. **Default branch = `develop`?** (Recommended — matches memex; keeps `main`
   quiet between releases.) *(§4.1, §5.1)*
3. **Squash-only merges + linear history?** (Recommended — keeps the post-flatten
   `main` a clean line of release commits.) *(§5.2/§5.3)*
4. **Delete internal `vX.Y.Z` tags and re-tag from the flattened `main`?**
   (Recommended — otherwise tags dangle into discarded history.) *(§6.3)*
5. **Scope of the first public cut:** minimal (Phases A–D) vs. also landing
   VALIDATION.md + ADRs now (A7). Recommend including A7 — it's a strong trust
   signal for a *security* tool and cheap given the material already exists in
   `docs/project-plan.md`.

---

## 9. Notes & caveats

- **Flattening is irreversible for the public repo.** Keep a private mirror/backup
  of the full pre-flatten history (a private fork or an archived bundle:
  `git bundle create code-scanner-prepublic.bundle --all`) before B2, in case the
  internal history is ever needed for provenance.
- **The scaffolding must land before flatten** so the single public commit is
  complete; anything added after flatten is just normal history on top — which is
  fine, but the "clean start" is nicer if A1–A8 are already in the tree.
- **Required status checks can only be selected after they've run once.** Push the
  workflows, let them run on a throwaway PR, then pick their check names in the
  ruleset (§5.2).
- This plan intentionally **keeps cscan's stricter 3-day cooldown** rather than
  matching memex's 5-day window — do not "align" it downward.
