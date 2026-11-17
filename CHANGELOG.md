# Historial de cambios

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el versionado [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Agregado
- **Snap** (`snap/snapcraft.yaml`, base core22): paquete *classic* para uso diario y variante *beta* en `devmode` para los canales beta y edge de la Store; `scripts/construir-snap.sh` construye ambos.
- **Capturas e imagen social** en `docs/`, generadas con la aplicación real y datos de ejemplo (`tools/capturar-pantallas.py`, `tools/crear-imagen-social.py`).
- README en inglés (`README.en.md`), código de conducta, guía para contribuir, política de seguridad, plantillas de issues y de Pull Request.
- CI en GitHub Actions: pruebas, metadatos de AppStream y construcción y prueba del snap (classic y beta, amd64 y arm64).
- Guía de publicación (`packaging/PUBLICAR.md`) y script de configuración del repositorio (`tools/configurar-github.sh`).

### Seguridad
- **La sesión y la configuración ya no son legibles por otras personas del equipo.** La carpeta `~/.config/pytrol` queda en 700 y `session.json` y `config.json` en 600; antes tenían los permisos normales (775 y 664) y la sesión contiene lo que se veía en cada terminal, claves incluidas. Se corrigen al abrir Pytrol también las instalaciones anteriores. Se escribe de forma atómica y 4 pruebas nuevas lo comprueban.

### Cambiado
- Dentro del snap, el shell de cada panel y las aplicaciones abiertas desde el árbol de archivos reciben el entorno original del usuario, sin las variables de las bibliotecas del snap; el ayudante de contraseña de `sudo` y `ssh` llama al comando del snap.

## [0.6.4] - 2026-11-16

### Agregado y cambiado
- Control de la sesión: cada panel puede marcarse como «no recordar» para que vuelva limpio al reabrir, y Archivo → «Salir sin guardar la sesión» descarta todo lo guardado para empezar de cero.

## [0.6.3] - 2026-11-16

### Agregado y cambiado
- En las cuadrículas de paneles puedes elegir si los divisores independientes son los verticales (por fila) o los horizontales (por columna), e intercambiarlos en una pestaña ya abierta sin perder terminales ni proyectos.

## [0.6.2] - 2026-11-16

### Agregado y cambiado
- Los diseños de paneles horizontales (varias filas) ahora tienen divisores independientes en cada columna: mover el divisor de una columna ya no mueve el de las demás.

## [0.6.1] - 2026-11-13

### Agregado y cambiado
- Pegar desde el portapapeles funciona en todos lados: Ctrl+Shift+V, el menú Editar y el menú contextual actúan sobre el editor o el terminal que tenga el foco, y Shift+Insert también pega en el terminal.

## [0.6.0] - 2026-11-13

### Agregado y cambiado
- Editor de archivos integrado en cada panel: doble clic en el árbol abre el archivo encima del terminal, con pestañas, resaltado de sintaxis, números de línea, guardado con Ctrl+S y aviso de cambios sin guardar. Los archivos abiertos se recuerdan con la sesión.

## [0.5.1] - 2026-11-13

### Agregado y cambiado
- sudo y ssh funcionan también desde programas sin terminal (scripts, asistentes como Claude Code, aplicaciones lanzadas desde el terminal): Pytrol muestra una ventana para la contraseña en lugar del error "a terminal is required".

## [0.5.0] - 2026-11-13

### Agregado y cambiado
- Cada panel lleva su propio árbol de carpetas y archivos del proyecto: se actualiza solo, sigue al directorio del terminal o queda fijado, doble clic entra en la carpeta o abre el archivo, y se oculta por panel o para todos con Ctrl+Shift+E.

## [0.4.0] - 2026-11-13

### Agregado y cambiado
- Cada terminal conserva lo escrito al cerrar (pantalla e historial) y lo muestra de nuevo al reabrir, salvo que se haya limpiado con clear. La restauración de sesión ya no arranca shells temporales.

## [0.3.1] - 2026-11-11

### Agregado y cambiado
- Flatpak: el shell del anfitrión obtiene su terminal de control (control de trabajos, sin el aviso "can't access tty") y se usa el shell real del usuario en lugar de /bin/sh.

## [0.3.0] - 2026-11-11

### Agregado y cambiado
- Sesión persistente (restaura pestañas, paneles y carpetas tras un cierre inesperado), cierre seguro con doble confirmación, atajos de división Ctrl+Shift+R / Ctrl+Shift+D y empaquetado Flatpak sobre GNOME 51 con VTE 0.84.

## [0.2.0] - 2026-11-11

### Agregado y cambiado
- Barra de menú, paneles divisibles (2/4/6/8), proyectos por panel, preferencias y atajos configurables.

## [0.1.0] - 2026-11-11

### Agregado y cambiado
- Primera versión.
