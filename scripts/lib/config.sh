# shellcheck shell=bash
# Central configuration for the airlock shell layer. Source after common.sh.

: "${AIRLOCK_ROOT:?source scripts/lib/common.sh first}"

# --- paths -----------------------------------------------------------------
AIRLOCK_SCRIPTS_DIR="${AIRLOCK_ROOT}/scripts"
AIRLOCK_SCANNERS_DIR="${AIRLOCK_ROOT}/scanners"
AIRLOCK_CONFIG_DIR="${AIRLOCK_ROOT}/config"
export AIRLOCK_SCRIPTS_DIR AIRLOCK_SCANNERS_DIR AIRLOCK_CONFIG_DIR

# --- defaults (override via environment) -----------------------------------
# Name of the per-target directory where raw scanner output is written.
: "${AIRLOCK_RESULTS_DIRNAME:=.airlock}"
# Severity gate: report fails (non-zero) if any finding is at/above this level.
: "${AIRLOCK_GATE:=high}"
# Run heckler against dependency directories too (slower). 0/1.
: "${AIRLOCK_HECKLER_SCAN_DEPS:=0}"
export AIRLOCK_RESULTS_DIRNAME AIRLOCK_GATE AIRLOCK_HECKLER_SCAN_DEPS

# --- supply-chain cooldown -------------------------------------------------
# Ensure uvx-run scanners (semgrep, guarddog, heckler) honor the same 3-day
# cooldown as the project. uv >= 0.9.17 understands relative durations.
: "${UV_EXCLUDE_NEWER:=3 days}"
export UV_EXCLUDE_NEWER

# --- scanner registry ------------------------------------------------------
# Default scanners run unless the user narrows the selection. Each id maps to
# an adapter at scanners/<id>.sh implementing: detect | install | run | name.
AIRLOCK_DEFAULT_SCANNERS=(gitleaks semgrep osv-scanner guarddog heckler)
# Optional adapters (off by default; e.g. require Node, or are user-provided).
AIRLOCK_OPTIONAL_SCANNERS=(anti-trojan-source)
export AIRLOCK_DEFAULT_SCANNERS AIRLOCK_OPTIONAL_SCANNERS

# Path to a scanner adapter by id.
scanner_adapter() { printf '%s/%s.sh' "$AIRLOCK_SCANNERS_DIR" "$1"; }
