#!/usr/bin/env bash
set -euo pipefail

# PackyCode macOS .app build script (py2app)
# Usage:
#   bash build_app.sh            # build with venv, install deps, create .app
#   bash build_app.sh --open     # build and open the .app
#   bash build_app.sh --clean    # clean build artifacts then build
#   bash build_app.sh --no-venv  # build in current environment (no venv)

cd "$(dirname "$0")"

CLEAN=0
OPEN_APP=0
USE_VENV=1

for arg in "$@"; do
  case "$arg" in
    --clean) CLEAN=1 ;;
    --open) OPEN_APP=1 ;;
    --no-venv) USE_VENV=0 ;;
    -h|--help)
      cat <<'USAGE'
PackyCode .app build script

Options:
  --clean     Remove build/ and dist/ before building
  --open      Open the generated .app after build
  --no-venv   Do not create/use a local virtualenv
USAGE
      exit 0
      ;;
  esac
done

if [[ ${CLEAN} -eq 1 ]]; then
  echo "[clean] Removing build/ dist/ ..."
  rm -rf build dist
fi

PY=python3
if [[ ${USE_VENV} -eq 1 ]]; then
  if [[ ! -d .venv ]]; then
    echo "[venv] Creating virtual environment (.venv) ..."
    ${PY} -m venv .venv
  fi
  # shellcheck disable=SC1091
  source .venv/bin/activate
  PY=python
  echo "[venv] Using $(python --version) at $(command -v python)"
fi

echo "[deps] Installing runtime dependencies ..."
${PY} -m pip install --upgrade pip wheel >/dev/null
${PY} -m pip install -r requirements.txt

echo "[deps] Installing py2app ..."
${PY} -m pip install py2app

echo "[build] Running py2app ..."
${PY} setup.py py2app -q

APP_PATH="dist/PackyCode.app"
if [[ -d "${APP_PATH}" ]]; then
  echo "[ok] Built: ${APP_PATH}"
  if [[ -f "${APP_PATH}/Contents/Resources/icon.png" ]]; then
    echo "[ok] Icon bundled: Contents/Resources/icon.png"
  fi
  if [[ ${OPEN_APP} -eq 1 ]]; then
    echo "[open] Launching app ..."
    open "${APP_PATH}"
  fi
else
  echo "[error] Build failed, not found: ${APP_PATH}" >&2
  exit 1
fi

