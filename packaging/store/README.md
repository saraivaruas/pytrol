# Ficha de Pytrol en la Snap Store

Todo lo que pide la ficha (https://snapcraft.io/pytrol), listo para usar. El texto, el icono y los
enlaces salen del propio snap (`snap/snapcraft.yaml`) y se envían con `snapcraft upload-metadata`;
las imágenes se suben a mano en la web, en la pestaña **Listing** del panel del snap
(https://snapcraft.io/pytrol/listing), porque la Store no tiene una orden de consola para ellas.

## Imágenes

| Qué | Archivo | Tamaño | Límites de la Store |
|---|---|---|---|
| Icono | `packaging/store/icon.png` (también `icon:` del snap, SVG) | 512×512 | cuadrado, hasta 512×512 |
| Banner | `packaging/store/banner.png` | 1920×640 (3:1) | entre 720×240 y 4320×1440, hasta 2 MB; solo se muestra si la Store destaca el snap |
| Captura 1 | `docs/pytrol-paneles.png` | 1420×800 | mínimo 480×480, proporción entre 1:2 y 2:1, hasta 2 MB |
| Captura 2 | `docs/pytrol-claro.png` | 1400×800 | idem |
| Captura 3 | `docs/pytrol-dracula.png` | 1400×800 | idem |
| Captura 4 | `docs/pytrol-preferencias.png` | 684×585 | idem |

Subir las capturas en ese orden: la primera es la que se ve en el listado.
Se regeneran con `tools/capturar-pantallas.py` y `tools/crear-imagen-social.py`.

## Textos y datos de la ficha

- **Nombre:** `pytrol` · **Título:** Pytrol
- **Resumen (≤ 78 caracteres):** Terminal avanzado con paneles, proyectos y editor integrado
- **Descripción:** la de `snap/snapcraft.yaml`.
- **Categorías sugeridas:** Desarrollo (*development*) y Utilidades (*utilities*). Se eligen en la web.
- **Licencia:** MIT · **Sitio web, código fuente y errores:** https://github.com/saraivaruas/pytrol
- **Contacto:** https://github.com/saraivaruas/pytrol/issues
