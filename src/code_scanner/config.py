"""Configuration for the cscan vetting pipeline (the ``[tool.cscan]`` surface).

Resolution precedence (later wins):

1. Built-in defaults (see :class:`Config`).
2. ``[tool.cscan]`` in a project ``pyproject.toml`` (repo-level defaults).
3. A user config file at ``<store_root>/config.toml`` (machine-wide prefs).
4. Environment overrides (``CSCAN_*``).

The store root defaults to ``~/cscan`` — deliberately *not* a dotdir, so a user
can find reports easily when something fires. Nothing here reads the target
repo; this only configures where output goes and how the LLM tier behaves.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields, replace
from pathlib import Path

DEFAULT_STORE_ROOT = "~/cscan"

# Harness ids registered as canary decoy sets by default (see data/harness_signatures.*).
_DEFAULT_HARNESS_SETS = (
    "claude_code",
    "codex_cli",
    "gemini_cli",
    "cursor",
    "opencode",
    "zed",
    "cline",
    "warp",
)


@dataclass(frozen=True, slots=True)
class PersistenceConfig:
    """Files are the portable source of truth; SQLite is a derived index."""

    files_are_source_of_truth: bool = True
    sqlite_index: bool = True
    ingested_bytes_ttl_days: int = 30


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """Tier-2 reviewer backend.

    We speak the **OpenAI-compatible** Chat Completions API, so a single client
    reaches OpenAI, DeepInfra, OpenRouter, Together, Groq, Fireworks, and local
    servers (Ollama ``/v1``, vLLM, llama.cpp) — the only difference is
    ``base_url`` + ``model`` + which env var holds the key. Cloud is the default
    because canary tripwires need reliable tool-calling.
    """

    provider: str = "openai"  # label only; base_url drives the actual endpoint
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    api_key_env: str = "OPENAI_API_KEY"  # name of the env var holding the API key
    # Used by the "local" preset (an OpenAI-compatible local server, e.g. Ollama).
    local_base_url: str = "http://localhost:11434/v1"
    local_model: str = "qwen2.5-coder"
    redact_tier1_secrets: bool = True
    temperature: float = 0.0
    request_timeout: int = 60
    max_file_bytes: int = 200_000  # skip/chunk files larger than this
    max_files: int = 400
    gate_only_on_suspicious: bool = True

    @property
    def effective_base_url(self) -> str:
        """The endpoint to use, applying the ``local`` preset when selected."""
        if self.provider == "local":
            return self.local_base_url
        return self.base_url

    @property
    def effective_model(self) -> str:
        return self.local_model if self.provider == "local" else self.model


@dataclass(frozen=True, slots=True)
class CanaryConfig:
    """Decoy tripwire sets offered to the quarantined reviewer."""

    harness_sets: tuple[str, ...] = _DEFAULT_HARNESS_SETS
    agnostic_set: bool = True
    bisect_on_fire: bool = True


@dataclass(frozen=True, slots=True)
class Config:
    """Top-level cscan configuration."""

    store_root: Path = field(default_factory=lambda: Path(DEFAULT_STORE_ROOT).expanduser())
    write_into_target: bool = False
    export_requires_optin: bool = True
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    canary: CanaryConfig = field(default_factory=CanaryConfig)


# --- loading ---------------------------------------------------------------

_SECTION_TYPES = {
    "persistence": PersistenceConfig,
    "llm": LLMConfig,
    "canary": CanaryConfig,
}


def _coerce_section(section_cls: type, raw: dict) -> dict:
    """Keep only known keys; coerce tuple-typed list values. Unknown keys ignored."""
    known = {f.name for f in fields(section_cls)}
    out: dict = {}
    for key, value in raw.items():
        if key not in known:
            continue
        out[key] = tuple(value) if isinstance(value, list) else value
    return out


def _apply_table(cfg: Config, table: dict) -> Config:
    """Apply a ``[tool.cscan]`` table (already extracted) onto ``cfg``."""
    top: dict = {}
    if "store_root" in table:
        top["store_root"] = Path(str(table["store_root"])).expanduser()
    if "write_into_target" in table:
        top["write_into_target"] = bool(table["write_into_target"])
    if "export_requires_optin" in table:
        top["export_requires_optin"] = bool(table["export_requires_optin"])

    for name, section_cls in _SECTION_TYPES.items():
        sub = table.get(name)
        if isinstance(sub, dict):
            current = getattr(cfg, name)
            top[name] = replace(current, **_coerce_section(section_cls, sub))

    return replace(cfg, **top)


def _read_cscan_table(toml_path: Path) -> dict:
    """Return the ``[tool.cscan]`` table from a pyproject-style file, or {}."""
    try:
        with toml_path.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return (data.get("tool", {}) or {}).get("cscan", {}) or {}


def _read_user_config(toml_path: Path) -> dict:
    """User config file: a bare cscan table (no [tool.cscan] nesting required)."""
    try:
        with toml_path.open("rb") as fh:
            data = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    # Accept either a top-level table or a nested [tool.cscan] for convenience.
    nested = (data.get("tool", {}) or {}).get("cscan")
    return nested if isinstance(nested, dict) else data


# Flat env overrides → (section or None, attribute, caster).
_ENV_MAP: dict[str, tuple[str | None, str, type]] = {
    "CSCAN_STORE_ROOT": (None, "store_root", Path),
    "CSCAN_WRITE_INTO_TARGET": (None, "write_into_target", bool),
    "CSCAN_LLM_PROVIDER": ("llm", "provider", str),
    "CSCAN_LLM_BASE_URL": ("llm", "base_url", str),
    "CSCAN_LLM_MODEL": ("llm", "model", str),
    "CSCAN_LLM_API_KEY_ENV": ("llm", "api_key_env", str),
    "CSCAN_LLM_LOCAL_MODEL": ("llm", "local_model", str),
    "CSCAN_LLM_MAX_FILES": ("llm", "max_files", int),
}


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _apply_env(cfg: Config, environ: dict[str, str]) -> Config:
    top: dict = {}
    section_updates: dict[str, dict] = {}
    for env_key, (section, attr, caster) in _ENV_MAP.items():
        if env_key not in environ:
            continue
        raw = environ[env_key]
        if caster is bool:
            value: object = _as_bool(raw)
        elif caster is Path:
            value = Path(raw).expanduser()
        else:
            value = caster(raw)
        if section is None:
            top[attr] = value
        else:
            section_updates.setdefault(section, {})[attr] = value

    for name, updates in section_updates.items():
        top[name] = replace(getattr(cfg, name), **updates)
    return replace(cfg, **top)


def load_config(
    *,
    pyproject: Path | None = None,
    environ: dict[str, str] | None = None,
) -> Config:
    """Resolve configuration across all four sources (see module docstring)."""
    environ = os.environ if environ is None else environ
    cfg = Config()

    # 2. pyproject [tool.cscan]
    pyproject = pyproject or _find_pyproject(Path.cwd())
    if pyproject and pyproject.is_file():
        cfg = _apply_table(cfg, _read_cscan_table(pyproject))

    # Determine store_root early so the user config path can depend on it,
    # honoring an env override of the store root before reading the user file.
    store_root = cfg.store_root
    if "CSCAN_STORE_ROOT" in environ:
        store_root = Path(environ["CSCAN_STORE_ROOT"]).expanduser()

    # 3. user config at <store_root>/config.toml
    user_cfg = store_root / "config.toml"
    if user_cfg.is_file():
        cfg = _apply_table(cfg, _read_user_config(user_cfg))

    # 4. environment overrides
    cfg = _apply_env(cfg, environ)
    return cfg


def _find_pyproject(start: Path) -> Path | None:
    """Walk up from ``start`` looking for a pyproject.toml."""
    for directory in (start, *start.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None
