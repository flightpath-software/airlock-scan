"""Evaluation harness — measure the pipeline against a labeled corpus.

Loads a labeled corpus (clean / trigger-word-heavy clean / adversarial /
harness-targeted), runs the Tier-2 reviewer over each file, and computes the
metrics that matter for this project:

* **detection rate** — injection-labeled files that get flagged,
* **canary false-positive rate** — *clean* files (especially the trigger corpus)
  that nonetheless fire a canary — the headline over-defense metric,
* **harness attribution accuracy** — targeted payloads attributed to the right
  harness.

The corpus + metrics math are deterministic; the *backend* is pluggable, so the
same harness scores a real model (``cscan-helper eval``) or, offline, a baseline
``FakeBackend`` or the naive :func:`heuristic_responder` (which illustrates how a
"fires on any tool mention" model over-defends on the trigger corpus).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from code_scanner.llm_backend import BackendResponse, ToolCall

LABELS_FILE = "labels.json"
_LABELS = {"clean", "injection"}


@dataclass(frozen=True, slots=True)
class CorpusItem:
    path: Path
    rel: str
    category: str
    label: str  # "clean" | "injection"
    expected_harness: str | None


def load_corpus(root: Path) -> list[CorpusItem]:
    """Load a labeled corpus from ``<root>/labels.json``."""
    root = root.expanduser()
    data = json.loads((root / LABELS_FILE).read_text(encoding="utf-8"))
    items: list[CorpusItem] = []
    for entry in data.get("items", []):
        label = entry["label"]
        if label not in _LABELS:
            raise ValueError(f"bad label {label!r} for {entry['path']}")
        items.append(
            CorpusItem(
                path=root / entry["path"],
                rel=entry["path"],
                category=entry["category"],
                label=label,
                expected_harness=entry.get("expected_harness"),
            )
        )
    return items


@dataclass(frozen=True, slots=True)
class ItemResult:
    item: CorpusItem
    flagged: bool  # predicted "injection" (canary fired or verdict said so)
    canary_fired: bool
    attributed_harness: str | None
    status: str


@dataclass(slots=True)
class EvalReport:
    results: list[ItemResult]

    def _label(self, label: str) -> list[ItemResult]:
        return [r for r in self.results if r.item.label == label]

    @property
    def injection(self) -> list[ItemResult]:
        return self._label("injection")

    @property
    def clean(self) -> list[ItemResult]:
        return self._label("clean")

    @staticmethod
    def _rate(num: int, den: int) -> float:
        return round(num / den, 4) if den else 0.0

    @property
    def detection_rate(self) -> float:
        inj = self.injection
        return self._rate(sum(r.flagged for r in inj), len(inj))

    @property
    def canary_fp_rate(self) -> float:
        cl = self.clean
        return self._rate(sum(r.canary_fired for r in cl), len(cl))

    @property
    def flag_fp_rate(self) -> float:
        cl = self.clean
        return self._rate(sum(r.flagged for r in cl), len(cl))

    @property
    def attribution(self) -> dict:
        targeted = [r for r in self.injection if r.item.expected_harness]
        fired = [r for r in targeted if r.canary_fired]
        correct = [r for r in fired if r.attributed_harness == r.item.expected_harness]
        return {
            "targeted": len(targeted),
            "fired": len(fired),
            "correct": len(correct),
            "accuracy": self._rate(len(correct), len(fired)),
        }

    def category_counts(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in self.results:
            c = out.setdefault(r.item.category, {"n": 0, "flagged": 0, "canary": 0})
            c["n"] += 1
            c["flagged"] += int(r.flagged)
            c["canary"] += int(r.canary_fired)
        return out

    def as_dict(self) -> dict:
        return {
            "metrics": {
                "detection_rate": self.detection_rate,
                "canary_fp_rate": self.canary_fp_rate,
                "flag_fp_rate": self.flag_fp_rate,
                "attribution": self.attribution,
            },
            "category_counts": self.category_counts(),
            "items": [
                {
                    "rel": r.item.rel,
                    "category": r.item.category,
                    "label": r.item.label,
                    "flagged": r.flagged,
                    "canary_fired": r.canary_fired,
                    "expected_harness": r.item.expected_harness,
                    "attributed_harness": r.attributed_harness,
                    "status": r.status,
                }
                for r in self.results
            ],
        }


def evaluate(reviewer, items: list[CorpusItem]) -> EvalReport:
    """Run ``reviewer`` over each corpus item and score the predictions.

    ``reviewer`` only needs a ``review_file(rel, content_bytes) -> ReviewOutcome``
    method, so a stub can drive the metric math in tests.
    """
    results: list[ItemResult] = []
    for item in items:
        data = item.path.read_bytes()
        outcome = reviewer.review_file(item.rel, data)
        event = outcome.canary_event or {}
        results.append(
            ItemResult(
                item=item,
                flagged=bool(outcome.verdict.contains_injection),
                canary_fired=outcome.canary_event is not None,
                attributed_harness=event.get("harness"),
                status=outcome.verdict.status,
            )
        )
    return EvalReport(results)


def render_eval_markdown(report: EvalReport) -> str:
    m = report.as_dict()["metrics"]
    a = m["attribution"]
    lines = [
        "# cscan evaluation",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Detection rate (injection recall) | {m['detection_rate']:.0%} |",
        f"| Canary false-positive rate (clean) | {m['canary_fp_rate']:.0%} |",
        f"| Any-flag false-positive rate (clean) | {m['flag_fp_rate']:.0%} |",
        f"| Harness attribution accuracy | {a['accuracy']:.0%} ({a['correct']}/{a['fired']}) |",
        "",
        "## Per-category",
        "",
        "| Category | Files | Flagged | Canary fires |",
        "| --- | --- | --- | --- |",
    ]
    for cat, c in sorted(report.category_counts().items()):
        lines.append(f"| {cat} | {c['n']} | {c['flagged']} | {c['canary']} |")
    # Surface clean files that fired a canary — the false positives to fix.
    fps = [r for r in report.clean if r.canary_fired]
    if fps:
        lines += ["", "## ⚠ Clean files that fired a canary (false positives)", ""]
        for r in fps:
            lines.append(f"- `{r.item.rel}` → {r.attributed_harness or 'agnostic'}")
    return "\n".join(lines) + "\n"


# --- offline demo backend --------------------------------------------------

# Only treat *distinctive* tool names (underscored or containing uppercase) as
# triggers, so the heuristic doesn't fire on ordinary prose like "read the docs".
def _distinctive(name: str) -> bool:
    return "_" in name or any(c.isupper() for c in name)


def heuristic_responder(system: str, user: str, tools: list[dict]) -> BackendResponse:
    """Naive offline model: fire a canary if the content names a tool, else clean.

    This is a *test/demo* stand-in — it illustrates the over-defense failure mode
    (it fires on the trigger corpus, which merely *mentions* tools). It is not a
    real detector.
    """
    names = [
        t["function"]["name"]
        for t in tools
        if t["function"]["name"] != "submit_verdict" and _distinctive(t["function"]["name"])
    ]
    for name in sorted(names, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name)}\b", user):
            return BackendResponse(tool_calls=[ToolCall(name, {"args": "(heuristic match)"})])
    return BackendResponse(
        tool_calls=[
            ToolCall(
                "submit_verdict",
                {"contains_injection": False, "confidence": 0.5, "summary": "no tool mention"},
            )
        ]
    )
