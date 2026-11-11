# Pytrol

**Advanced Python Terminal: Power, Speed, Control.**

Terminal avanzado para Linux escrito en Python con GTK 3 y VTE (el mismo motor
que GNOME Terminal). Licencia MIT.

- Pestañas reordenables que heredan el directorio actual.
- **Paneles divisibles** en 2, 4, 6 u 8, vertical u horizontalmente (menú
  Paneles → Diseño de paneles), o dividiendo el panel activo a mano.
- **Un proyecto distinto por panel**: menú Proyectos → abre una carpeta en el
  panel actual, en un panel nuevo o en una pestaña nueva. Cada panel muestra una
  cabecera con su carpeta y hay lista de proyectos recientes.
- Barra de menú completa (Archivo, Paneles, Proyectos, Edición, Ver,
  Preferencias, Ayuda) que se puede ocultar con Ctrl+Shift+M.
- **Preferencias**: fuente, esquema de colores (qterminal oscuro, Dracula,
  Solarized, claro), cursor, historial, shell y **todos los atajos editables**.
  Se guardan en `~/.config/pytrol/config.json`.

## Instalar y probar en tu máquina

```bash
./install.sh
```

Instala en `~/.local` sin pedir contraseña (usa `./install.sh --system` para
`/usr/local`). Si faltan GTK o VTE los instala con apt. Después:

```bash
pytrol
```

También aparece como «Pytrol» en el menú de aplicaciones. Para quitarlo:

```bash
./uninstall.sh
```

## Ejecutar en desarrollo (sin instalar)

Dependencias en Ubuntu/Debian:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91
```

```bash
python3 pytrol.py
```

## Atajos

Todos se cambian en Preferencias → Atajos de teclado.

| Acción                               | Atajo por defecto         |
|--------------------------------------|---------------------------|
| Nueva pestaña / cerrar pestaña       | Ctrl+Shift+T / Ctrl+Shift+W |
| Cambiar de pestaña                   | Ctrl+PgUp / Ctrl+PgDn     |
| Dividir vertical (izq/der)           | Ctrl+Shift+→              |
| Dividir horizontal (arriba/abajo)    | Ctrl+Shift+↓              |
| Cerrar panel                         | Ctrl+Shift+X              |
| Moverse entre paneles                | Alt+flechas               |
| Abrir proyecto en este panel         | Ctrl+Shift+O              |
| Abrir proyecto en nueva pestaña      | Ctrl+Shift+P              |
| Copiar / Pegar / Seleccionar todo    | Ctrl+Shift+C / V / A      |
| Limpiar terminal                     | Ctrl+Shift+L              |
| Zoom                                 | Ctrl + / Ctrl - / Ctrl 0  |
| Mostrar u ocultar barra de menú      | Ctrl+Shift+M              |
| Pantalla completa                    | F11                       |
| Preferencias                         | Ctrl+Shift+,              |

## Construir el Flatpak

```bash
sudo apt install flatpak flatpak-builder
```

```bash
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

```bash
flatpak install --user flathub org.gnome.Platform//47 org.gnome.Sdk//47
```

```bash
flatpak-builder --user --install --force-clean build-dir com.inge_innova.Pytrol.yml
```

```bash
flatpak run com.inge_innova.Pytrol
```

Dentro del sandbox el programa abre el shell del sistema anfitrión mediante
`flatpak-spawn --host`, por eso el manifest pide `--talk-name=org.freedesktop.Flatpak`.

## Publicar en Flathub (gratis)

Flathub es el repositorio que aparece en GNOME Software, KDE Discover y
flathub.org. Publicar es gratuito; el proceso es:

1. **Subir el código a GitHub** (repositorio público). Flathub necesita que el
   manifest apunte a una fuente con URL y hash, no a un directorio local.
2. **Elegir el ID definitivo.** El ID debe ser un dominio que controles al
   revés. Opciones:
   - `com.inge_innova.Pytrol` (actual): Flathub pedirá verificar el dominio
     inge-innova.com con un fichero en `/.well-known/`.
   - `io.github.saraivaruas.Pytrol`: se verifica solo con tu cuenta de GitHub,
     sin tocar DNS. Es el camino más fácil.
   Si cambias el ID, renombra los ficheros en `data/`, el manifest y la
   constante `APP_ID` en `pytrol.py`.
3. **Completar el metainfo.** Cambia las URL con `saraivaruas` en
   `data/com.inge_innova.Pytrol.metainfo.xml` por las reales y añade una
   captura de pantalla real en `data/screenshots/main.png`. Valida con:

   ```bash
   appstreamcli validate data/com.inge_innova.Pytrol.metainfo.xml
   ```

4. **Cambiar la fuente del manifest** de `type: dir` a una etiqueta de git:

   ```yaml
   sources:
     - type: git
       url: https://github.com/saraivaruas/pytrol.git
       tag: v0.1.0
       commit: <sha del tag>
   ```

5. **Abrir el pull request** en https://github.com/flathub/flathub contra la
   rama `new-pr`, con un único fichero: el manifest. Un bot lo construye y un
   revisor humano lo aprueba; suele tardar unos días. Después Flathub crea el
   repositorio `flathub/<app-id>` y cada actualización es un PR ahí.

Guía oficial: https://docs.flathub.org/docs/for-app-authors/submission

## Alternativa: Snap Store

Si prefieres la tienda de Ubuntu, el equivalente es un `snapcraft.yaml` con
`base: core24`, extensión `gnome` y `plugs: [home, x11, wayland]`. Publicar
también es gratis con una cuenta de Ubuntu One.
