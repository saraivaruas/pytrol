#!/usr/bin/env bash
# Construye el snap de Pytrol.
#   ./scripts/construir-snap.sh classic   snap classic, listo para el canal stable (por defecto)
#   ./scripts/construir-snap.sh beta      variante devmode, para los canales beta o edge
# Compila en una copia dentro de /tmp porque snapcraft falla si la ruta tiene espacios.
# Requiere Ubuntu 22.04 (compila en este equipo con --destructive-mode, sin instalar nada).
set -euo pipefail

VARIANTE="${1:-classic}"
case "$VARIANTE" in classic|beta) ;; *) echo "Uso: $0 [classic|beta]" >&2; exit 1 ;; esac

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d /tmp/pytrol-snap.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

rsync -a --exclude .git --exclude .flatpak-builder --exclude __pycache__ --exclude flathub \
      --exclude '*.snap' --exclude parts --exclude stage --exclude prime --exclude overlay "$AQUI/" "$TMP/"

if [[ "$VARIANTE" == beta ]]; then
  # devmode no se puede publicar en stable ni candidate, y exige grade devel.
  sed -i 's/^grade: stable/grade: devel/; s/^confinement: classic/confinement: devmode/' "$TMP/snap/snapcraft.yaml"
  sed -i 's/craftctl set version="\$version"/craftctl set version="$version-beta"/' "$TMP/snap/snapcraft.yaml"
fi

cd "$TMP" && snapcraft pack --destructive-mode
cp "$TMP"/*.snap "$AQUI/"
echo "Listo: $(ls "$TMP"/*.snap | xargs -n1 basename) en $AQUI"
