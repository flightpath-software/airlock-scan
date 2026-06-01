#!/usr/bin/env bash
# Adapter: guarddog — malicious PyPI/npm package heuristics. Run via uvx.
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

# verify_manifest <ecosystem> <manifest_path> <out_file>
verify_manifest() {
  local eco="$1" manifest="$2" out_file="$3"
  [ -f "$manifest" ] || return 0
  uvx guarddog "$eco" verify --output-format=sarif "$manifest" >"$out_file" 2>/dev/null || true
  [ -s "$out_file" ] && echo "$out_file"
}

case "$cmd" in
  name)    echo "guarddog — malicious PyPI/npm package detection (uvx)";;
  detect)  have uvx;;
  install) ensure_uv; ui_spin "Warming guarddog" -- uvx guarddog --help >/dev/null 2>&1 || true;;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    found=0
    # PyPI manifests
    for req in "$target"/requirements*.txt; do
      [ -f "$req" ] || continue
      verify_manifest pypi "$req" "${out}/guarddog-pypi.sarif" && found=1
      break
    done
    # npm manifest
    if [ -f "$target/package.json" ]; then
      verify_manifest npm "$target/package.json" "${out}/guarddog-npm.sarif" && found=1
    fi
    [ "$found" -eq 0 ] && log_warn "guarddog: no requirements*.txt or package.json found in target — skipped"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
