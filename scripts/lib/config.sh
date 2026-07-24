# shellcheck shell=bash
# Central configuration for the cscan shell layer. Source after common.sh.

: "${CSCAN_ROOT:?source scripts/lib/common.sh first}"

# --- paths -----------------------------------------------------------------
CSCAN_SCRIPTS_DIR="${CSCAN_ROOT}/scripts"
CSCAN_SCANNERS_DIR="${CSCAN_ROOT}/scanners"
CSCAN_CONFIG_DIR="${CSCAN_ROOT}/config"
export CSCAN_SCRIPTS_DIR CSCAN_SCANNERS_DIR CSCAN_CONFIG_DIR

# --- defaults (override via environment) -----------------------------------
# Name of the per-target directory where raw scanner output is written.
: "${CSCAN_RESULTS_DIRNAME:=.cscan}"
# Severity gate: report fails (non-zero) if any finding is at/above this level.
: "${CSCAN_GATE:=high}"
# Run heckler against dependency directories too (slower). 0/1.
: "${CSCAN_HECKLER_SCAN_DEPS:=0}"
export CSCAN_RESULTS_DIRNAME CSCAN_GATE CSCAN_HECKLER_SCAN_DEPS

# --- supply-chain cooldown -------------------------------------------------
# Ensure uvx-run scanners (semgrep, guarddog, heckler) honor the same 3-day
# cooldown as the project. uv >= 0.9.17 understands relative durations.
: "${UV_EXCLUDE_NEWER:=3 days}"
export UV_EXCLUDE_NEWER

# --- scanner registry ------------------------------------------------------
# Default scanners run unless the user narrows the selection. Each id maps to
# an adapter at scanners/<id>.sh implementing: detect | install | run | name.
CSCAN_DEFAULT_SCANNERS=(gitleaks semgrep osv-scanner guarddog heckler)
# Optional adapters (off by default; e.g. require Node, or are user-provided).
CSCAN_OPTIONAL_SCANNERS=(anti-trojan-source)
export CSCAN_DEFAULT_SCANNERS CSCAN_OPTIONAL_SCANNERS

# Path to a scanner adapter by id.
scanner_adapter() { printf '%s/%s.sh' "$CSCAN_SCANNERS_DIR" "$1"; }
