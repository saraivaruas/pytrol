# Cómo contribuir a Pytrol

¡Gracias por querer mejorar Pytrol! El proyecto es de código abierto (licencia MIT), pero **todo cambio entra mediante un Pull Request** que revisa el mantenedor.

*(English summary at the end.)*

## Flujo

1. **Abre un issue** antes de un cambio grande, para acordar el enfoque. Para errores pequeños puedes ir directo al PR.
2. **Haz un fork** y crea una rama con un nombre claro: `fix/arbol-de-archivos`, `feat/pestanas-fijas`, `docs/instalacion-fedora`.
3. **Programa y prueba.** Todo cambio de comportamiento lleva su prueba. Las pruebas necesitan una pantalla; en un servidor sin ella:
   ```bash
   xvfb-run -a python3 -m unittest discover -s tests -v
   ```
4. **Abre el Pull Request** hacia `main` y completa la plantilla. Las pruebas automáticas (GitHub Actions) deben pasar.
5. **Revisión.** El mantenedor revisa, puede pedir cambios y, si todo está bien, hace la fusión.

## Reglas del código

- Todo está en un solo archivo, `pytrol.py`, a propósito: se instala copiándolo. Mantenlo así.
- Solo **Python 3, PyGObject, GTK 3, VTE 2.91 y GtkSourceView 4** (opcional). No se agregan otras dependencias sin discutirlo antes.
- Los textos para el usuario van en **español**; los comentarios explican el *por qué*, no el *qué*.
- La sesión del usuario es suya: nunca borrar ni sobrescribir lo guardado sin avisar.
- Si cambias algo que se ve, regenera las capturas: `tools/capturar-pantallas.py` (usa datos de ejemplo y no toca tu configuración).
- Si cambias cómo corre dentro del snap, léete antes `snap/local/pytrol-launcher`: el entorno del shell de cada panel no debe heredar nada del snap.

## Probar los paquetes

```bash
./install.sh                          # instalación local en ~/.local
./scripts/construir-snap.sh classic   # snap; ver README, sección Snap
```

## Qué es especialmente bienvenido

- Probar y reportar en otras distribuciones y en Wayland.
- Traducciones de los textos.
- Más esquemas de colores y mejoras del editor integrado.

## Seguridad

**No publiques vulnerabilidades en issues.** Mira [SECURITY.md](SECURITY.md).

## Commits

Mensajes claros, en español, que digan qué cambia para quién; uno por cambio lógico. Los commits conservan al autor real de cada cambio.

## English summary

Every change goes through a Pull Request reviewed by the maintainer. Keep `pytrol.py` as a single file, add no dependencies beyond Python 3, PyGObject, GTK 3, VTE and GtkSourceView 4, write user-facing text in Spanish and run `xvfb-run -a python3 -m unittest discover -s tests -v` before opening the PR. Report vulnerabilities privately (see [SECURITY.md](SECURITY.md)).
