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

echo "Ports ${PORT_API} (API) and ${PORT_UI} (UI) are free. Launching dev servers..."
cd "${FRONTEND_DIR}"

trap 'echo; echo "Stopping dev servers...";' EXIT

npm run dev:full
