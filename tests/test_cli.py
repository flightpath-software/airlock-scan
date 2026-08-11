"""Tests for CLI helper functions."""

from __future__ import annotations

from airlock_scan.cli import _resolve_backend
from airlock_scan.config import Config, LLMConfig


def test_no_api_key_error_never_echoes_configured_value(capsys, monkeypatch):
    # An identifier-shaped secret mistakenly pasted into api_key_env passes config
    # validation (#25 only rejects non-identifier shapes), so the "no API key"
    # diagnostic must not print the configured value, whatever its shape (#41).
    secret = "sk_live_" + "A" * 24  # a valid identifier, but a secret shape
    monkeypatch.delenv(secret, raising=False)
    cfg = Config(llm=LLMConfig(api_key_env=secret, provider="openai"))

    result = _resolve_backend(cfg, fake=False)

    assert result is None
    err = capsys.readouterr().err
    assert secret not in err
    assert "no api key" in err.lower()


def test_no_api_key_message_states_the_default_env_name(capsys, monkeypatch):
    # The message states the built-in default var name (a public constant) as a
    # plain literal — helpful, and safe because it never interpolates the
    # configured value (#41). A literal is also not a CodeQL taint source.
    from airlock_scan.cli import _resolve_backend
    from airlock_scan.config import DEFAULT_API_KEY_ENV, Config, LLMConfig

    monkeypatch.delenv(DEFAULT_API_KEY_ENV, raising=False)
    cfg = Config(llm=LLMConfig(provider="openai"))  # default api_key_env
    assert _resolve_backend(cfg, fake=False) is None
    assert DEFAULT_API_KEY_ENV in capsys.readouterr().err


def test_truncation_note_lists_only_partially_reviewed_files(capsys):
    from airlock_scan.cli import _print_truncation_note

    _print_truncation_note(
        [{"file_path": "big.py", "truncated": True},
         {"file_path": "ok.py", "truncated": False}]
    )
    out = capsys.readouterr().out
    assert "partially reviewed" in out
    assert "big.py" in out
    assert "ok.py" not in out


def test_truncation_note_silent_when_nothing_truncated(capsys):
    from airlock_scan.cli import _print_truncation_note

    _print_truncation_note([{"file_path": "ok.py", "truncated": False}])
    assert capsys.readouterr().out == ""
