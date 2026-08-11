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
