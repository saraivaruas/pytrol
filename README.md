# Pytrol

**Advanced Python Terminal: Power, Speed, Control.**

Terminal avanzado para Linux escrito en Python con GTK 3 y VTE (el mismo motor
que GNOME Terminal). Licencia MIT.

- **Sesión a tu medida**: por defecto Pytrol recuerda paneles, proyectos, archivos y contenido. Un panel puede marcarse como «no recordar» (clic derecho o menú Paneles) para que vuelva limpio, y Archivo → «Salir sin guardar la sesión» empieza de cero la próxima vez.
- Pestañas reordenables que heredan el directorio actual.
- **Paneles divisibles** en 2, 4, 6 u 8, vertical u horizontalmente (menú
  Paneles → Diseño de paneles), o dividiendo el panel activo a mano. En las
  cuadrículas eliges qué divisores se mueven de forma independiente (verticales
  por fila u horizontales por columna) y puedes intercambiarlos en cualquier
  momento con Paneles → Diseño de paneles → Intercambiar divisores.
- **Un proyecto distinto por panel**: menú Proyectos → abre una carpeta en el
  panel actual, en un panel nuevo o en una pestaña nueva. Cada panel muestra una
  cabecera con su carpeta y hay lista de proyectos recientes.
- **Árbol de archivos en cada panel**: a la izquierda de cada terminal, el árbol
  de carpetas y archivos de su proyecto (o del directorio actual del shell si no
  hay proyecto abierto). Se actualiza solo cuando cambian los archivos, carga las
  carpetas al expandirlas, y con doble clic entra en una carpeta (`cd` en ese
  terminal) o abre un archivo con la aplicación predeterminada. Menú contextual:
  insertar ruta, copiar ruta, nuevo panel o pestaña en esa carpeta, archivos
  ocultos, fijar carpeta. Se oculta por panel (botón ×) o en todos los paneles
  con Ctrl+Shift+E.
- Barra de menú completa (Archivo, Paneles, Proyectos, Edición, Ver,
  Preferencias, Ayuda) que se puede ocultar con Ctrl+Shift+M.
- **Preferencias**: fuente, esquema de colores (qterminal oscuro, Dracula,
  Solarized, claro), cursor, historial, shell y **todos los atajos editables**.
  Se guardan en `~/.config/pytrol/config.json`.
- **Sesión persistente**: cada 5 segundos guarda pestañas, divisiones, la
  carpeta de cada panel y **lo escrito en cada terminal** (pantalla e historial,
  hasta 5000 líneas); al volver a abrir, por cierre normal o de golpe (corte de
  luz, `kill`, cuelgue), reconstruye todo y muestra el contenido anterior bajo
  un separador. Si limpiaste con `clear`, se restaura vacío. Se puede desactivar
  en Preferencias.
- **Editor integrado en cada panel**: doble clic en un archivo del árbol (o
  Archivo → Abrir archivo en el editor…, Ctrl+Shift+F) lo abre encima del
  terminal de ese panel, con pestañas por archivo, resaltado de sintaxis y
  números de línea (GtkSourceView), Ctrl+S para guardar, Ctrl+W para cerrar la
  pestaña y Esc para volver al terminal. Marca con ● los archivos con cambios,
  avisa antes de cerrar sin guardar y recuerda los archivos abiertos con la
  sesión. Los binarios se abren en solo lectura. Al cerrar el último archivo el
  terminal recupera todo el panel.
- **sudo y ssh sin terminal**: cuando `sudo` o `ssh` los ejecuta un programa que
  no tiene terminal (un script, un asistente como Claude Code, una aplicación
  gráfica lanzada desde el panel), en vez de fallar con "a terminal is required
  to read the password" aparece una ventana de Pytrol que pide la contraseña.
  Lo hace fijando `SUDO_ASKPASS` y `SSH_ASKPASS` en cada panel hacia
  `~/.config/pytrol/askpass`, que abre `pytrol --askpass`. Si escribes `sudo` tú
  mismo en el terminal, sigue preguntando ahí como siempre. Se puede desactivar
  en Preferencias.
- **Cierre seguro**: al cerrar pregunta dos veces (configurable: ninguna, una o
  dos) para que no se pierda el trabajo por un atajo pulsado sin querer. Si el
  shell termina por sí solo con `exit`, no pregunta.

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
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 gir1.2-gtksource-4
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
| Dividir vertical (izq/der)           | Ctrl+Shift+R              |
| Dividir horizontal (arriba/abajo)    | Ctrl+Shift+D              |
| Cerrar panel                         | Ctrl+Shift+X              |
| Moverse entre paneles                | Alt+flechas               |
| Abrir proyecto en este panel         | Ctrl+Shift+O              |
| Abrir proyecto en nueva pestaña      | Ctrl+Shift+P              |
| Abrir archivo en el editor           | Ctrl+Shift+F              |
| Editor: guardar / cerrar / al terminal | Ctrl+S / Ctrl+W / Esc   |
| No recordar un panel / salir sin guardar sesión | Menú Paneles · clic derecho / Archivo |
| Copiar / Pegar / Seleccionar todo    | Ctrl+Shift+C / V / A      |
| Pegar en el terminal (alternativa)   | Shift+Insert, clic central (selección) |
| Pegar en el editor                   | Ctrl+V, Ctrl+Shift+V o Shift+Insert |
| Limpiar terminal                     | Ctrl+Shift+L              |
| Zoom                                 | Ctrl + / Ctrl - / Ctrl 0  |
| Mostrar u ocultar barra de menú      | Ctrl+Shift+M              |
| Árboles de proyecto (todos los paneles) | Ctrl+Shift+E           |
| Pantalla completa                    | F11                       |
| Preferencias                         | Ctrl+Shift+,              |

## Construir el Flatpak

Se compila con `org.flatpak.Builder`, la misma herramienta (y el mismo linter)
que usa Flathub. El runtime de GNOME no incluye VTE ni GtkSourceView 4, así que
el manifest los compila como módulos (variantes GTK 3); la primera compilación
tarda unos minutos.

```bash
sudo apt install flatpak
```

```bash
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

```bash
flatpak install --user flathub org.flatpak.Builder org.gnome.Platform//51 org.gnome.Sdk//51
```

```bash
flatpak run org.flatpak.Builder --user --install --force-clean --compose-url-policy=full --mirror-screenshots-url=https://dl.flathub.org/media/ --state-dir=$HOME/.cache/pytrol-build/state $HOME/.cache/pytrol-build/build-dir io.github.saraivaruas.Pytrol.yml
```

```bash
flatpak run io.github.saraivaruas.Pytrol
```

Dentro del sandbox el programa abre el shell del sistema anfitrión mediante
`flatpak-spawn --host`, por eso el manifest pide `--talk-name=org.freedesktop.Flatpak`
(el mismo permiso que usan Ptyxis, Black Box o Tilix).

Linter de Flathub (debe pasar sin errores antes de enviar):

```bash
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest flathub/io.github.saraivaruas.Pytrol.yml
```

```bash
flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream data/io.github.saraivaruas.Pytrol.metainfo.xml
```

## Publicar en Flathub (gratis)

Flathub es el repositorio que aparece en GNOME Software, KDE Discover y
flathub.org. Publicar es gratuito; el proceso es:

1. **Subir el código a GitHub** (repositorio público). Flathub necesita que el
   manifest apunte a una fuente con URL y hash, no a un directorio local.
2. **Elegir el ID definitivo.** El ID debe ser un dominio que controles al
   revés. Opciones:
   - `io.github.saraivaruas.Pytrol` (actual): Flathub pedirá verificar el dominio
     inge-innova.com con un fichero en `/.well-known/`.
   - `io.github.saraivaruas.Pytrol`: se verifica solo con tu cuenta de GitHub,
     sin tocar DNS. Es el camino más fácil.
   Si cambias el ID, renombra los ficheros en `data/`, el manifest y la
   constante `APP_ID` en `pytrol.py`.
3. **Completar el metainfo.** Cambia las URL con `saraivaruas` en
   `data/io.github.saraivaruas.Pytrol.metainfo.xml` por las reales y añade una
   captura de pantalla real en `data/screenshots/main.png`. Valida con:

   ```bash
   appstreamcli validate data/io.github.saraivaruas.Pytrol.metainfo.xml
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

## Snap

El proyecto incluye `snap/snapcraft.yaml` (base core22, **confinamiento classic**). Es
classic porque Pytrol es un terminal: el shell de cada panel debe ser el tuyo, con
acceso a tus proyectos y herramientas; un snap estricto lo encerraría en un entorno
aislado. Python y la biblioteca C vienen de la base core22 (snapd la instala sola);
GTK 3, VTE y GtkSourceView 4 van dentro del paquete (unos 35 MB).

Instalar el paquete ya construido (pide contraseña, por ser classic y local):

```bash
sudo snap install --dangerous --classic ./pytrol_0.6.4_amd64.snap
```

Quitarlo: `sudo snap remove pytrol`. Comparte `~/.config/pytrol` con la instalación
normal, así que conserva la misma sesión y preferencias.

Construirlo de nuevo (en Ubuntu 22.04; compila en este equipo y no instala nada):

```bash
./scripts/construir-snap.sh classic    # snap classic para el canal stable
./scripts/construir-snap.sh beta       # variante devmode para el canal beta
```

El script compila en una copia dentro de `/tmp` porque **snapcraft falla si la ruta del
proyecto tiene espacios**. Por debajo ejecuta `snapcraft pack --destructive-mode`.

### Beta (devmode) y después classic

La Store exige una aprobación manual para publicar un snap classic. Mientras llega,
puede publicarse una **beta en modo devmode**, que no la necesita:

| | Beta | Classic |
|---|---|---|
| Confinamiento | `devmode`, `grade: devel` | `classic`, `grade: stable` |
| Canales de la Store | `beta` y `edge` (nunca `stable` ni `candidate`) | todos, tras la aprobación |
| Versión | `0.6.4-beta` | `0.6.4` |
| Shell de los paneles | Corre sobre el sistema de archivos de core22: sin tu `git` ni tus herramientas, y solo el shell que exista allí | Tu shell y tu sistema |
| Para qué sirve | Probar la ventana, los paneles, el editor y la instalación desde la Store | Uso diario |

La beta solo sirve para validar el paquete; el uso real de un terminal es el classic.

Publicación en orden (cada paso requiere tu cuenta de Ubuntu One):

```bash
snapcraft login
snapcraft register pytrol
snapcraft upload --release=beta pytrol_0.6.4-beta_amd64.snap
```

Cuando la Store apruebe el confinamiento classic:

```bash
snapcraft upload --release=stable pytrol_0.6.4_amd64.snap
```

Detalles prácticos:

- Dentro del snap el lanzador (`snap/local/pytrol-launcher`) cambia variables de entorno
  para encontrar sus bibliotecas; Pytrol las deja como estaban antes de abrir el shell de
  un panel o una aplicación externa, de modo que `python3`, `git`, etc. del sistema no
  ven nada del snap.

La aprobación del confinamiento classic se pide en el foro https://forum.snapcraft.io,
categoría «store-requests», explicando que Pytrol es un emulador de terminal y que su
shell debe correr en el sistema del usuario. Mientras tanto, el snap classic solo se
instala desde archivo local.
