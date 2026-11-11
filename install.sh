#!/usr/bin/env bash
# Instala Pytrol para el usuario actual (sin sudo) o para todo el sistema (--system).
set -euo pipefail
APP_ID=io.github.saraivaruas.Pytrol
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--system" ]]; then
  PREFIX=/usr/local
  SUDO=sudo
else
  PREFIX="$HOME/.local"
  SUDO=""
fi
BIN="$PREFIX/bin"; APPS="$PREFIX/share/applications"
ICONS="$PREFIX/share/icons/hicolor/scalable/apps"; META="$PREFIX/share/metainfo"

echo "→ Comprobando dependencias (python3-gi, GTK 3, VTE 2.91)…"
if ! python3 -c "import gi; gi.require_version('Gtk','3.0'); gi.require_version('Vte','2.91'); from gi.repository import Gtk, Vte" 2>/dev/null; then
  echo "   Faltan dependencias. Instalando con apt…"
  sudo apt-get install -y python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
fi

echo "→ Instalando en $PREFIX"
$SUDO install -Dm755 "$HERE/pytrol.py"                      "$BIN/pytrol"
$SUDO install -Dm644 "$HERE/data/$APP_ID.desktop"           "$APPS/$APP_ID.desktop"
$SUDO install -Dm644 "$HERE/data/$APP_ID.metainfo.xml"      "$META/$APP_ID.metainfo.xml"
$SUDO install -Dm644 "$HERE/data/icons/$APP_ID.svg"         "$ICONS/$APP_ID.svg"
# El .desktop debe apuntar a la ruta real cuando se instala en ~/.local
$SUDO sed -i "s|^Exec=.*|Exec=$BIN/pytrol|" "$APPS/$APP_ID.desktop"

$SUDO update-desktop-database "$APPS" 2>/dev/null || true
$SUDO gtk-update-icon-cache -q -t "$PREFIX/share/icons/hicolor" 2>/dev/null || true

echo
echo "✔ Pytrol instalado."
echo "  Ejecutar:   pytrol      (o búscalo como «Pytrol» en el menú de aplicaciones)"
if [[ -z "$SUDO" ]] && ! echo ":$PATH:" | grep -q ":$BIN:"; then
  echo "  Aviso: $BIN no está en tu PATH. Añade a ~/.bashrc:"
  echo "         export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
echo "  Desinstalar: ./uninstall.sh${1:+ $1}"
