#!/usr/bin/env bash
# Detect each scanner and offer to install the missing ones.
# Usage: install-tools.sh [--yes]   (--yes installs missing tools without prompting)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

assume_yes=0
[ "${1:-}" = "--yes" ] && assume_yes=1

ui_header "airlock • install / check scanners"

for id in "${AIRLOCK_DEFAULT_SCANNERS[@]}" "${AIRLOCK_OPTIONAL_SCANNERS[@]}"; do
  adapter="$(scanner_adapter "$id")"
  [ -f "$adapter" ] || { log_warn "no adapter for ${id}"; continue; }
  name="$(bash "$adapter" name 2>/dev/null || echo "$id")"

  if bash "$adapter" detect >/dev/null 2>&1; then
    log_ok "present : ${name}"
    continue
  fi

  log_warn "missing : ${name}"
  if [ "$assume_yes" -eq 1 ] || ui_confirm "Install ${id} now?"; then
    if bash "$adapter" install; then
      log_ok "installed ${id}"
    else
      log_err "failed to install ${id}"
    fi
  fi
done

log_info "Tip: run 'airlock doctor' for an environment + OSV supply-chain audit."
