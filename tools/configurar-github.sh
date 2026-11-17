#!/usr/bin/env bash
# Configura el repositorio público en GitHub: descripción, temas (para que aparezca en las búsquedas),
# seguridad y, si lo pides, la protección de la rama main (todo cambio entra por Pull Request).
# Requiere la CLI «gh» autenticada con tu cuenta (gh auth login).
# Uso: tools/configurar-github.sh [usuario/repositorio]
#      PROTEGER_MAIN=1 tools/configurar-github.sh      # además protege main
set -euo pipefail
REPO="${1:-saraivaruas/pytrol}"
DESC="Pytrol: terminal avanzado para Linux con paneles divisibles, un proyecto por panel, árbol de archivos y editor integrado. Python + GTK 3 + VTE. MIT"
cd "$(dirname "$0")/.."

echo "== 1/4 Repositorio público"
gh repo view "$REPO" >/dev/null 2>&1 || gh repo create "$REPO" --public --description "$DESC" --homepage "https://github.com/$REPO"
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$REPO.git"
echo "   (no se sube nada: haz «git push» tú cuando quieras publicar)"

echo "== 2/4 Descripción, temas y ajustes"
gh repo edit "$REPO" --description "$DESC" --enable-issues --enable-discussions \
  --enable-wiki=false --enable-projects=false --delete-branch-on-merge \
  --enable-squash-merge --enable-merge-commit=false --enable-rebase-merge=false
for t in terminal terminal-emulator linux gtk3 vte python pygobject developer-tools code-editor tabs \
         split-panes flatpak snap productivity gtksourceview; do
  gh repo edit "$REPO" --add-topic "$t"
done

echo "== 3/4 Seguridad: reporte privado de vulnerabilidades, alertas de secretos y de dependencias"
gh api -X PUT "repos/$REPO/private-vulnerability-reporting" >/dev/null || echo "   (actívalo a mano en Settings > Security)"
gh api -X PATCH "repos/$REPO" -F "security_and_analysis[secret_scanning][status]=enabled" -F "security_and_analysis[secret_scanning_push_protection][status]=enabled" >/dev/null || true
gh api -X PUT "repos/$REPO/vulnerability-alerts" >/dev/null || true

echo "== 4/4 Protección de la rama main"
if [[ "${PROTEGER_MAIN:-0}" == 1 ]]; then
  # Cuidado: después de esto ya no se puede hacer push directo a main (los commits de «Manifest de
  # envío a Flathub» tampoco): todo cambio, incluido el de cada versión, entra por Pull Request.
  gh api -X PUT "repos/$REPO/branches/main/protection" --input - >/dev/null <<'JSON'
{
  "required_status_checks": {"strict": true, "contexts": ["Pruebas en ubuntu-22.04", "Pruebas en ubuntu-24.04"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "require_code_owner_reviews": true, "dismiss_stale_reviews": true},
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
  echo "   main protegida."
else
  echo "   omitida (usa PROTEGER_MAIN=1 para activarla)."
fi
echo "Listo: https://github.com/$REPO"
echo "Falta a mano (solo la web lo permite): Settings > General > Social preview > subir docs/social-preview.png"
