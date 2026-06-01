#!/usr/bin/env bash
# Adapter: gitleaks — secret / credential scanning.
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
  name)    echo "gitleaks — secrets / credential scanning (brew)";;
  detect)  have gitleaks;;
  install) have gitleaks && { log_ok "gitleaks already installed"; exit 0; }; brew_install gitleaks;;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    out_file="${out}/gitleaks.sarif"
    # Prefer the modern `gitleaks dir` (8.19+); fall back to `detect --no-git`.
    if ! gitleaks dir "$target" --report-format sarif --report-path "$out_file" \
          --exit-code 0 --no-banner >/dev/null 2>&1; then
      gitleaks detect --source "$target" --no-git --report-format sarif \
          --report-path "$out_file" --exit-code 0 --no-banner >/dev/null 2>&1 || true
    fi
    [ -f "$out_file" ] && echo "$out_file"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
