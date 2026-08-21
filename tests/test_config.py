"""Tests for the [tool.airlock] configuration loader and its precedence."""

from __future__ import annotations

from pathlib import Path

import pytest

from airlock_scan.config import Config, ConfigError, LLMConfig, load_config


def test_defaults():
    cfg = Config()
    assert cfg.store_root == Path("~/airlock").expanduser()
    assert cfg.write_into_target is False
    assert cfg.llm.provider == "openai"
    assert cfg.llm.effective_base_url == "https://api.openai.com/v1"
    assert cfg.llm.max_files == 5  # conservative cost/safety cap by default
    assert cfg.persistence.ingested_bytes_ttl_days == 30
    assert "claude_code" in cfg.canary.harness_sets


def test_pyproject_overrides(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.airlock]
store_root = "/tmp/elsewhere"
write_into_target = true

[tool.airlock.llm]
provider = "openai"
max_files = 10

[tool.airlock.canary]
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
        "[tool.airlock.llm]\nprovider = \"openai\"\n", encoding="utf-8"
    )
    environ = {"AIRLOCK_LLM_PROVIDER": "local", "AIRLOCK_LLM_MAX_FILES": "7"}
    cfg = load_config(pyproject=pyproject, environ=environ)
    assert cfg.llm.provider == "local"
    assert cfg.llm.max_files == 7


def test_user_config_under_store_root(tmp_path):
    store_root = tmp_path / "store"
    store_root.mkdir()
    (store_root / "config.toml").write_text(
        "[llm]\nmodel = \"from-user-config\"\n", encoding="utf-8"
    )
    environ = {"AIRLOCK_STORE_ROOT": str(store_root)}
    cfg = load_config(pyproject=tmp_path / "nope.toml", environ=environ)
    assert cfg.store_root == store_root
    assert cfg.llm.model == "from-user-config"


def test_local_preset_switches_endpoint(tmp_path):
    cfg = load_config(
        pyproject=tmp_path / "nope.toml",
        environ={"AIRLOCK_LLM_PROVIDER": "local"},
    )
    assert cfg.llm.effective_base_url == cfg.llm.local_base_url
    assert cfg.llm.effective_model == cfg.llm.local_model


def test_unknown_keys_ignored(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.airlock]\nbogus_key = 1\n[tool.airlock.llm]\nalso_bogus = 2\nprovider = \"openai\"\n",
        encoding="utf-8",
    )
    cfg = load_config(pyproject=pyproject, environ={})
    assert cfg.llm.provider == "openai"


def test_api_key_env_accepts_valid_names():
    # The default and any real env-var name are accepted unchanged.
    assert LLMConfig().api_key_env == "OPENAI_API_KEY"
    assert LLMConfig(api_key_env="MY_CUSTOM_KEY_1").api_key_env == "MY_CUSTOM_KEY_1"
    assert LLMConfig(api_key_env="_secret").api_key_env == "_secret"


def test_api_key_env_rejects_non_identifier():
    # A value that isn't a valid env-var identifier — which a mis-pasted secret
    # would not be — must be rejected at load, before it can reach
    # os.environ.get() or the "no API key" error message. (Benign, low-entropy
    # literals here on purpose, so the fixture doesn't look like a real secret.)
    with pytest.raises(ConfigError):
        LLMConfig(api_key_env="not-an-identifier")  # '-' is not allowed


def test_api_key_env_error_does_not_echo_the_value():
    bad_value = "do-not-echo-this-value"
    with pytest.raises(ConfigError) as exc:
        LLMConfig(api_key_env=bad_value)
    assert bad_value not in str(exc.value)  # the offending value must not leak


def test_api_key_env_rejects_trailing_newline():
    # A `$` anchor would accept this: it also matches just before a final
    # newline. The value is used for the env lookup and printed by the CLI, so
    # the check has to be a whole-string one.
    with pytest.raises(ConfigError):
        LLMConfig(api_key_env="OPENAI_API_KEY\n")


def test_api_key_env_rejects_non_string():
    # TOML values aren't coerced on the way in (_coerce_section keeps them as
    # parsed), so a non-string must fail as a ConfigError the CLI can report —
    # not as a TypeError out of the regex.
    with pytest.raises(ConfigError):
        LLMConfig(api_key_env=123)


def test_pyproject_bad_api_key_env_is_rejected(tmp_path):
    # The [tool.airlock] path is validated too: _apply_table reconstructs
    # LLMConfig via replace() -> __post_init__.
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.airlock.llm]\napi_key_env = "not-a-name"\n', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(pyproject=pyproject, environ={})


def test_env_override_bad_api_key_env_is_rejected(tmp_path):
    # The AIRLOCK_LLM_API_KEY_ENV override path is validated too (reconstructs
    # LLMConfig via replace() -> __post_init__). Point at a missing pyproject so
    # the loader can't walk up to a real one outside the test.
    with pytest.raises(ConfigError):
        load_config(
            pyproject=tmp_path / "nope.toml",
            environ={"AIRLOCK_LLM_API_KEY_ENV": "bad-name-123"},
        )


def test_explicit_config_path_wins_over_cwd(tmp_path):
    cfgfile = tmp_path / "myconf.toml"
    cfgfile.write_text('[tool.airlock.llm]\nmodel = "custom-model"\n', encoding="utf-8")
    cfg = load_config(
        config_path=cfgfile,
        environ={"AIRLOCK_STORE_ROOT": str(tmp_path / "store")},
    )
    assert cfg.llm.model == "custom-model"


def test_airlock_config_env_is_honored(tmp_path):
    cfgfile = tmp_path / "envconf.toml"
    cfgfile.write_text('[tool.airlock.llm]\nmodel = "env-model"\n', encoding="utf-8")
    cfg = load_config(
        environ={"AIRLOCK_CONFIG": str(cfgfile), "AIRLOCK_STORE_ROOT": str(tmp_path / "store")},
    )
    assert cfg.llm.model == "env-model"


def test_config_explicitly_pointed_inside_target_is_refused(tmp_path, capsys):
    # Even an explicit --config path is refused if it lives inside the scanned
    # target, so an untrusted repo can't reconfigure the scanner (#45).
    target = tmp_path / "untrusted-repo"
    target.mkdir()
    (target / "pyproject.toml").write_text(
        '[tool.airlock.llm]\nmodel = "attacker-model"\n', encoding="utf-8"
    )
    cfg = load_config(
        config_path=target / "pyproject.toml",
        target=target,
        environ={"AIRLOCK_STORE_ROOT": str(tmp_path / "store")},
    )
    assert cfg.llm.model != "attacker-model"
    assert "refusing to read config from inside" in capsys.readouterr().err


def test_cwd_pyproject_inside_target_is_refused(tmp_path, monkeypatch):
    # Running from inside the target must not let its pyproject reconfigure us.
    target = tmp_path / "repo"
    target.mkdir()
    (target / "pyproject.toml").write_text(
        '[tool.airlock.llm]\nmodel = "attacker-model"\n', encoding="utf-8"
    )
    monkeypatch.chdir(target)
    cfg = load_config(target=target, environ={"AIRLOCK_STORE_ROOT": str(tmp_path / "store")})
    assert cfg.llm.model != "attacker-model"


def test_airlock_config_env_inside_target_is_refused(tmp_path, capsys):
    target = tmp_path / "repo"
    target.mkdir()
    (target / "cfg.toml").write_text(
        '[tool.airlock.llm]\nmodel = "attacker-model"\n', encoding="utf-8"
    )
    cfg = load_config(
        target=target,
        environ={
            "AIRLOCK_CONFIG": str(target / "cfg.toml"),
            "AIRLOCK_STORE_ROOT": str(tmp_path / "store"),
        },
    )
    assert cfg.llm.model != "attacker-model"
    assert "refusing to read config from inside" in capsys.readouterr().err


def test_symlink_inside_target_pointing_out_is_refused(tmp_path, capsys):
    # A symlink inside the target pointing at an outside config must not escape the
    # guard: resolve() would follow it outside, but the path is reachable via the
    # target, so it's refused (#45 hardening).
    outside = tmp_path / "outside.toml"
    outside.write_text('[tool.airlock.llm]\nmodel = "attacker-model"\n', encoding="utf-8")
    target = tmp_path / "repo"
    target.mkdir()
    link = target / "pyproject.toml"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        import pytest

        pytest.skip("symlinks not supported on this platform")
    cfg = load_config(
        config_path=link,
        target=target,
        environ={"AIRLOCK_STORE_ROOT": str(tmp_path / "store")},
    )
    assert cfg.llm.model != "attacker-model"
    assert "refusing to read config from inside" in capsys.readouterr().err


def test_explicit_config_path_is_expanduser(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "airlockcfg.toml").write_text(
        '[tool.airlock.llm]\nmodel = "home-model"\n', encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(home))
    cfg = load_config(
        config_path=Path("~/airlockcfg.toml"),
        environ={"AIRLOCK_STORE_ROOT": str(tmp_path / "store")},
    )
    assert cfg.llm.model == "home-model"
