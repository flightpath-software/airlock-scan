#!/usr/bin/env bash
# Scan a target repo/directory with the selected scanners, then apply the gate.
# Usage: scan.sh [<target>] [<scanner-id>...]
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
  target="$(ui_input "Path to the repo/dir to scan")"
fi
[ -n "$target" ] || die "no target provided"
target="$(cd "$target" 2>/dev/null && pwd)" || die "target not found: $target"

ui_header "airlock • scanning ${target}"

# Determine which scanners to run.
declare -a selected
if [ "$#" -gt 0 ]; then
  selected=("$@")
else
  mapfile -t selected < <(
    ui_choose_multi "Select scanners (space toggles, enter confirms)" \
      "${AIRLOCK_DEFAULT_SCANNERS[@]}" "${AIRLOCK_OPTIONAL_SCANNERS[@]}"
  )
  [ "${#selected[@]}" -gt 0 ] || selected=("${AIRLOCK_DEFAULT_SCANNERS[@]}")
fi

# Per-target results directory (travels with what you scanned; git-ignored).
out="${target}/${AIRLOCK_RESULTS_DIRNAME}"
mkdir -p "$out"
rm -f "$out"/*.sarif "$out"/*.json 2>/dev/null || true

for id in "${selected[@]}"; do
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

ui_header "airlock • report (gate: ${AIRLOCK_GATE})"
# Normalize the raw scanner output into a user-local ~/airlock run (report.json +
# readable report.md + queryable index), and apply the gate.
( cd "$ROOT" && uv run airlock-helper ingest "$out" --target "$target" --gate "$AIRLOCK_GATE" )
rc=$?

echo
if [ "$rc" -eq 0 ]; then
  log_ok "PASS — nothing at/above the '${AIRLOCK_GATE}' gate. Raw output: ${out}"
else
  log_err "FAIL — findings at/above '${AIRLOCK_GATE}'. Review before installing or exposing to an LLM."
fi
exit "$rc"
