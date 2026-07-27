#!/usr/bin/env bash
# Unified vet: run the deterministic Tier-1 scanners, then the Tier-2 quarantined
# LLM reviewer, and merge both into a SINGLE user-local ~/airlock run + report.
# Usage: vet.sh [<target>] [extra airlock-helper vet args, e.g. --fake]
#
# Tier-2 needs OPENAI_API_KEY (or AIRLOCK_LLM_PROVIDER=local), or pass --fake.
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

ui_header "airlock • vetting ${target} (Tier-1 + Tier-2)"

# Per-target raw scanner output (git-ignored; travels with what you scanned).
out="${target}/${AIRLOCK_RESULTS_DIRNAME}"
mkdir -p "$out"
rm -f "$out"/*.sarif "$out"/*.json 2>/dev/null || true

# --- Tier 1: deterministic scanners ---------------------------------------
for id in "${AIRLOCK_DEFAULT_SCANNERS[@]}"; do
  adapter="$(scanner_adapter "$id")"
  if [ ! -f "$adapter" ]; then
    log_warn "unknown scanner '${id}' — skipping"
    continue
  fi
  if ! bash "$adapter" detect >/dev/null 2>&1; then
    log_warn "${id} not installed — skipping (use 'airlock install' to add it)"
    continue
  fi
  ui_spin "Running ${id}" -- bash "$adapter" run "$target" "$out"
  log_ok "${id} done"
done

# --- Tier 2 + merge: quarantined reviewer into the same ~/airlock run -------
ui_header "airlock • vet report (gate: ${AIRLOCK_GATE})"
( cd "$ROOT" && uv run airlock-helper vet "$target" --tier1-results "$out" --gate "$AIRLOCK_GATE" "$@" )
rc=$?

echo
if [ "$rc" -eq 0 ]; then
  log_ok "PASS — nothing at/above the '${AIRLOCK_GATE}' gate. Review the report under ~/airlock/."
else
  log_err "FAIL — findings at/above '${AIRLOCK_GATE}', or a canary fired. Review before installing."
fi
exit "$rc"
