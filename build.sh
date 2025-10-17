#!/usr/bin/env bash
set -euo pipefail

# Wrapper to always clean build artifacts before packaging
# Usage:
#   bash build.sh           # clean then build (uses build_app.sh defaults)
#   bash build.sh --open    # clean then build, open the .app
#   bash build.sh --no-venv # clean then build without creating a venv

cd "$(dirname "$0")"

echo "[clean] Removing build/ dist/ ..."
rm -rf build dist

exec bash build_app.sh "$@"

