"""Shared pytest support for tests that shell out to external tools."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _default_exclude_newer() -> str:
    """This repo's own supply-chain cooldown (pyproject.toml is the one source of truth)."""
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["tool"]["uv"]["exclude-newer"]


def uv_subprocess_env() -> dict[str, str]:
    """Environment for a subprocess that invokes `uvx` directly from Python.

    `scripts/lib/config.sh` exports `UV_EXCLUDE_NEWER` for scanners run through the
    real shell adapters (e.g. `scanners/semgrep.sh`), applying this repo's 3-day
    supply-chain cooldown to every `uvx`-run tool. Tests that call `uvx` via
    `subprocess.run` bypass that script entirely and never inherit the cooldown —
    confirmed the hard way when a freshly published, Windows-broken Semgrep release
    took down the whole suite with an unrelated-looking "semgrep-core.exe not
    found" error, something the cooldown exists specifically to prevent.

    Mirrors config.sh's own default-if-unset behavior: an already-set
    `UV_EXCLUDE_NEWER` is left alone, otherwise it falls back to pyproject.toml's
    own `[tool.uv] exclude-newer` value, so there's one source of truth for the
    cooldown period rather than a second hardcoded copy.
    """
    env = dict(os.environ)
    env.setdefault("UV_EXCLUDE_NEWER", _default_exclude_newer())
    return env
