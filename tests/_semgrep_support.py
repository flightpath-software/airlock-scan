"""Shared support for the tests that run the real Semgrep over fixtures/semgrep/.

test_semgrep_taint_live.py (does the pack fire where labels.json says it should?) and
test_semgrep_pattern_coverage.py (does every declared pattern appear in a fixture?) shell
out to `uvx semgrep` the same way, so the invocation, the cooldown environment and the
path matching live here once.

Imported by plain name (`from _semgrep_support import ...`), which works because pytest
puts tests/ on sys.path for test modules. It is a helper module rather than part of
conftest.py because pytest loads conftest.py itself, as a plugin, and test modules
aren't meant to import it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RULES_DIR = ROOT / "config" / "semgrep"
FIXTURES_DIR = ROOT / "fixtures" / "semgrep"
LABELS_FILE = FIXTURES_DIR / "labels.json"

# Skips a test that runs Semgrep when `uvx` isn't on PATH (e.g. a machine without uv
# installed) so the rest of the suite is unaffected; CI has uv/uvx available via
# astral-sh/setup-uv and runs them for real.
requires_uvx = pytest.mark.skipif(
    shutil.which("uvx") is None,
    reason="uvx not on PATH; skipping live Semgrep tests",
)


def load_labels() -> list[dict]:
    return json.loads(LABELS_FILE.read_text(encoding="utf-8"))["items"]


def matches_path(reported: str, rel_path: str) -> bool:
    """Whether a file path Semgrep reported is the labels.json-relative `rel_path`.

    SARIF artifact URIs may be relative to the scan target or to the invocation cwd (and
    use backslashes on Windows) depending on semgrep version/platform, so match on the
    normalized suffix rather than requiring exact equality. The leading "/" stops
    `xpython/a.py` from matching `python/a.py`.
    """
    reported = reported.replace("\\", "/")
    target = Path(rel_path).as_posix()
    return reported == target or reported.endswith("/" + target)


def _default_exclude_newer() -> str:
    """This repo's own supply-chain cooldown (pyproject.toml is the one source of truth)."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["tool"]["uv"]["exclude-newer"]


def uv_subprocess_env() -> dict[str, str]:
    """Environment for a subprocess that invokes `uvx` directly from Python.

    `scripts/lib/config.sh` exports `UV_EXCLUDE_NEWER` for scanners run through the
    real shell adapters (e.g. `scanners/semgrep.sh`), applying this repo's 3-day
    supply-chain cooldown to every `uvx`-run tool. Tests that call `uvx` via
    `subprocess.run` bypass that script entirely and never inherit the cooldown -
    confirmed the hard way when a freshly published, Windows-broken Semgrep release took
    the whole suite down with an unrelated-looking "semgrep-core.exe not found" error,
    something the cooldown exists specifically to prevent.

    Mirrors config.sh's own default-if-unset behavior: an already-set
    `UV_EXCLUDE_NEWER` is left alone, otherwise it falls back to pyproject.toml's
    own `[tool.uv] exclude-newer` value, so there's one source of truth for the
    cooldown period rather than a second hardcoded copy.
    """
    env = dict(os.environ)
    env.setdefault("UV_EXCLUDE_NEWER", _default_exclude_newer())
    return env


def run_semgrep_over_fixtures(config: Path, out_file: Path) -> dict:
    """Run `uvx semgrep scan --config <config>` over fixtures/semgrep/; return the SARIF.

    SARIF is the format production's own `parse_sarif` expects.
    """
    result = subprocess.run(
        [
            "uvx",
            "semgrep",
            "scan",
            "--config",
            str(config),
            "--sarif",
            "--output",
            str(out_file),
            "--quiet",
            "--disable-version-check",
            # Unlike scanners/semgrep.sh (which scans real, checked-out target
            # repos), Semgrep's default --use-git-ignore mode restricts
            # scanning to git-tracked files. A freshly added fixture that
            # hasn't been `git add`-ed yet would then silently score 0
            # findings and look like a broken rule. Fixture validation must
            # not depend on git index state.
            "--no-git-ignore",
            # Semgrep's default --rewrite-rule-ids prefixes each rule id with
            # its --config directory path (e.g. "config.semgrep.airlock-...").
            # Nothing downstream in airlock_scan relies on that prefix (the
            # gate keys off SARIF severity, not rule id), so disable it here
            # to keep the ids in the results matching the ones we asked for.
            "--no-rewrite-rule-ids",
            str(FIXTURES_DIR),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        env=uv_subprocess_env(),
    )
    if not out_file.exists():
        pytest.fail(
            f"semgrep produced no SARIF output (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return json.loads(out_file.read_text(encoding="utf-8"))
