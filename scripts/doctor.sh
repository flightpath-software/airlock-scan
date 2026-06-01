#!/usr/bin/env bash
# Environment + supply-chain health check.
# Usage: doctor.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/common.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/config.sh"
# shellcheck source=/dev/null
source "${ROOT}/scripts/lib/tools.sh"

# version_ge <have> <min>  -> 0 if have >= min
version_ge() {
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

ui_header "cscan • doctor"

# --- core tooling ----------------------------------------------------------
if have uv; then
  uvver="$(uv --version 2>/dev/null | awk '{print $2}')"
  if version_ge "$uvver" "0.11.8"; then
    log_ok "uv ${uvver} (>= 0.11.8, supports the 3-day cooldown)"
  else
    log_err "uv ${uvver} is too old for relative exclude-newer — run: uv self update"
  fi
else
  log_err "uv not found — https://docs.astral.sh/uv/"
fi

have gum  && log_ok "gum present" || log_warn "gum missing (UI falls back to plain prompts) — brew install gum"
have brew && log_ok "Homebrew present" || log_warn "Homebrew missing (needed for gitleaks/osv-scanner)"
have npx  && log_ok "node/npx present (optional)" || log_warn "node/npx missing (only needed for anti-trojan-source)"

# --- scanners --------------------------------------------------------------
ui_note "Scanners:"
for id in "${CSCAN_DEFAULT_SCANNERS[@]}" "${CSCAN_OPTIONAL_SCANNERS[@]}"; do
  adapter="$(scanner_adapter "$id")"
  [ -f "$adapter" ] || continue
  if bash "$adapter" detect >/dev/null 2>&1; then
    log_ok "  ${id}"
  else
    log_warn "  ${id} (missing)"
  fi
done

# --- OSV supply-chain audit of locked dependencies -------------------------
ui_note "OSV audit of uv.lock (the versions uv will actually install):"
lock="${CSCAN_ROOT}/uv.lock"
if [ ! -f "$lock" ]; then
  log_warn "  no uv.lock yet — run 'uv sync' first"
elif ! have python3; then
  log_warn "  python3 unavailable — skipping OSV audit"
else
  if python3 - "$lock" <<'PY'
import json, sys, tomllib, urllib.request

with open(sys.argv[1], "rb") as fh:
    lock = tomllib.load(fh)

problems = 0
checked = 0
for pkg in lock.get("package", []):
    name, ver = pkg.get("name"), pkg.get("version")
    # Skip the local root project and any non-registry (editable/path) entries.
    if not name or not ver or (pkg.get("source", {}) or {}).get("editable"):
        continue
    if (pkg.get("source", {}) or {}).get("virtual"):
        continue
    payload = json.dumps({"package": {"name": name, "ecosystem": "PyPI"}, "version": ver}).encode()
    req = urllib.request.Request("https://api.osv.dev/v1/query", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            vulns = json.load(r).get("vulns", [])
    except Exception as exc:
        print(f"  ? {name} {ver}: OSV query failed ({exc})")
        continue
    checked += 1
    if vulns:
        problems += 1
        ids = ", ".join(v.get("id", "?") for v in vulns)
        print(f"  x {name} {ver}: {ids}")
print(f"  checked {checked} package(s); {problems} with advisories")
sys.exit(1 if problems else 0)
PY
  then
    log_ok "no OSV advisories in locked dependencies"
  else
    log_err "OSV advisories found above — investigate before using this environment"
  fi
fi
