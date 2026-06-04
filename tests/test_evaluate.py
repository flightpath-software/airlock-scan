"""Tests for the M5 evaluation harness and labeled corpus."""

from __future__ import annotations

from pathlib import Path

from code_scanner.canary import build_canary_set
from code_scanner.evaluate import (
    CorpusItem,
    evaluate,
    heuristic_responder,
    load_corpus,
    render_eval_markdown,
)
from code_scanner.llm_backend import FakeBackend
from code_scanner.quarantine import FileVerdict, QuarantineReviewer, ReviewOutcome

_CORPUS = Path(__file__).resolve().parents[1] / "corpus"


# --- corpus -----------------------------------------------------------------

def test_corpus_loads_and_is_well_formed():
    items = load_corpus(_CORPUS)
    assert len(items) >= 8
    for it in items:
        assert it.path.is_file(), f"missing fixture: {it.rel}"
        assert it.label in {"clean", "injection"}
        if it.category == "targeted":
            assert it.expected_harness, f"targeted item needs expected_harness: {it.rel}"


# --- metric math (stub reviewer) -------------------------------------------

def _clean_outcome(rel):
    return ReviewOutcome(
        verdict=FileVerdict(rel, contains_injection=False, confidence=1.0, summary="ok", status="OK")
    )


def _canary_outcome(rel, harness):
    return ReviewOutcome(
        verdict=FileVerdict(rel, contains_injection=True, confidence=1.0, summary="fired",
                            status="HUMAN_REVIEW"),
        canary_event={"harness": harness, "tool": "x"},
    )


class _StubReviewer:
    def __init__(self, by_rel):
        self.by_rel = by_rel

    def review_file(self, rel, data):  # noqa: ARG002 - content unused in the stub
        return self.by_rel[rel]


def test_metric_math(tmp_path):
    specs = [
        ("c1", "clean", "clean", None, _clean_outcome("c1")),
        ("c2", "trigger", "clean", None, _canary_outcome("c2", "cursor")),   # false positive
        ("i1", "adversarial", "injection", None, _canary_outcome("i1", None)),
        ("i2", "adversarial", "injection", None, _clean_outcome("i2")),       # missed (FN)
        ("t1", "targeted", "injection", "cursor", _canary_outcome("t1", "cursor")),   # correct
        ("t2", "targeted", "injection", "codex_cli", _canary_outcome("t2", "cline")),  # wrong
    ]
    items, by_rel = [], {}
    for rel, cat, label, harness, outcome in specs:
        f = tmp_path / rel
        f.write_text("x", encoding="utf-8")
        items.append(CorpusItem(f, rel, cat, label, harness))
        by_rel[rel] = outcome

    report = evaluate(_StubReviewer(by_rel), items)
    assert report.detection_rate == 0.75       # 3 of 4 injection flagged
    assert report.canary_fp_rate == 0.5         # 1 of 2 clean fired a canary
    assert report.flag_fp_rate == 0.5
    attr = report.attribution
    assert attr == {"targeted": 2, "fired": 2, "correct": 1, "accuracy": 0.5}

    md = render_eval_markdown(report)
    assert "Detection rate" in md and "false positives" in md


# --- heuristic backend over the real corpus (offline integration) ----------

def test_heuristic_backend_over_real_corpus():
    items = load_corpus(_CORPUS)
    canaries = build_canary_set(
        ("claude_code", "codex_cli", "gemini_cli", "cursor", "opencode", "zed", "cline", "warp"),
        include_agnostic=True,
    )
    reviewer = QuarantineReviewer(FakeBackend(heuristic_responder), canaries)
    report = evaluate(reviewer, items)

    # Every injection fixture names a tool -> all detected.
    assert report.detection_rate == 1.0
    # Trigger fixtures *mention* tools -> they fire (over-defense); truly clean don't.
    assert report.canary_fp_rate == 0.5
    # Each targeted payload is attributed to the right harness.
    assert report.attribution["accuracy"] == 1.0


def test_fake_baseline_is_silent():
    # The always-clean baseline catches nothing and never false-positives.
    items = load_corpus(_CORPUS)
    canaries = build_canary_set(("cursor",), include_agnostic=True)
    reviewer = QuarantineReviewer(FakeBackend(), canaries)
    report = evaluate(reviewer, items)
    assert report.detection_rate == 0.0
    assert report.canary_fp_rate == 0.0
