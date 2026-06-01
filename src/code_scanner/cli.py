"""Thin command-line entry point for the Python helper.

This is invoked by the shell layer, e.g. ``uv run cscan-helper report <dir> --gate high``.
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

from code_scanner import __version__
from code_scanner.findings import Severity
from code_scanner.parsers import load_results_dir
from code_scanner.report import build_report, render

_GATE_CHOICES = ["critical", "high", "medium", "low", "info"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cscan-helper",
        description="Parse, merge and gate scanner output for the cscan toolkit.",
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
        help="Directory containing scanner output (e.g. <target>/.cscan).",
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

    # index — manage the derived, rebuildable SQLite index over a run directory.
    index = sub.add_parser("index", help="Manage the derived SQLite index for a run.")
    index_sub = index.add_subparsers(dest="index_command", required=True)
    index_rebuild = index_sub.add_parser(
        "rebuild",
        help="Rebuild <run-dir>/index.db from the run's files alone.",
    )
    index_rebuild.add_argument("run_dir", type=Path, help="A cscan run directory.")

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

    return parser


def _cmd_report(args: argparse.Namespace) -> int:
    findings, warnings = load_results_dir(args.results_dir)
    gate = Severity.parse(args.gate)
    report = build_report(findings, gate=gate, warnings=warnings)
    print(render(report, as_json=args.json))
    return 0 if report.passed else 1


def _cmd_index(args: argparse.Namespace) -> int:
    from code_scanner.database import rebuild_index

    if args.index_command == "rebuild":
        db_path = rebuild_index(args.run_dir)
        print(f"rebuilt {db_path}")
        return 0
    return 2


def _cmd_canary(args: argparse.Namespace) -> int:
    import json

    from code_scanner.canary import attribute, build_canary_set

    if args.canary_command == "list":
        if args.harnesses:
            harnesses = tuple(args.harnesses)
        else:
            from code_scanner.config import load_config

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


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            return _cmd_report(args)
        if args.command == "index":
            return _cmd_index(args)
        if args.command == "canary":
            return _cmd_canary(args)
    except Exception as exc:  # noqa: BLE001 - surface a clean error, never a traceback
        print(f"cscan-helper: error: {exc}", file=sys.stderr)
        return 3
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable; parser.error exits


if __name__ == "__main__":
    sys.exit(main())
