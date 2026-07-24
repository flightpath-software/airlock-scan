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
    "Vet a repo (Tier-1 + Tier-2)" \
    "Scan a repo (Tier-1 only)" \
    "Quarantine review (Tier-2 only)" \
    "Evaluate against corpus" \
    "Install / check tools" \
    "Configure shell" \
    "Doctor (env + OSV audit)" \
    "Add changelog entry" \
    "Cut a release" \
    "Quit")"

  case "$choice" in
    "Vet a repo (Tier-1 + Tier-2)") bash "${ROOT}/scripts/vet.sh" || true ;;
    "Scan a repo (Tier-1 only)")    bash "${ROOT}/scripts/scan.sh" || true ;;
    "Quarantine review (Tier-2 only)")
        t="$(ui_input "Path to the repo/dir to review")"
        [ -n "$t" ] && ( cd "$ROOT" && uv run cscan-helper quarantine "$t" ) || true ;;
    "Evaluate against corpus")  ( cd "$ROOT" && uv run cscan-helper eval ) || true ;;
    "Install / check tools")    bash "${ROOT}/scripts/install-tools.sh" || true ;;
    "Configure shell")          bash "${ROOT}/scripts/shell-setup.sh" || true ;;
    "Doctor (env + OSV audit)") bash "${ROOT}/scripts/doctor.sh" || true ;;
    "Add changelog entry")      bash "${ROOT}/scripts/changelog.sh" || true ;;
    "Cut a release")            bash "${ROOT}/scripts/release.sh" || true ;;
    "Quit"|"")                  log_info "bye"; exit 0 ;;
    *)                          log_warn "unknown choice: ${choice}" ;;
  esac
  echo
done
