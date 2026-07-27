# shellcheck shell=bash
# Detection / installation helpers shared by install-tools.sh and doctor.sh.
# Source after common.sh + config.sh.

: "${AIRLOCK_ROOT:?source scripts/lib/common.sh first}"

# Pick a python interpreter for small helper queries (OSV, version math).
_airlock_python() {
  if have uv; then printf 'uv run --no-project python'; return; fi
  if have python3; then printf 'python3'; return; fi
  printf 'python'
}

# osv_check <ecosystem> <name> <version>
# Returns 0 if OSV reports no advisories for that version, 1 otherwise.
osv_check() {
  local ecosystem="$1" name="$2" version="$3"
  if ! have python3 && ! have uv; then
    log_warn "no python available; skipping OSV check for ${name}"
    return 0
  fi
  OSV_ECO="$ecosystem" OSV_NAME="$name" OSV_VER="$version" python3 - <<'PY'
import json, os, sys, urllib.request
eco, name, ver = os.environ["OSV_ECO"], os.environ["OSV_NAME"], os.environ["OSV_VER"]
payload = json.dumps({"package": {"name": name, "ecosystem": eco}, "version": ver}).encode()
req = urllib.request.Request("https://api.osv.dev/v1/query", data=payload,
                             headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        vulns = json.load(r).get("vulns", [])
except Exception as exc:                       # network/parse problems: don't hard-fail
    print(f"OSV query failed for {name} {ver}: {exc}", file=sys.stderr)
    sys.exit(0)
if vulns:
    ids = ", ".join(v.get("id", "?") for v in vulns)
    print(f"{name} {ver}: {len(vulns)} OSV advisory(ies): {ids}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
PY
}

# require_clean <ecosystem> <name> <version>
# Logs and returns non-zero if the pinned version has known advisories.
require_clean() {
  if osv_check "$1" "$2" "$3"; then
    log_ok "OSV clean: $2 $3"
    return 0
  fi
  log_err "OSV advisory found for $2 $3 — refusing to install"
  return 1
}

# brew_install <formula>
brew_install() {
  have brew || die "Homebrew is required to install $1 (https://brew.sh)"
  ui_spin "Installing $1 via brew" -- brew install "$1"
}

# ensure_uv / ensure_node — soft checks used by adapters and doctor.
ensure_uv()  { have uv  || die "uv is required (https://docs.astral.sh/uv/); run: uv self update"; }
ensure_node(){ have npx || die "Node/npx is required for this optional scanner"; }
