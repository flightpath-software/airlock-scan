---
id: ADR-0001
title: The deterministic Tier-1 gate is authoritative; the LLM tier is advisory
date: 2026-07-21
decider: Sean Howard
status: accepted
---

# ADR-0001 — The deterministic tier is authoritative

## Context

`cscan` vets **untrusted** repositories and skills. Its second (Tier-2) tier reads
untrusted content with an LLM to surface semantic risks the deterministic scanners
miss. But *the act of an LLM reading untrusted content is itself the attack surface*:
an indirect prompt injection can try to make the reviewer emit a "looks clean"
verdict. If an LLM verdict could clear or downgrade a deterministic finding, a single
crafted file could talk its way past the gate.

## Decision

The **deterministic tier is authoritative.** Tier-1 scanners (gitleaks, semgrep,
osv-scanner, guarddog, heckler) run against the target as *data*, normalize into one
`Finding` model, and drive the gate. The Tier-2 LLM reviewer is **advisory only**: it
can *raise* attention (add flags, force `NEEDS_REVIEW`) but can **never clear,
downgrade, or override** a Tier-1 finding, and a fired canary tripwire forces human
review regardless of any verdict. The gate decision lives in `gate.py`, not in the
model's output.

## Alternatives considered

- **Let the LLM produce the final verdict.** Rejected — it makes the gate
  prompt-injectable by construction and defeats the tool's purpose.
- **Let the LLM downgrade Tier-1 findings it judges to be false positives.**
  Rejected — the same injection channel could manufacture that judgment; false-positive
  tuning belongs in the deterministic rules, not the LLM.

## Consequences

- The gate is reproducible and explainable, and works with **no LLM key at all** —
  Tier-2 is a pure add-on.
- The LLM can only ever make the result *more* cautious, never less. Verdict-corruption
  attempts are neutralized rather than merely detected.
- Enforced by tests: `tests/test_gate.py::test_block_on_finding_at_gate`,
  `::test_canary_wins_even_if_verdict_also_present`,
  `::test_block_on_canary_even_without_findings`,
  `::test_gate_blocks_high_but_passes_when_threshold_is_critical`, and
  `tests/test_vet.py::test_ingest_blocks_on_high`.
