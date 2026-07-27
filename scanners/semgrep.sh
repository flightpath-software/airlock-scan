#!/usr/bin/env bash
# Adapter: semgrep — SAST / pattern rules. Run ephemerally via uvx.
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
  name)    echo "semgrep — SAST / pattern rules (uvx)";;
  detect)  have uvx;;          # fetched on demand by uvx; only uv is required
  install) ensure_uv; ui_spin "Warming semgrep" -- uvx semgrep --version >/dev/null 2>&1 || true;;
  run)
    target="${1:?run requires <target>}"; out="${2:?run requires <out_dir>}"
    out_file="${out}/semgrep.sarif"
    # Always run airlock's bundled taint pack; add the auto registry on top when
    # reachable. The custom rules are the deterministic, self-contained core and
    # must never be dropped just because a local dir exists.
    local_rules="${AIRLOCK_CONFIG_DIR}/semgrep"
    config_arg=(--config auto)
    if compgen -G "${local_rules}/*.y*ml" >/dev/null 2>&1; then
      config_arg+=(--config "$local_rules")
    fi
    # semgrep exits non-zero when findings exist; the gate is applied later.
    uvx semgrep scan "${config_arg[@]}" --sarif --output "$out_file" \
        --quiet --disable-version-check "$target" >/dev/null 2>&1 || true
    [ -f "$out_file" ] && echo "$out_file"
    ;;
  *) echo "usage: $0 {name|detect|install|run <target> <out_dir>}" >&2; exit 2;;
esac
