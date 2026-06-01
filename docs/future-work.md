# Future work / deferred backlog

Candidate enhancements that are **intentionally out of the committed milestones**
in [project-plan.md](project-plan.md). Each entry records *what*, *why it's
deferred*, and *what would trigger pulling it in*. This is the home for ideas
that are relevant but not yet scheduled — not a commitment.

> Naming note: this file is `future-work.md` (not `feature-pipeline.md`) to avoid
> confusion with the product's two-tier *pipeline*. Rename if you prefer.

---

## 1. YARA signature scanning (Tier 1)

- **What:** Add a `yara` adapter (`scanners/yara.sh` + `[scanners.yara]` in
  `config/scanners.toml`) running curated rule families against the target,
  normalized into the existing `Finding` model like every other scanner.
- **Why deferred:** The brief and the early SPEC both list YARA, but it adds a
  signature-set to source, vet, and *maintain* (rules go stale, false-positive
  tuning is ongoing). The current deterministic tier (gitleaks, semgrep,
  osv-scanner, guarddog, heckler) already covers secrets, SAST/taint, vulnerable
  deps, malicious-package indicators, and Trojan-Source — YARA is additive, not
  blocking. Decision (this planning pass): **keep the current set; capture YARA
  here.**
- **Pull-in trigger:** A concrete need for known-bad *family* signatures (e.g. a
  specific malware/worm class such as Glassworm variants) that taint + package
  indicators don't catch, or a maintained rule source we trust.
- **Notes:** Fits cleanly as "just another adapter"; no architectural change.
  Semgrep already does pattern matching, so scope YARA to binary/family
  signatures to avoid overlap.

## 2. Dynamic-analysis escalation tier (disposable sandbox)

- **What:** For the small "suspicious-but-unclear" set Tier 1 flags, optionally
  execute the target in a disposable, **network-isolated** sandbox to observe
  real behavior (exfil attempts, install-hook side effects).
- **Why deferred:** Out of scope per the brief's non-goals (this is *pre-install*
  triage, no execution). Sandboxes also face environment-aware evasion (malware
  that stays dormant when it detects a sandbox).
- **Pull-in trigger:** Demand for behavioral confirmation on the unclear minority
  that static analysis can't resolve, plus a hardened sandbox runtime.

## 3. CaMeL-style capability tracking

- **What:** Attach capabilities to values and enforce "this data cannot reach
  that capability" as an explicit data-flow policy (beyond the structural
  Dual-LLM quarantine), per the CaMeL paper.
- **Why deferred:** The Dual-LLM + no-functional-tools + canary design already
  makes action-seeking injection structurally inert for *this* pipeline; full
  capability tracking is a larger framework better justified once the core ships.
- **Pull-in trigger:** Expanding Tier 2 beyond pure classification into anything
  that takes parameterized actions.

## 4. Harness-signature dataset maintenance & expansion

- **What:** Keep `harness_signatures.yaml` current as agent tools rename/add;
  expand coverage (e.g. Cursor CLI low-confidence names, Warp once names are
  public) and add a refresh/lint check.
- **Why deferred:** The vendored snapshot (`schema_version`, `generated`,
  per-entry `confidence`) is sufficient to ship M4 fingerprinting; ongoing
  curation is operational, not blocking.
- **Pull-in trigger:** Observed drift (a fingerprint stops matching) or a new
  harness worth attributing.

## 5. anti-trojan-source second opinion (already optional)

- **What:** Promote the optional `anti-trojan-source` (Node/`npx`) adapter to a
  routinely-run second opinion alongside `heckler` for Unicode/bidi findings.
- **Why deferred:** Adds a Node dependency; `heckler` already covers the primary
  vector. Keep optional until a gap motivates it.
- **Pull-in trigger:** A Trojan-Source class `heckler` misses that
  `anti-trojan-source` catches.

## 6. Shareable report bundles / signing

- **What:** A `cscan export` that packages a run's files into a portable,
  optionally-signed bundle (the index is rebuilt on the other side via
  `cscan index rebuild`).
- **Why deferred:** Core file-primary persistence + rebuildable index (M0) is the
  prerequisite; signing/packaging is a follow-on convenience.
- **Pull-in trigger:** Teams routinely sharing verdicts and wanting integrity
  guarantees on shared bundles.
