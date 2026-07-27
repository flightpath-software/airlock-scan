"""Ensure the packaged JSON dataset stays in sync with the human-facing YAML.

The YAML at ``data/harness_signatures.yaml`` is the source of truth that humans
edit; the packaged ``src/airlock_scan/data/harness_signatures.json`` is the
machine form loaded at runtime (stdlib json — no PyYAML at runtime). This test
regenerates the expected JSON from the YAML and compares. It is skipped when
PyYAML is unavailable, so it never adds a runtime dependency.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from airlock_scan.canary import load_signatures

yaml = pytest.importorskip("yaml")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_YAML = _REPO_ROOT / "data" / "harness_signatures.yaml"


def test_packaged_json_matches_yaml():
    if not _YAML.is_file():
        pytest.skip("source YAML not present in this checkout")
    expected = yaml.safe_load(_YAML.read_text(encoding="utf-8"))
    assert load_signatures() == expected
