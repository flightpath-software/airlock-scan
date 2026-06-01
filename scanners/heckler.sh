#!/usr/bin/env bash
# Adapter: heckler — invisible-unicode / trojan-source / Glassworm / tag-char
# prompt-injection detection (language-agnostic). Run via uvx.
# Contract: name | detect | install | run <target> <out_dir>
set -uo pipefail

ADAPTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${ADAPTER_DIR}/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

cmd="${1:-}"; shift || true

case "$cmd" in
  name)    echo "heckler — invisible-unicode / trojan-source / prompt-injection (uvx)";;
  detect)  have uvx;;
  install) ensure_uv; ui_spin "Warming heckler" -- uvx heckler --help >/dev/null 2>&1 || true;;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    out_file="${out}/heckler.sarif"
    args=(--format sarif)
    [ "${CSCAN_HECKLER_SCAN_DEPS:-0}" = "1" ] && args+=(--scan-deps)
    uvx heckler "${args[@]}" "$target" >"$out_file" 2>/dev/null || true
    [ -s "$out_file" ] && echo "$out_file"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
