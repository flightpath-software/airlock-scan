#!/usr/bin/env bash
# Adapter: anti-trojan-source (OPTIONAL) — trojan-source / confusable unicode.
# npm/Node tool, run via npx; off by default. Provides a second opinion to heckler.
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
  name)    echo "anti-trojan-source — trojan-source / confusable unicode (npx, optional)";;
  detect)  have npx;;
  install) ensure_node; log_info "anti-trojan-source is fetched on demand via npx (nothing to install)";;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    out_file="${out}/anti-trojan-source.json"
    # Emits a JSON array; the helper's parser understands this shape.
    npx --yes anti-trojan-source --files="${target}/**/*" --json >"$out_file" 2>/dev/null || true
    [ -s "$out_file" ] && echo "$out_file"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
