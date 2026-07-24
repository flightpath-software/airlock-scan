#!/usr/bin/env bash
# Adapter: osv-scanner — vulnerable dependency (CVE) scanning.
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
  name)    echo "osv-scanner — dependency vulnerabilities / CVEs (brew)";;
  detect)  have osv-scanner;;
  install) have osv-scanner && { log_ok "osv-scanner already installed"; exit 0; }; brew_install osv-scanner;;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    out_file="${out}/osv-scanner.sarif"
    # osv-scanner v2 uses `scan source`; v1 uses the bare invocation.
    if ! osv-scanner scan source --recursive --format sarif --output "$out_file" \
          "$target" >/dev/null 2>&1; then
      osv-scanner --format sarif --output "$out_file" -r "$target" >/dev/null 2>&1 || true
    fi
    [ -f "$out_file" ] && echo "$out_file"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
