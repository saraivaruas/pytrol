#!/usr/bin/env bash
set -euo pipefail
APP_ID=io.github.saraivaruas.Pytrol
if [[ "${1:-}" == "--system" ]]; then PREFIX=/usr/local; SUDO=sudo; else PREFIX="$HOME/.local"; SUDO=""; fi
$SUDO rm -f "$PREFIX/bin/pytrol" \
  "$PREFIX/share/applications/$APP_ID.desktop" \
  "$PREFIX/share/metainfo/$APP_ID.metainfo.xml" \
  "$PREFIX/share/icons/hicolor/scalable/apps/$APP_ID.svg"
$SUDO update-desktop-database "$PREFIX/share/applications" 2>/dev/null || true
echo "✔ Pytrol desinstalado de $PREFIX (la configuración sigue en ~/.config/pytrol)"
