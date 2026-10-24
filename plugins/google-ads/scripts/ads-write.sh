#!/bin/bash
# Corre ads_write.py com a biblioteca oficial google-ads (via uv, sem instalar nada).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec uv run --quiet --python 3.12 --with "google-ads>=28" python "$DIR/ads_write.py" "$@"
