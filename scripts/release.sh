#!/usr/bin/env bash
# Cut a release:
#   1. compute the next version from Conventional Commits (commitizen)
#   2. compile changelog.d/* into CHANGELOG.md (towncrier)
#   3. bump version files + uv.lock, commit, and tag (commitizen)
# Usage: release.sh [--yes]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

ensure_uv
cd "$ROOT"

assume_yes=0
[ "${1:-}" = "--yes" ] && assume_yes=1

ui_header "airlock • release"

# Warn on a dirty tree (uncommitted changes get swept into the bump commit).
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  log_warn "working tree has uncommitted changes; they may be included in the bump commit"
  if [ "$assume_yes" -eq 0 ] && ! ui_confirm "Continue anyway?"; then
    die "aborted"
  fi
fi

current="$(uv run cz version -p 2>/dev/null || echo "?")"
# `cz bump --get-next` prints the next version (or fails if no eligible commits).
if ! next="$(uv run cz bump --get-next 2>/dev/null)"; then
  die "no version-bumping commits since the last tag (need feat/fix/etc.)"
fi

log_info "current: ${current}  ->  next: ${next}"
frag_count="$(find "${ROOT}/changelog.d" -type f ! -name '.gitkeep' 2>/dev/null | wc -l | tr -d ' ')"
log_info "news fragments to compile: ${frag_count}"

if [ "$assume_yes" -eq 0 ] && ! ui_confirm "Build changelog for v${next}, then bump + tag?"; then
  die "aborted"
fi

# 1) Compile the changelog (stages CHANGELOG.md, git rm's the fragments).
ui_spin "Building CHANGELOG.md" -- uv run towncrier build --yes --version "$next"

# 2) Bump version files + uv.lock, commit (incl. staged changelog), and tag.
#    update_changelog_on_bump=false, so commitizen won't touch CHANGELOG.md.
uv run cz bump --yes

log_ok "released v${next}"
ui_note "Review the commit + tag, then publish with:  git push --follow-tags"
