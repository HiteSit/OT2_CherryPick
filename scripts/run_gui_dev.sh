#!/usr/bin/env bash
# Unified dev runner: frees the fixed ports, then launches FastAPI + Vite.

set -euo pipefail

PORT_API=8000
PORT_UI=5173

if ! command -v lsof >/dev/null 2>&1; then
  echo "Error: 'lsof' is required to free occupied ports. Please install it (sudo apt install lsof)." >&2
  exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
FRONTEND_DIR="${REPO_ROOT}/src/gui/frontend"

free_port() {
  local port=$1
  local pids
  if pids=$(lsof -ti tcp:"${port}" 2>/dev/null); then
    if [[ -n "${pids}" ]]; then
      echo "Port ${port} is occupied by PID(s): ${pids}. Terminating..."
      # shellcheck disable=SC2086
      kill -9 ${pids} || true
      sleep 0.2
    fi
  fi
}

echo "Preparing development environment..."
free_port "${PORT_API}"
free_port "${PORT_UI}"

# Bootstrap new database files to gui_state if they don't exist yet
GUI_STATE_DIR="${REPO_ROOT}/gui_state"
mkdir -p "${GUI_STATE_DIR}"
for f in offset_database.toml opentrons_labware_official.txt; do
  if [[ -f "${REPO_ROOT}/${f}" && ! -f "${GUI_STATE_DIR}/${f}" ]]; then
    echo "Bootstrapping ${f} to gui_state/"
    cp "${REPO_ROOT}/${f}" "${GUI_STATE_DIR}/${f}"
  fi
done

echo "Ports ${PORT_API} (API) and ${PORT_UI} (UI) are free. Launching dev servers..."
cd "${FRONTEND_DIR}"

trap 'echo; echo "Stopping dev servers...";' EXIT

npm run dev:full
