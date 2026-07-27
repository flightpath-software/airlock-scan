"""Thin command-line entry point for the Python helper.

This is invoked by the shell layer, e.g. ``uv run airlock-helper report <dir> --gate high``.
It deliberately stays small: parse args, load+merge findings, render, and exit with a code
the shell can branch on.

Exit codes:
  0  success, findings below the gate (PASS)
  1  blocking findings at or above the gate (FAIL)
  2  argument/usage error (argparse default)
  3  unexpected internal error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from airlock_scan import __version__
from airlock_scan.findings import Severity
from airlock_scan.parsers import load_results_dir
from airlock_scan.report import build_report, render

_GATE_CHOICES = ["critical", "high", "medium", "low", "info"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="airlock-helper",
        description="Parse, merge and gate scanner output for the airlock toolkit.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser(
        "report",
        help="Merge result files in a directory and apply a severity gate.",
    )
    report.add_argument(
        "results_dir",
        type=Path,
        help="Directory containing scanner output (e.g. <target>/.airlock).",
    )
    report.add_argument(
        "--gate",
        choices=_GATE_CHOICES,
        default="high",
        help="Fail (exit 1) if any finding is at or above this severity. Default: high.",
    )
    report.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a table.",
    )

    # ingest — normalize Tier-1 scanner output into a user-local ~/airlock run.
    ingest = sub.add_parser(
        "ingest",
        help="Ingest scanner output into a ~/airlock run (report.json + report.md + index).",
    )
    ingest.add_argument(
        "results_dir",
        type=Path,
        help="Directory containing scanner output (e.g. <target>/.airlock).",
    )
    ingest.add_argument("--target", type=Path, default=None, help="Path that was scanned.")
    ingest.add_argument(
        "--gate",
        choices=_GATE_CHOICES,
        default="high",
        help="Fail (exit 1) if any finding is at or above this severity. Default: high.",
    )

    # index — manage the derived, rebuildable SQLite index over a run directory.
    index = sub.add_parser("index", help="Manage the derived SQLite index for a run.")
    index_sub = index.add_subparsers(dest="index_command", required=True)
    index_rebuild = index_sub.add_parser(
        "rebuild",
        help="Rebuild <run-dir>/index.db from the run's files alone.",
    )
    index_rebuild.add_argument("run_dir", type=Path, help="A airlock run directory.")

    # canary — inspect the inert decoy tool registry and harness attribution.
    canary = sub.add_parser("canary", help="Inspect canary tripwires / harness fingerprinting.")
    canary_sub = canary.add_subparsers(dest="canary_command", required=True)
    canary_list = canary_sub.add_parser("list", help="List the decoy tool set.")
    canary_list.add_argument(
        "--harness",
        action="append",
        dest="harnesses",
        help="Harness id to include (repeatable). Defaults to configured sets.",
    )
    canary_list.add_argument(
        "--no-agnostic",
        action="store_true",
        help="Exclude the harness-agnostic decoy set.",
    )
    canary_list.add_argument("--json", action="store_true", help="Emit JSON.")
    canary_attr = canary_sub.add_parser(
        "attribute",
        help="Show which harness a fired decoy name fingerprints.",
    )
    canary_attr.add_argument("tool_name", help="The fired canary tool name.")
    canary_attr.add_argument("--json", action="store_true", help="Emit JSON.")

    # quarantine — Tier-2 per-file LLM review into a user-local run store.
    quarantine = sub.add_parser(
        "quarantine",
        help="Run the Tier-2 quarantined reviewer over a target directory.",
    )
    quarantine.add_argument("target", type=Path, help="Directory to review.")
    quarantine.add_argument(
        "--fake",
        action="store_true",
        help="Use the offline FakeBackend (no API key, no network) for a dry run.",
    )
    quarantine.add_argument(
        "--gate",
        choices=_GATE_CHOICES,
        default="high",
        help="Severity gate for the run verdict. Default: high.",
    )
    quarantine.add_argument(
        "--no-localize",
        action="store_true",
        help="Disable canary-fire bisection (cheaper; skips the extra probe calls).",
    )

    # vet — the unified run: merge Tier-1 scanner output + Tier-2 quarantine.
    vet = sub.add_parser(
        "vet",
        help="Unified run: merge Tier-1 findings (--tier1-results) + Tier-2 into one ~/airlock run.",
    )
    vet.add_argument("target", type=Path, help="Directory to vet.")
    vet.add_argument(
        "--tier1-results",
        type=Path,
        default=None,
        dest="tier1_results",
        help="Directory of Tier-1 scanner output to merge (from scripts/scan.sh).",
    )
    vet.add_argument(
        "--fake",
        action="store_true",
        help="Use the offline FakeBackend (no API key, no network) for a dry run.",
    )
    vet.add_argument(
        "--gate",
        choices=_GATE_CHOICES,
        default="high",
        help="Severity gate for the run verdict. Default: high.",
    )
    vet.add_argument(
        "--no-localize",
        action="store_true",
        help="Disable canary-fire bisection (cheaper; skips the extra probe calls).",
    )

    # eval — score the pipeline against a labeled corpus.
    ev = sub.add_parser(
        "eval",
        help="Evaluate the Tier-2 reviewer against a labeled corpus (detection / FP / attribution).",
    )
    ev.add_argument(
        "--corpus",
        type=Path,
        default=Path("corpus"),
        help="Corpus directory containing labels.json. Default: ./corpus.",
    )
    ev.add_argument(
        "--fake",
        action="store_true",
        help="Offline baseline backend (always clean) — sanity-checks the harness.",
    )
    ev.add_argument(
        "--heuristic",
        action="store_true",
        help="Offline naive backend that fires on any tool-name mention (illustrates over-defense).",
    )
    ev.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")

    return parser


def _cmd_report(args: argparse.Namespace) -> int:
    findings, warnings = load_results_dir(args.results_dir)
    gate = Severity.parse(args.gate)
    report = build_report(findings, gate=gate, warnings=warnings)
    print(render(report, as_json=args.json))
    return 0 if report.passed else 1


def _cmd_ingest(args: argparse.Namespace) -> int:
    from datetime import datetime, timezone

    from airlock_scan.config import load_config
    from airlock_scan.database import build_index
    from airlock_scan.gate import decide
    from airlock_scan.report import build_report, render, render_markdown
    from airlock_scan.store import RunStore

    findings, warnings = load_results_dir(args.results_dir)
    gate = Severity.parse(args.gate)
    report = build_report(findings, gate=gate, warnings=warnings)
    decision = decide(findings, gate=gate)

    cfg = load_config()
    target = str((args.target or args.results_dir))
    store = RunStore.create(
        cfg.store_root,
        target=target,
        gate=args.gate,
        backend="tier1",
        model="",
        airlock_version=__version__,
    )
    store.write_report(static_findings=[f.as_dict() for f in findings])
    store.report_md_path.write_text(
        render_markdown(
            report,
            target=target,
            verdict_label=decision.verdict.label,
            generated=datetime.now(timezone.utc).isoformat(),
        ),
        encoding="utf-8",
    )
    build_index(store, store.index_db_path)

    print(render(report))
    print(f"\n{decision.summary_line()}")
    print(f"run:    {store.run_dir}")
    print(f"report: {store.report_md_path}")
    return 0 if decision.installable else 1


def _cmd_index(args: argparse.Namespace) -> int:
    from airlock_scan.database import rebuild_index

    if args.index_command == "rebuild":
        db_path = rebuild_index(args.run_dir)
        print(f"rebuilt {db_path}")
        return 0
    return 2


def _cmd_canary(args: argparse.Namespace) -> int:
    import json

    from airlock_scan.canary import attribute, build_canary_set

    if args.canary_command == "list":
        if args.harnesses:
            harnesses = tuple(args.harnesses)
        else:
            from airlock_scan.config import load_config

            harnesses = load_config().canary.harness_sets
        tools = build_canary_set(harnesses, include_agnostic=not args.no_agnostic)
        if args.json:
            print(json.dumps([t.__dict__ for t in tools], indent=2, default=list))
        else:
            for t in tools:
                print(f"{t.name:<22} {t.action_class:<9} {t.source:<18} {','.join(t.harnesses)}")
        return 0

    if args.canary_command == "attribute":
        attr = attribute(args.tool_name)
        if args.json:
            print(json.dumps(attr.__dict__, indent=2, default=list))
        else:
            print(f"tool:          {attr.tool}")
            print(f"action_class:  {attr.action_class}")
            print(f"specificity:   {attr.specificity}")
            print(f"fingerprints:  {attr.fingerprints or '-'}")
            print(f"exposed by:    {', '.join(attr.harnesses_exposing) or '-'}")
        return 0
    return 2


def _resolve_backend(cfg, fake: bool):
    """Build the Tier-2 backend, or print an error and return None."""
    import os

    from airlock_scan.llm_backend import FakeBackend, from_config

    if fake:
        return FakeBackend()
    api_key = os.environ.get(cfg.llm.api_key_env)
    if not api_key and cfg.llm.provider != "local":
        print(
            f"airlock-helper: error: no API key in ${cfg.llm.api_key_env}. "
            f"Set it, choose provider=local, or use --fake.",
            file=sys.stderr,
        )
        return None
    return from_config(cfg.llm, api_key=api_key)


def _file_cap_note(cfg) -> None:
    """Alert when the default file cap applies (each file is one LLM call)."""
    import os

    if "AIRLOCK_LLM_MAX_FILES" not in os.environ:
        print(
            f"note: reviewing at most {cfg.llm.max_files} file(s) this run "
            f"(default cap). Set AIRLOCK_LLM_MAX_FILES to review more.",
            file=sys.stderr,
        )


def _print_canary_lines(canary_events: list[dict]) -> None:
    for ev in canary_events:
        line = f"  ⚠ canary {ev.get('tool')} in {ev.get('file_path')}"
        if ev.get("harness"):
            line += f" (harness: {ev['harness']})"
        span = ev.get("localized_span")
        if span:
            line += f" — lines {span['start_line']}-{span['end_line']}"
        print(line)


def _cmd_quarantine(args: argparse.Namespace) -> int:
    from airlock_scan.canary import build_canary_set
    from airlock_scan.config import load_config
    from airlock_scan.database import build_index
    from airlock_scan.gate import decide
    from airlock_scan.quarantine import QuarantineReviewer, review_tree
    from airlock_scan.store import RunStore

    cfg = load_config()
    target = args.target.expanduser().resolve()
    if not target.is_dir():
        print(f"airlock-helper: error: not a directory: {target}", file=sys.stderr)
        return 2

    backend = _resolve_backend(cfg, args.fake)
    if backend is None:
        return 2
    _file_cap_note(cfg)

    canaries = build_canary_set(cfg.canary.harness_sets, include_agnostic=cfg.canary.agnostic_set)
    store = RunStore.create(
        cfg.store_root,
        target=str(target),
        gate=args.gate,
        backend=cfg.llm.provider,
        model=cfg.llm.effective_model,
        airlock_version=__version__,
    )
    reviewer = QuarantineReviewer(
        backend,
        canaries,
        store=store,
        max_file_bytes=cfg.llm.max_file_bytes,
        bisect_on_fire=cfg.canary.bisect_on_fire and not args.no_localize,
    )
    outcomes = review_tree(reviewer, target, max_files=cfg.llm.max_files)

    verdicts = [o.verdict.as_dict() for o in outcomes]
    store.write_report(file_verdicts=verdicts)
    build_index(store, store.index_db_path)

    canary_events = store.iter_canary_events()
    decision = decide(
        [],
        gate=Severity.parse(args.gate),
        canary_events=canary_events,
        file_verdicts=verdicts,
    )
    print(f"reviewed {len(outcomes)} file(s) → {store.run_dir}")
    print(decision.summary_line())
    for reason in decision.reasons:
        print(f"  - {reason}")
    _print_canary_lines(canary_events)
    return 0 if decision.installable else 1


def _cmd_vet(args: argparse.Namespace) -> int:
    """Unified run: merge Tier-1 scanner output + Tier-2 quarantine into one run."""
    from datetime import datetime, timezone

    from airlock_scan.canary import build_canary_set
    from airlock_scan.config import load_config
    from airlock_scan.database import build_index
    from airlock_scan.gate import decide
    from airlock_scan.quarantine import QuarantineReviewer, review_tree
    from airlock_scan.report import build_report, render_markdown
    from airlock_scan.store import RunStore

    cfg = load_config()
    target = args.target.expanduser().resolve()
    if not target.is_dir():
        print(f"airlock-helper: error: not a directory: {target}", file=sys.stderr)
        return 2

    # Tier-1: optional deterministic findings produced by the shell scanners.
    findings, warnings = ([], [])
    if args.tier1_results:
        findings, warnings = load_results_dir(args.tier1_results)

    backend = _resolve_backend(cfg, args.fake)
    if backend is None:
        return 2
    _file_cap_note(cfg)

    canaries = build_canary_set(cfg.canary.harness_sets, include_agnostic=cfg.canary.agnostic_set)
    store = RunStore.create(
        cfg.store_root,
        target=str(target),
        gate=args.gate,
        backend=cfg.llm.provider,
        model=cfg.llm.effective_model,
        airlock_version=__version__,
    )
    reviewer = QuarantineReviewer(
        backend,
        canaries,
        store=store,
        max_file_bytes=cfg.llm.max_file_bytes,
        bisect_on_fire=cfg.canary.bisect_on_fire and not args.no_localize,
    )
    outcomes = review_tree(reviewer, target, max_files=cfg.llm.max_files)
    verdicts = [o.verdict.as_dict() for o in outcomes]

    store.write_report(
        static_findings=[f.as_dict() for f in findings],
        file_verdicts=verdicts,
    )
    canary_events = store.iter_canary_events()
    gate = Severity.parse(args.gate)
    report = build_report(findings, gate=gate, warnings=warnings)
    decision = decide(findings, gate=gate, canary_events=canary_events, file_verdicts=verdicts)
    store.report_md_path.write_text(
        render_markdown(
            report,
            target=str(target),
            verdict_label=decision.verdict.label,
            generated=datetime.now(timezone.utc).isoformat(),
            file_verdicts=verdicts,
            canary_events=canary_events,
        ),
        encoding="utf-8",
    )
    build_index(store, store.index_db_path)

    print(f"vetted {target}")
    print(
        f"  Tier-1: {len(findings)} finding(s)   "
        f"Tier-2: {len(outcomes)} file(s), {len(canary_events)} canary fire(s)"
    )
    print(decision.summary_line())
    for reason in decision.reasons:
        print(f"  - {reason}")
    _print_canary_lines(canary_events)
    print(f"run:    {store.run_dir}")
    print(f"report: {store.report_md_path}")
    return 0 if decision.installable else 1


def _cmd_eval(args: argparse.Namespace) -> int:
    import json

    from airlock_scan.canary import build_canary_set
    from airlock_scan.config import load_config
    from airlock_scan.evaluate import (
        evaluate,
        heuristic_responder,
        load_corpus,
        render_eval_markdown,
    )
    from airlock_scan.llm_backend import FakeBackend
    from airlock_scan.quarantine import QuarantineReviewer

    cfg = load_config()
    root = args.corpus.expanduser().resolve()
    if not (root / "labels.json").is_file():
        print(f"airlock-helper: error: no labels.json in {root}", file=sys.stderr)
        return 2
    items = load_corpus(root)

    if args.heuristic:
        backend = FakeBackend(heuristic_responder)
    elif args.fake:
        backend = FakeBackend()
    else:
        backend = _resolve_backend(cfg, fake=False)
        if backend is None:
            return 2

    canaries = build_canary_set(cfg.canary.harness_sets, include_agnostic=cfg.canary.agnostic_set)
    reviewer = QuarantineReviewer(
        backend, canaries, store=None, max_file_bytes=cfg.llm.max_file_bytes, bisect_on_fire=False
    )
    report = evaluate(reviewer, items)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(render_eval_markdown(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            return _cmd_report(args)
        if args.command == "ingest":
            return _cmd_ingest(args)
        if args.command == "index":
            return _cmd_index(args)
        if args.command == "canary":
            return _cmd_canary(args)
        if args.command == "quarantine":
            return _cmd_quarantine(args)
        if args.command == "vet":
            return _cmd_vet(args)
        if args.command == "eval":
            return _cmd_eval(args)
    except Exception as exc:  # noqa: BLE001 - surface a clean error, never a traceback
        print(f"airlock-helper: error: {exc}", file=sys.stderr)
        return 3
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable; parser.error exits


if __name__ == "__main__":
    sys.exit(main())
