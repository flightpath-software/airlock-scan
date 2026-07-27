---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when the user wants to pin down domain terminology or a ubiquitous language, record an architectural decision, or when another skill needs to maintain the domain model.
source: mattpocock
forked: revised for the airlock-scan repo structure
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill — that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

airlock-scan is a single-context repo:

```
/
├── CONTEXT.md                                        ← the glossary (created lazily)
├── docs/
│   └── adr/
│       ├── 0001-deterministic-tier-authoritative.md
│       └── 0002-local-only-reports.md
└── src/airlock_scan/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one
when the first term is resolved. New ADRs go in `docs/adr/` (which already exists).

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'finding' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'scan' — do you mean a Tier-1 deterministic run or the full Tier-1+Tier-2 vet? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts (e.g. "a canary fires *and* the LLM returns a clean verdict — what's the gate result?").

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "You said the LLM tier can downgrade a finding, but `gate.py` makes Tier-1 authoritative — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](../shared/CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the canonical format and process in
[`docs/adr/README.md`](../../../docs/adr/README.md) ("Adding one") — a single decision paragraph,
alternatives in `considering:` frontmatter, no impact/consequences prose.
