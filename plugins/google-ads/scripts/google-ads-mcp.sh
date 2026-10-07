#!/bin/bash
# Arranca o servidor MCP oficial do Google Ads (github.com/googleads/google-ads-mcp)
# por stdio, a partir das credenciais em variáveis de ambiente.
#
# O google-ads-mcp autentica com Application Default Credentials (ADC). Se
# GOOGLE_ADS_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN estiverem definidos,
# geramos um ficheiro ADC do tipo "authorized_user" com eles; caso contrário
# usa-se o ADC já existente (ex.: `gcloud auth application-default login`).
#
# Variáveis: ver README.md.
set -euo pipefail

VERSION="${GOOGLE_ADS_MCP_VERSION:-0.0.4}"

if [ -n "${GOOGLE_ADS_REFRESH_TOKEN:-}" ] && [ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
  : "${GOOGLE_ADS_CLIENT_ID:?GOOGLE_ADS_CLIENT_ID em falta}"
  : "${GOOGLE_ADS_CLIENT_SECRET:?GOOGLE_ADS_CLIENT_SECRET em falta}"
  dir="${XDG_CONFIG_HOME:-$HOME/.config}/google-ads-mcp"
  mkdir -p "$dir"
  umask 077
  python3 - "$dir/adc.json" <<'PY'
import json, os, sys
json.dump({
    "type": "authorized_user",
    "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
    "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
    "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
}, open(sys.argv[1], "w"))
PY
  export GOOGLE_APPLICATION_CREDENTIALS="$dir/adc.json"
fi

# O ID de cliente MCC tem de ser só dígitos.
if [ -n "${GOOGLE_ADS_LOGIN_CUSTOMER_ID:-}" ]; then
  export GOOGLE_ADS_LOGIN_CUSTOMER_ID="${GOOGLE_ADS_LOGIN_CUSTOMER_ID//[^0-9]/}"
fi

if command -v uvx >/dev/null 2>&1; then
  exec uvx --quiet --from "google-ads-mcp==$VERSION" google-ads-mcp
elif command -v pipx >/dev/null 2>&1; then
  exec pipx run --spec "google-ads-mcp==$VERSION" google-ads-mcp
else
  echo "google-ads-mcp: instale 'uv' ou 'pipx' (Python 3.12+)." >&2
  exit 1
fi
