"""Gate logic — turn findings, canary events, and Tier-2 verdicts into a verdict.

The gate encodes the project's core invariant: **Tier 1 is authoritative; Tier 2
is advisory.** Deterministic findings at/above the configured severity, and any
canary fire (a confirmed injection *attempt*), drive a ``BLOCK``. The LLM tier
can only *raise* attention to ``NEEDS_REVIEW`` — it can never clear a Tier-1
finding or, on its own, downgrade a run to ``CLEAN``.

Precedence (highest wins): BLOCK > NEEDS_REVIEW > WARN > CLEAN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

from airlock_scan.findings import Finding, Severity

# Tier-2 statuses that mean "a human must look" (see store / quarantine).
_REVIEW_STATUSES = {"NEEDS_REVIEW", "HUMAN_REVIEW", "MALFORMED"}


class GateVerdict(IntEnum):
    """Run-level outcome, orderable so the most severe wins."""

    CLEAN = 0
    WARN = 1
    NEEDS_REVIEW = 2
    BLOCK = 3

    @property
    def label(self) -> str:
        return self.name


@dataclass(slots=True)
class GateDecision:
    verdict: GateVerdict
    reasons: list[str] = field(default_factory=list)

    @property
    def installable(self) -> bool:
        """Only a CLEAN/WARN run is a candidate for install (human decides)."""
        return self.verdict <= GateVerdict.WARN

    def summary_line(self) -> str:
        head = self.reasons[0] if self.reasons else "no findings"
        return f"[{self.verdict.label}] {head}"


def decide(
    findings: list[Finding],
    *,
    gate: Severity = Severity.HIGH,
    canary_events: list[dict] | None = None,
    file_verdicts: list[dict] | None = None,
) -> GateDecision:
    """Compute the run verdict. ``findings`` are authoritative; the rest advisory."""
    canary_events = canary_events or []
    file_verdicts = file_verdicts or []
    reasons: list[str] = []
    verdict = GateVerdict.CLEAN

    def raise_to(level: GateVerdict, reason: str) -> None:
        nonlocal verdict
        if level > verdict:
            verdict = level
        reasons.append(reason)

    # --- BLOCK (authoritative) ---------------------------------------------
    blocking = [f for f in findings if f.severity >= gate]
    if blocking:
        tools = sorted({f.tool for f in blocking})
        raise_to(
            GateVerdict.BLOCK,
            f"{len(blocking)} deterministic finding(s) at/above {gate.label} "
            f"from {', '.join(tools)}",
        )
    if canary_events:
        tools = sorted({str(e.get("tool")) for e in canary_events})
        raise_to(
            GateVerdict.BLOCK,
            f"{len(canary_events)} canary tripwire fire(s) — attempted prompt "
            f"injection via {', '.join(tools)}",
        )

    # --- NEEDS_REVIEW (advisory raises attention) --------------------------
    flagged = [
        v
        for v in file_verdicts
        if v.get("contains_injection") or str(v.get("status", "")).upper() in _REVIEW_STATUSES
    ]
    if flagged:
        raise_to(
            GateVerdict.NEEDS_REVIEW,
            f"{len(flagged)} file(s) flagged by the advisory Tier-2 reviewer",
        )

    # --- WARN (sub-gate deterministic findings) ----------------------------
    sub_gate = [f for f in findings if Severity.LOW <= f.severity < gate]
    if sub_gate:
        raise_to(
            GateVerdict.WARN,
            f"{len(sub_gate)} finding(s) below the {gate.label} gate",
        )

    if not reasons:
        reasons.append("no findings at or above any threshold")
    return GateDecision(verdict=verdict, reasons=reasons)
