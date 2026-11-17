# Política de seguridad

Pytrol es un terminal: ve lo que escribes, incluidas contraseñas y claves. Tomamos los reportes en serio.

## Versiones con soporte

| Versión | Soporte |
|---|---|
| 0.6.x | ✅ correcciones de seguridad |
| Anteriores | ❌ actualiza a la última |

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa el reporte privado de GitHub: pestaña **Security → Report a vulnerability** de este repositorio. Incluye:

- la versión y cómo lo instalaste (`install.sh`, Flatpak o Snap),
- tu distribución y si usas X11 o Wayland,
- los pasos para reproducirlo y qué impacto tiene.

Responderemos en un plazo de **7 días** y buscaremos publicar la corrección y el aviso de forma coordinada.

## Qué se considera vulnerabilidad

- Que otro programa o usuario pueda leer la contraseña que escribes en la ventana de `sudo` y `ssh` de Pytrol.
- Que un archivo, un nombre de carpeta o lo que imprime un terminal pueda ejecutar comandos, sin que tú lo pidas, a través de Pytrol (el árbol de archivos, el editor, los enlaces, la sesión restaurada).
- Que la sesión guardada o la configuración se escriban en un lugar o con permisos que expongan su contenido a otras personas del equipo.
- Que el snap o el Flatpak entreguen a un programa más acceso del que se documenta aquí.

## Límites conocidos (no son vulnerabilidades)

- **Pytrol no es una barrera de seguridad.** Ejecuta tu shell con tus permisos, igual que cualquier terminal.
- **La sesión guarda lo que se ve en cada terminal** (pantalla e historial, hasta 5000 líneas) para mostrarlo al reabrir. Solo tu usuario puede leerla (`~/.config/pytrol` en 700, archivos en 600). Si trabajas con secretos, desactívalo en Preferencias («Conservar lo escrito en cada terminal…») o marca el panel como «no recordar».
- **La ventana de contraseña** (`SUDO_ASKPASS`, `SSH_ASKPASS`) existe para que programas sin terminal puedan pedir tu clave; cualquier programa que se ejecute dentro de un panel y use `sudo -A` puede abrirla. Se desactiva en Preferencias.
- **Flatpak:** para ser un terminal necesita ejecutar el shell del sistema (`flatpak-spawn --host`) y ver tu carpeta personal. Es lo que hacen otros terminales en Flathub.
- **Snap:** usa confinamiento *classic* (sin aislamiento) por la misma razón. La variante beta en `devmode` tampoco aísla: sirve para probar, no es una versión más segura.
