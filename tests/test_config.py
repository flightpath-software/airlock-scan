"""Tests for the [tool.cscan] configuration loader and its precedence."""

from __future__ import annotations

from pathlib import Path

from code_scanner.config import Config, load_config


def test_defaults():
    cfg = Config()
    assert cfg.store_root == Path("~/cscan").expanduser()
    assert cfg.write_into_target is False
    assert cfg.llm.provider == "openai"
    assert cfg.llm.effective_base_url == "https://api.openai.com/v1"
    assert cfg.persistence.ingested_bytes_ttl_days == 30
    assert "claude_code" in cfg.canary.harness_sets


def test_pyproject_overrides(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.cscan]
store_root = "/tmp/elsewhere"
write_into_target = true

[tool.cscan.llm]
provider = "openai"
max_files = 10

[tool.cscan.canary]
harness_sets = ["cursor", "codex_cli"]
agnostic_set = false
""",
        encoding="utf-8",
    )
    cfg = load_config(pyproject=pyproject, environ={})
    assert cfg.store_root == Path("/tmp/elsewhere")
    assert cfg.write_into_target is True
    assert cfg.llm.provider == "openai"
    assert cfg.llm.max_files == 10
    # untouched fields keep their defaults
    assert cfg.llm.redact_tier1_secrets is True
    assert cfg.canary.harness_sets == ("cursor", "codex_cli")
    assert cfg.canary.agnostic_set is False


def test_env_overrides_win_over_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.cscan.llm]\nprovider = \"openai\"\n", encoding="utf-8"
    )
    environ = {"CSCAN_LLM_PROVIDER": "local", "CSCAN_LLM_MAX_FILES": "7"}
    cfg = load_config(pyproject=pyproject, environ=environ)
    assert cfg.llm.provider == "local"
    assert cfg.llm.max_files == 7


def test_user_config_under_store_root(tmp_path):
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "config.toml").write_text(
        "[llm]\nmodel = \"from-user-config\"\n", encoding="utf-8"
    )
    environ = {"CSCAN_STORE_ROOT": str(store_root)}
    cfg = load_config(pyproject=tmp_path / "nope.toml", environ=environ)
    assert cfg.store_root == store_root
    assert cfg.llm.model == "from-user-config"


def test_local_preset_switches_endpoint(tmp_path):
    cfg = load_config(
        pyproject=tmp_path / "nope.toml",
        environ={"CSCAN_LLM_PROVIDER": "local"},
    )
    assert cfg.llm.effective_base_url == cfg.llm.local_base_url
    assert cfg.llm.effective_model == cfg.llm.local_model


def test_unknown_keys_ignored(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.cscan]\nbogus_key = 1\n[tool.cscan.llm]\nalso_bogus = 2\nprovider = \"openai\"\n",
        encoding="utf-8",
    )
    cfg = load_config(pyproject=pyproject, environ={})
    assert cfg.llm.provider == "openai"
