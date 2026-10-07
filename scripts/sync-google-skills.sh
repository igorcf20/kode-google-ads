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

# área do google/skills -> plugin deste repositório
declare -A MAP=(
  [ads]=google-ads
  [analytics]=google-analytics
  [cloud]=google-cloud
  [developers]=google-developers
  [identity]=google-identity
)

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
