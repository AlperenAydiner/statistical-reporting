#!/usr/bin/env bash
# statrep setup — provisions an isolated virtual environment and probes
# optional capabilities (R, LibreOffice). Never touches system Python.
#
# Usage:
#   ./setup.sh            install everything
#   ./setup.sh --check    re-run only the capability probe (= `statrep doctor`)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"
CAP_DIR="$SCRIPT_DIR/.statrep"
CAP_FILE="$CAP_DIR/capabilities.json"

RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; BOLD='\033[1m'; NC='\033[0m'

CHECK_ONLY=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_ONLY=1
fi

# ─────────────────────────────────────────
# Step 1: Python version
# ─────────────────────────────────────────
find_python() {
  for cand in python3.12 python3.11 python3.10 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
      ver="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
      major="${ver%%.*}"; minor="${ver##*.}"
      if [[ "$major" -eq 3 && "$minor" -ge 10 ]]; then
        echo "$cand"; return 0
      fi
    fi
  done
  return 1
}

if [[ "$CHECK_ONLY" -eq 0 ]]; then
  echo -e "${BOLD}[1/4] Python${NC}"
  PYTHON_BIN="$(find_python || true)"
  if [[ -z "${PYTHON_BIN:-}" ]]; then
    echo -e "${RED}No Python >= 3.10 found. Install Python 3.10+ and re-run.${NC}" >&2
    exit 1
  fi
  echo -e "  ${GREEN}✓${NC} $($PYTHON_BIN --version) at $(command -v "$PYTHON_BIN")"

  # ─────────────────────────────────────────
  # Step 2: Virtual environment — always .venv, never system Python
  # ─────────────────────────────────────────
  echo -e "${BOLD}[2/4] Virtual environment${NC}"
  if command -v uv >/dev/null 2>&1; then
    echo "  Using uv (fast path)"
    uv venv --python "$PYTHON_BIN" "$VENV_DIR" >/dev/null
    VENV_PY="$VENV_DIR/bin/python"
    VIRTUAL_ENV="$VENV_DIR" uv pip install --python "$VENV_PY" -r requirements.txt
    VIRTUAL_ENV="$VENV_DIR" uv pip install --python "$VENV_PY" -e .
  else
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    VENV_PY="$VENV_DIR/bin/python"
    "$VENV_PY" -m pip install -q --upgrade pip
    "$VENV_PY" -m pip install -q -r requirements.txt
    "$VENV_PY" -m pip install -q -e .
  fi
  echo -e "  ${GREEN}✓${NC} Installed into $VENV_DIR (statrep and all dependencies)"

  echo -e "${BOLD}[3/4] Capability probe${NC}"
else
  VENV_PY="$VENV_DIR/bin/python"
  if [[ ! -x "$VENV_PY" ]]; then
    echo -e "${RED}No .venv found — run ./setup.sh first (without --check).${NC}" >&2
    exit 1
  fi
  echo -e "${BOLD}Capability probe${NC}"
fi

# ─────────────────────────────────────────
# Step 3: Probe optional capabilities
# ─────────────────────────────────────────
mkdir -p "$CAP_DIR"

R_PRESENT=false
R_PACKAGES="[]"
if command -v Rscript >/dev/null 2>&1; then
  R_PRESENT=true
  R_PACKAGES="$(Rscript -e 'cat(paste0("[", paste(shQuote(rownames(installed.packages()), type="cmd"), collapse=","), "]"))' 2>/dev/null || echo "[]")"
  echo -e "  ${GREEN}✓${NC} R found: $(Rscript --version 2>&1 | head -1)"
else
  echo -e "  ${YELLOW}~${NC} R not found — SEM/HLM analyses and the flextable table path will be unavailable (optional)"
fi

SOFFICE_PRESENT=false
SOFFICE_WORKS=false
if command -v soffice >/dev/null 2>&1; then
  SOFFICE_PRESENT=true
  # Presence is not enough — some containers ship a soffice binary that
  # fails to convert anything at all. Probe with a real, tiny conversion.
  PROBE_DIR="$(mktemp -d)"
  echo "probe" > "$PROBE_DIR/probe.txt"
  if timeout 25 soffice --headless -env:"UserInstallation=file://$PROBE_DIR/profile" \
       --convert-to pdf --outdir "$PROBE_DIR/out" "$PROBE_DIR/probe.txt" \
       >/dev/null 2>&1 && [[ -f "$PROBE_DIR/out/probe.pdf" ]]; then
    SOFFICE_WORKS=true
    echo -e "  ${GREEN}✓${NC} LibreOffice found and conversion works: $(soffice --version 2>&1 | head -1)"
  else
    echo -e "  ${YELLOW}~${NC} LibreOffice binary found but conversion failed in this environment — PDF export and page-count measurement will be skipped, .docx/.html output is unaffected"
  fi
  rm -rf "$PROBE_DIR"
else
  echo -e "  ${YELLOW}~${NC} LibreOffice not found — PDF export and page-count measurement will be skipped (optional)"
fi

"$VENV_PY" - "$CAP_FILE" "$R_PRESENT" "$R_PACKAGES" "$SOFFICE_PRESENT" "$SOFFICE_WORKS" <<'PYEOF'
import json, sys
cap_file, r_present, r_packages, soffice_present, soffice_works = sys.argv[1:6]
try:
    r_pkgs = json.loads(r_packages)
except Exception:
    r_pkgs = []
data = {
    "r_present": r_present == "true",
    "r_packages": r_pkgs,
    "soffice_present": soffice_present == "true",
    "soffice_works": soffice_works == "true",
}
with open(cap_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"  Wrote {cap_file}")
PYEOF

if [[ "$CHECK_ONLY" -eq 0 ]]; then
  echo -e "${BOLD}[4/4] Done${NC}"
  echo ""
  echo -e "${GREEN}statrep is installed.${NC} Activate it with:"
  echo "  source .venv/bin/activate"
  echo "Or run directly:"
  echo "  .venv/bin/statrep doctor"
  echo "  .venv/bin/statrep build --input your-data.xlsx --tier standard --lang tr"
fi
