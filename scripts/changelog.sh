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

slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-40
}

cmd_new() {
  ensure_uv
  local type id summary fragment
  type="$(ui_choose "Type of change" "${TYPES[@]}")"
  [ -n "$type" ] || die "no type selected"

  summary="$(ui_input "One-line summary (e.g. 'add osv-scanner adapter')")"
  [ -n "$summary" ] || die "summary is required"

  id="$(ui_input "Issue/PR number (leave blank for a no-issue fragment)")"
  if [ -n "$id" ]; then
    fragment="${id}.${type}.md"
  else
    # Orphan fragment: '+<slug>' so it isn't tied to an issue number.
    local slug; slug="$(slugify "$summary")"
    fragment="+${slug:-change}.${type}.md"
  fi

  ( cd "$ROOT" && uv run towncrier create --content "$summary" "$fragment" )
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
