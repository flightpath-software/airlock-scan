# shellcheck shell=bash
# Shared helpers for the airlock shell layer.
# Source this file; it defines functions/vars and does not run anything on its own.

# Resolve the repo root from this library's location ($ROOT/scripts/lib/common.sh).
AIRLOCK_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIRLOCK_ROOT="$(cd "${AIRLOCK_LIB_DIR}/../.." && pwd)"
export AIRLOCK_ROOT

# --- capability checks -----------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }
have_gum() { have gum; }

# --- logging ---------------------------------------------------------------
_c_reset=$'\033[0m'; _c_red=$'\033[31m'; _c_grn=$'\033[32m'
_c_yel=$'\033[33m'; _c_blu=$'\033[34m'; _c_dim=$'\033[2m'

log_info() { printf '%s[*]%s %s\n' "$_c_blu" "$_c_reset" "$*" >&2; }
log_ok()   { printf '%s[+]%s %s\n' "$_c_grn" "$_c_reset" "$*" >&2; }
log_warn() { printf '%s[!]%s %s\n' "$_c_yel" "$_c_reset" "$*" >&2; }
log_err()  { printf '%s[x]%s %s\n' "$_c_red" "$_c_reset" "$*" >&2; }
die()      { log_err "$*"; exit 1; }

# --- gum-backed UI (graceful fallback when gum is absent) ------------------
ui_header() {
  local title="$1"
  if have_gum; then
    gum style --border rounded --margin "0 0" --padding "1 3" \
      --border-foreground 212 --foreground 212 "$title"
  else
    printf '\n%s== %s ==%s\n' "$_c_blu" "$title" "$_c_reset"
  fi
}

ui_note() {
  if have_gum; then gum style --foreground 244 "$*"; else printf '%s%s%s\n' "$_c_dim" "$*" "$_c_reset"; fi
}

# ui_choose <header> <option>...   -> echoes the chosen option (single select)
ui_choose() {
  local header="$1"; shift
  if have_gum; then
    gum choose --header "$header" "$@"
  else
    printf '%s\n' "$header" >&2
    local opt
    select opt in "$@"; do
      [ -n "${opt:-}" ] && { printf '%s\n' "$opt"; return 0; }
    done
  fi
}

# ui_choose_multi <header> <option>...  -> echoes chosen options, one per line
ui_choose_multi() {
  local header="$1"; shift
  if have_gum; then
    gum choose --no-limit --header "$header" "$@"
  else
    log_warn "gum not installed; selecting all options by default"
    printf '%s\n' "$@"
  fi
}

# ui_confirm <prompt>  -> returns 0 (yes) / 1 (no)
ui_confirm() {
  if have_gum; then
    gum confirm "$1"
  else
    local ans
    read -r -p "$1 [y/N] " ans
    [[ "${ans:-}" =~ ^[Yy]$ ]]
  fi
}

# ui_input <placeholder>  -> echoes entered text
ui_input() {
  if have_gum; then
    gum input --placeholder "$1"
  else
    local v
    read -r -p "$1: " v
    printf '%s\n' "$v"
  fi
}

# ui_spin <title> -- <cmd...>   runs cmd, showing a spinner when gum is present
ui_spin() {
  local title="$1"; shift
  [ "${1:-}" = "--" ] && shift
  if have_gum; then
    gum spin --spinner dot --title "$title" -- "$@"
  else
    log_info "$title"
    "$@"
  fi
}
