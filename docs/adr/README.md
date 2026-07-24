# Architecture Decision Records

Short, dated notes that capture **why** a non-obvious decision was made — the context
and the trade-off — so a future reader doesn't have to reverse-engineer it from the
code or re-litigate it. They are a living log, not a design spec: most are a single
paragraph or two.

## Reading them

Files are numbered sequentially (`0001-slug.md`, `0002-slug.md`, …). Each has
frontmatter (`id`, `title`, `date`, `decider`) and an optional `status`
(`proposed` · `accepted` · `deprecated` · `superseded` · `rejected`). Superseded ADRs
are **kept**, marked `status: superseded` with `superseded_by: ADR-####` — the
evolution is part of the value.

## The current set

| ADR | Decision |
|---|---|
| [0001](0001-deterministic-tier-authoritative.md) | The deterministic Tier-1 gate is authoritative; the LLM tier is advisory and can never clear a Tier-1 finding |
| [0002](0002-local-only-reports.md) | Reports stay local to the user; nothing is written into the scanned repo, and nothing leaves the machine except a configured Tier-2 call or an explicit export |

## Adding one

**When to add one — all three must be true; otherwise skip it:**

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will look at the code and wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and one was chosen for a reason worth recording.

Copy the frontmatter shape of an existing ADR, give it the next number, set
`status: accepted` (or `proposed` if still under discussion), and add a row to the
table above. **Keep the body to a single paragraph: the decision and the trade-off
it settles — nothing else.** Record the alternatives you rejected as a `considering:`
list in the frontmatter, not in prose. Do **not** write out the decision's impact, the
work it creates, or what flows from it — that belongs in code, `VALIDATION.md`, or a
project plan. A meandering ADR is one no one reads.
