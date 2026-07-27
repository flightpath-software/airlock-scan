# CONTEXT.md Format

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Finding**:
{A one or two sentence description of the term}
_Avoid_: Issue, alert, hit

**Verdict**:
{A one or two sentence description of the term}
_Avoid_: Result, score, grade
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong even if the project uses them extensively. Before adding a term, ask: is this a concept unique to this context, or a general programming concept? Only the former belongs. (For airlock, terms like Finding, Verdict, Tier-1/Tier-2, canary/tripwire, harness signature, quarantine, and the run store belong; "SARIF" or "subprocess" do not.)
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.

## Single vs multi-context repos

**Single context (airlock-scan, and most repos):** one `CONTEXT.md` at the repo root.

**Multiple contexts:** a `CONTEXT-MAP.md` at the repo root lists the contexts, where they live, and how they relate:

```md
# Context Map

## Contexts

- [Deterministic tier](./src/pkg/tier1/CONTEXT.md) — runs non-LLM scanners and computes the authoritative gate verdict
- [Advisory tier](./src/pkg/tier2/CONTEXT.md) — quarantined LLM review with canary tripwires

## Relationships

- **Deterministic → Advisory**: the deterministic tier's verdict is authoritative; the advisory tier may only raise attention, never clear a finding
```

The skill infers which structure applies:

- If `CONTEXT-MAP.md` exists, read it to find contexts
- If only a root `CONTEXT.md` exists, single context
- If neither exists, create a root `CONTEXT.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.
