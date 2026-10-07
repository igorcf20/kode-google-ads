#!/bin/bash
# Copia todas as skills de github.com/google/skills para os plugins deste
# repositório, uma área por plugin. Correr de novo para atualizar.
#   scripts/sync-google-skills.sh [ref]   (por omissão: main)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${1:-main}"
SRC="$(mktemp -d)"
trap 'rm -rf "$SRC"' EXIT

git clone --quiet --depth 1 --branch "$REF" https://github.com/google/skills "$SRC"
COMMIT="$(git -C "$SRC" rev-parse HEAD)"

# Skills de Google Cloud úteis para a nossa atividade (sites, Google Ads/GA4,
# relatórios, conteúdo com IA). Vão para google-cloud-essencial (ativo);
# as restantes ficam em google-cloud (desativado por omissão).
CLOUD_ESSENCIAL=(
  google-cloud-recipe-onboarding  # projeto, faturação, APIs
  google-cloud-recipe-auth        # OAuth/ADC (credenciais Google Ads API)
  gcloud
  iam-helper-for-troubleshooting  # erros de permissão
  google-cloud-waf-cost-optimization
  bigquery-basics                 # exportações GA4 / Google Ads Data Transfer
  bigquery-ai-ml                  # previsões e segmentação sobre esses dados
  gemini-api                      # geração de textos/anúncios com Gemini
  cloud-run-basics                # alojar serviços (ex.: google-ads-mcp remoto)
  firebase-basics
  google-cloud-storage-basics
)

# área do google/skills -> plugin deste repositório
declare -A MAP=(
  [ads]=google-ads
  [analytics]=google-analytics
  [cloud]=google-cloud
  [developers]=google-developers
  [identity]=google-identity
)

# Limpa as cópias anteriores (as nossas skills ficam).
OURS=(gestao-google-ads)
for dir in "$ROOT"/plugins/*/skills/*/; do
  name="$(basename "$dir")"
  [[ " ${OURS[*]} " == *" $name "* ]] || rm -rf "$dir"
done

for area in "${!MAP[@]}"; do
  plugin="${MAP[$area]}"
  for dir in "$SRC/skills/$area"/*/; do
    name="$(basename "$dir")"
    # Skills de Ads ligadas à gestão de contas ficam no plugin google-ads;
    # as restantes (SDKs, IMA, Data Manager) vão para google-ads-dev.
    target="$plugin"
    if [ "$area" = ads ] && [[ "$name" != google-ads-api-* ]]; then
      target=google-ads-dev
    fi
    if [ "$area" = cloud ] && [[ " ${CLOUD_ESSENCIAL[*]} " == *" $name "* ]]; then
      target=google-cloud-essencial
    fi
    dest="$ROOT/plugins/$target/skills/$name"
    rm -rf "$dest"
    mkdir -p "$(dirname "$dest")"
    cp -R "$dir" "$dest"
  done
done

for p in "$ROOT"/plugins/*/; do
  [ -d "$p/skills" ] && cp "$SRC/LICENSE" "$p/skills/LICENSE-google-skills"
done

echo "$COMMIT" > "$ROOT/GOOGLE_SKILLS_COMMIT"
echo "google/skills@$COMMIT sincronizado."
