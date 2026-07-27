#!/usr/bin/env bash
# gum-driven changelog helper: create a towncrier news fragment, or preview the
# draft changelog.
# Usage:
#   changelog.sh [new]      interactively create a news fragment (default)
#   changelog.sh preview    render the unreleased changelog (draft, no writes)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

# Fragment types — keep in sync with [[tool.towncrier.type]] in pyproject.toml.
TYPES=(security added changed fixed scanner deprecated removed docs misc)

# Linear workspace slug — used to construct issue URLs.
: "${AIRLOCK_LINEAR_WORKSPACE:=flightpath}"

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-40
}

cmd_new() {
  ensure_uv
  local type ticket title summary content fragment
  type="$(ui_choose "Type of change" "${TYPES[@]}")"
  [ -n "$type" ] || die "no type selected"

  summary="$(ui_input "One-line summary (e.g. 'add osv-scanner adapter')")"
  [ -n "$summary" ] || die "summary is required"

  ticket="$(ui_input "Linear ticket ID? (e.g. FP-123, leave blank to skip)")"
  if [ -n "$ticket" ]; then
    title="$(ui_input "Ticket title? (leave blank to use ID only)")"
    local url="https://linear.app/${AIRLOCK_LINEAR_WORKSPACE}/issue/${ticket}"
    if [ -n "$title" ]; then
      content="[${ticket}: ${title}](${url}) — ${summary}"
    else
      content="[${ticket}](${url}) — ${summary}"
    fi
  else
    content="$summary"
  fi

  # Orphan fragment: '+<slug>' so it isn't tied to an issue number.
  local slug; slug="$(slugify "$summary")"
  fragment="+${slug:-change}.${type}.md"

  ( cd "$ROOT" && uv run towncrier create --content "$content" "$fragment" )
  log_ok "created changelog.d/${fragment}"

  if ui_confirm "Preview the draft changelog now?"; then
    cmd_preview
  fi
}

cmd_preview() {
  ensure_uv
  local ver
  ver="$(cd "$ROOT" && uv run cz version -p 2>/dev/null || echo "UNRELEASED")"
  ui_header "Draft changelog (version ${ver})"
  ( cd "$ROOT" && uv run towncrier build --draft --version "$ver" )
}

case "${1:-new}" in
  new|"")    cmd_new ;;
  preview)   cmd_preview ;;
  *)         echo "usage: $0 {new|preview}" >&2; exit 2 ;;
esac
