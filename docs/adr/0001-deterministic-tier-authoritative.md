---
id: ADR-0001
title: The deterministic Tier-1 gate is authoritative; the LLM tier can never clear a finding
date: 2026-07-21
decider: sean
status: accepted
considering:
  - let-the-llm-write-the-final-verdict
  - let-the-llm-downgrade-tier-1-false-positives
---

airlock's Tier-2 reviewer reads untrusted repo content with an LLM, so an indirect
prompt injection can try to talk the reviewer into a "looks clean" verdict — the act
of reading is itself the attack surface. The gate verdict is therefore computed only
by the deterministic Tier-1 scanners; the LLM tier is advisory and may raise concern
or force review, but can never clear, downgrade, or override a Tier-1 finding, and a
fired canary forces human review regardless of any verdict. Letting the model author
or adjust the verdict was the obvious alternative and is rejected because it makes the
gate itself injectable — the determinism is the product, not an implementation detail.
