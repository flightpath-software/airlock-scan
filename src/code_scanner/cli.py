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
    return parser


def _cmd_report(args: argparse.Namespace) -> int:
    findings, warnings = load_results_dir(args.results_dir)
    gate = Severity.parse(args.gate)
    report = build_report(findings, gate=gate, warnings=warnings)
    print(render(report, as_json=args.json))
    return 0 if report.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            return _cmd_report(args)
    except Exception as exc:  # noqa: BLE001 - surface a clean error, never a traceback
        print(f"cscan-helper: error: {exc}", file=sys.stderr)
        return 3
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable; parser.error exits


if __name__ == "__main__":
    sys.exit(main())
