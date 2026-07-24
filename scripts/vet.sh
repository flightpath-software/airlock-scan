#!/usr/bin/env bash
# Unified vet: run the deterministic Tier-1 scanners, then the Tier-2 quarantined
# LLM reviewer, and merge both into a SINGLE user-local ~/cscan run + report.
# Usage: vet.sh [<target>] [extra cscan-helper vet args, e.g. --fake]
#
# Tier-2 needs OPENAI_API_KEY (or CSCAN_LLM_PROVIDER=local), or pass --fake.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

target="${1:-}"
[ "$#" -gt 0 ] && shift || true

if [ -z "$target" ]; then
  target="$(ui_input "Path to the repo/dir to vet")"
fi
[ -n "$target" ] || die "no target provided"
target="$(cd "$target" 2>/dev/null && pwd)" || die "target not found: $target"

ui_header "cscan • vetting ${target} (Tier-1 + Tier-2)"

# Per-target raw scanner output (git-ignored; travels with what you scanned).
out="${target}/${CSCAN_RESULTS_DIRNAME}"
mkdir -p "$out"
rm -f "$out"/*.sarif "$out"/*.json 2>/dev/null || true

# --- Tier 1: deterministic scanners ---------------------------------------
for id in "${CSCAN_DEFAULT_SCANNERS[@]}"; do
  adapter="$(scanner_adapter "$id")"
  if [ ! -f "$adapter" ]; then
    log_warn "unknown scanner '${id}' — skipping"
    continue
  fi
  if ! bash "$adapter" detect >/dev/null 2>&1; then
    log_warn "${id} not installed — skipping (use 'cscan install' to add it)"
    continue
  fi
  ui_spin "Running ${id}" -- bash "$adapter" run "$target" "$out"
  log_ok "${id} done"
done

# --- Tier 2 + merge: quarantined reviewer into the same ~/cscan run -------
ui_header "cscan • vet report (gate: ${CSCAN_GATE})"
( cd "$ROOT" && uv run cscan-helper vet "$target" --tier1-results "$out" --gate "$CSCAN_GATE" "$@" )
rc=$?

echo
if [ "$rc" -eq 0 ]; then
  log_ok "PASS — nothing at/above the '${CSCAN_GATE}' gate. Review the report under ~/cscan/."
else
  log_err "FAIL — findings at/above '${CSCAN_GATE}', or a canary fired. Review before installing."
fi
exit "$rc"
