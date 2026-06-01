#!/usr/bin/env bash
# Interactive gum main menu for cscan.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"

while true; do
  ui_header "cscan — repo security scanner"
  choice="$(ui_choose "What would you like to do?" \
    "Scan a repo" \
    "Install / check tools" \
    "Configure shell" \
    "Doctor (env + OSV audit)" \
    "Quit")"

  case "$choice" in
    "Scan a repo")              bash "${ROOT}/scripts/scan.sh" || true ;;
    "Install / check tools")    bash "${ROOT}/scripts/install-tools.sh" || true ;;
    "Configure shell")          bash "${ROOT}/scripts/shell-setup.sh" || true ;;
    "Doctor (env + OSV audit)") bash "${ROOT}/scripts/doctor.sh" || true ;;
    "Quit"|"")                  log_info "bye"; exit 0 ;;
    *)                          log_warn "unknown choice: ${choice}" ;;
  esac
  echo
done
