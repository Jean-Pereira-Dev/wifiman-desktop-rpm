#!/usr/bin/env bash
# Successful discovery exits 0; errors fail closed. See --help for offline input.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/check_version.py "$@"
