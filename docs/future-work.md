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

- **What:** A `airlock export` that packages a run's files into a portable,
  optionally-signed bundle (the index is rebuilt on the other side via
  `airlock index rebuild`).
- **Why deferred:** Core file-primary persistence + rebuildable index (M0) is the
  prerequisite; signing/packaging is a follow-on convenience.
- **Pull-in trigger:** Teams routinely sharing verdicts and wanting integrity
  guarantees on shared bundles.

---

# Complementary detection approaches (stack with the canary)

The canary tripwire detects exactly one failure mode: **action-seeking**
injection (the model is steered into *calling* something). The brief's research
points at several other approaches that test *different* things and therefore
compose well with — rather than duplicate — the canary. None of these is in the
committed plan for this phase; each is captured here with how it stacks.

## 7. Verdict-corruption detection (consistency & control probes)

- **What:** Actively detect the failure mode the canary *cannot* see —
  injection that only tries to make the reviewer *output* "clean." Techniques:
  (a) **multi-sample / paraphrase consistency** — classify a file N times (and/or
  with reworded system framing); instability flags manipulation; (b) **planted
  control files** — inject known-clean and known-malicious controls into each run
  and alarm if their verdicts skew; (c) cross-model agreement (see #11).
- **Why deferred:** The plan already *neutralizes* verdict corruption
  architecturally (Tier-1 stays authoritative; the LLM is advisory and can only
  *raise* attention — plan §2 N5, R1, S4). An active *detector* is additive
  hardening, not required for safety.
- **Stacks with canary by:** covering the explicit blind spot the brief calls out
  ("verdict-corrupting injection will not fire a canary"). Canary = *did it try
  to act*; this = *did the content bend the verdict*.
- **Pull-in trigger:** Evidence of verdict-skewing payloads in the corpus, or a
  desire to promote Tier-2 from purely advisory toward semi-trusted.
- **Cite:** Strategy B "honest boundary"; detection-limits (guard-model
  over-defense ~60%) in the brief.

## 8. Honeytokens / canary-token data tripwires

- **What:** A *data-level* complement to the *tool-level* NOOP canaries. Seed the
  quarantine context (and, with a future sandbox tier, the workspace) with fake
  but enticing secrets — bogus API keys, `.env` values, internal URLs, unique
  [canarytoken](https://canarytokens.org)-style strings. If an exfil-seeking
  injection scoops them up, they appear verbatim in a fired canary's captured
  `tool_input` (e.g. `http_request(body="<planted .env>")`) — and, under a
  sandbox, a token callback would prove real exfiltration.
- **Why deferred:** Needs the canary subsystem (M3) first, and token minting /
  optional callback infrastructure; the core verdict path doesn't depend on it.
- **Stacks with canary by:** the canary reports *that* the model tried to act and
  *what tool*; honeytokens reveal *what data the attack was after* and give an
  unambiguous, attacker-attributable artifact. Two orthogonal signals from one
  fire.
- **Pull-in trigger:** Wanting exfil-intent attribution, or pairing with the
  dynamic-sandbox tier (#2) for true-positive confirmation.
- **Cite:** Embrace The Red exfiltration case studies (ZombAIs); the brief's
  "forensically rich" canary argument.

## 9. Second deterministic taint engine (CodeQL)

- **What:** Add **CodeQL** as a second, independent source→sink taint engine
  alongside Semgrep taint mode (plan M1), normalized into the same `Finding`
  model. Different query language, different coverage and language support.
- **Why deferred:** Semgrep taint is the committed engine for this phase; CodeQL
  adds database-build time, tooling, and licensing considerations. It's
  additive deterministic coverage, not a gap in the gate.
- **Stacks with canary by:** it is **deterministic and not prompt-injectable** —
  it strengthens the *authoritative* tier on a completely different axis from the
  LLM/canary tier. Two engines also reduce single-tool blind spots.
- **Pull-in trigger:** Languages/patterns Semgrep misses, or wanting a
  cross-engine "both must agree / either may flag" policy.
- **Cite:** brief §2 static taint analysis (Semgrep, **CodeQL**, CMU SEI
  static malicious-code detection).

## 10. Borrow the remaining "Design Patterns" hardening

- **What:** The plan already uses **Dual LLM** and **LLM Map-Reduce** from the
  design-patterns paper. The other patterns are borrowable: **Context-
  Minimization** (strip everything but the bytes under analysis from the
  reviewer's context — directly applicable to the quarantine), **Plan-Then-
  Execute** / **Action-Selector** / **Code-Then-Execute** (constrain any future
  action-taking tier so control flow is fixed before untrusted data is read).
- **Why deferred:** Context-Minimization is a cheap reviewer-side hardening worth
  doing soon; the action-oriented patterns only matter if Tier-2 ever gains
  capabilities — which is explicitly a **non-goal** this phase (plan N1/N4).
- **Stacks with canary by:** shrinks the attack surface the canary is watching
  (less context for an injection to exploit) and pre-commits control flow so an
  injection has less to steer — defense-in-depth around the same chokepoint.
- **Pull-in trigger:** Reviewer context bloat/cost, or any move to give Tier-2 a
  parameterized action.
- **Cite:** *Design Patterns for Securing LLM Agents against Prompt Injections*
  ([arXiv:2506.08837](https://arxiv.org/abs/2506.08837); Willison commentary).

## 11. Cross-model ensemble + advisory guard-model (with over-defense guardrails)

- **What:** (a) **Ensemble** — run per-file classification across two different
  model *families*; divergence is a high-signal review flag and raises the
  evasion bar (an attack must transfer across models). (b) Optionally add a
  dedicated **injection guard/classifier** as a *purely advisory* layer.
- **Why deferred:** Multiplies token cost/latency, and the brief is emphatic that
  detector/guard models suffer **over-defense** (accuracy collapsing toward
  ~random on trigger-word-heavy benign inputs) and are **evadable** (GCG-style
  suffixes >99% bypass on activation/task-drift probes). So this must **never**
  become the gate — Tier-1 stays authoritative.
- **Stacks with canary by:** tests "*does this content look like injection*"
  (content signal) vs the canary's "*did the model act*" (behavioral signal) —
  and ensemble disagreement catches model-specific evasions a single reviewer
  misses. Measure its FP impact on the C-trigger corpus before enabling.
- **Pull-in trigger:** A measured detection gap where the cost is justified and
  over-defense is controlled.
- **Cite:** brief §2 detection-limits (guard over-defense, GCG/task-drift
  evasion); AgentDojo ([arXiv:2406.13352](https://arxiv.org/abs/2406.13352)) for
  measuring it.
