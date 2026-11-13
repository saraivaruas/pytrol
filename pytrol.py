#!/usr/bin/env python3
"""Pytrol — Advanced Python Terminal: Power, Speed, Control (GTK3 + VTE)."""
import json
import os
import re
import shlex
import signal
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango, Vte  # noqa: E402

try:  # Resaltado de sintaxis (opcional): GtkSourceView 4 es la variante para GTK 3
    gi.require_version("GtkSource", "4")
    from gi.repository import GtkSource  # noqa: E402
    HAVE_GTKSOURCE = True
except (ValueError, ImportError):
    GtkSource = None
    HAVE_GTKSOURCE = False

APP_TITLE = "Pytrol"
APP_ID = "io.github.saraivaruas.Pytrol"
IN_FLATPAK = os.path.exists("/.flatpak-info")
CONFIG_DIR = os.environ.get("PYTROL_CONFIG_DIR") or os.path.join(GLib.get_user_config_dir(), "pytrol")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
SESSION_SAVE_SECONDS = 5
ASKPASS_HELPER = os.path.join(CONFIG_DIR, "askpass")

# ---------------------------------------------------------------- esquemas de color
SCHEMES = {
    "Oscuro (qterminal)": ("#dcdcdc", "#1e1e1e", [
        "#000000", "#cd0000", "#00cd00", "#cdcd00", "#0000ee", "#cd00cd", "#00cdcd", "#e5e5e5",
        "#7f7f7f", "#ff0000", "#00ff00", "#ffff00", "#5c5cff", "#ff00ff", "#00ffff", "#ffffff"]),
    "Dracula": ("#f8f8f2", "#282a36", [
        "#21222c", "#ff5555", "#50fa7b", "#f1fa8c", "#bd93f9", "#ff79c6", "#8be9fd", "#f8f8f2",
        "#6272a4", "#ff6e6e", "#69ff94", "#ffffa5", "#d6acff", "#ff92df", "#a4ffff", "#ffffff"]),
    "Solarized Dark": ("#839496", "#002b36", [
        "#073642", "#dc322f", "#859900", "#b58900", "#268bd2", "#d33682", "#2aa198", "#eee8d5",
        "#002b36", "#cb4b16", "#586e75", "#657b83", "#839496", "#6c71c4", "#93a1a1", "#fdf6e3"]),
    "Claro": ("#1e1e1e", "#fafafa", [
        "#000000", "#c91b00", "#00a600", "#c7c400", "#0225c7", "#ca30c7", "#00c5c7", "#c7c7c7",
        "#686868", "#ff6e67", "#5ffa68", "#fffc67", "#6871ff", "#ff77ff", "#60fdff", "#ffffff"]),
}
CURSOR_SHAPES = {"Bloque": Vte.CursorShape.BLOCK, "Línea": Vte.CursorShape.IBEAM,
                 "Subrayado": Vte.CursorShape.UNDERLINE}

# ---------------------------------------------------------------- acciones y atajos por defecto
# id, etiqueta de menú, atajo por defecto
ACTIONS = [
    ("new_tab", "Nueva pestaña", "<Primary><Shift>t"),
    ("close_tab", "Cerrar pestaña", "<Primary><Shift>w"),
    ("next_tab", "Pestaña siguiente", "<Primary>Page_Down"),
    ("prev_tab", "Pestaña anterior", "<Primary>Page_Up"),
    ("move_tab_left", "Mover pestaña a la izquierda", "<Primary><Shift>Left"),
    ("move_tab_right", "Mover pestaña a la derecha", "<Primary><Shift>Right"),
    ("quit", "Salir", "<Primary><Shift>q"),
    ("split_h", "Dividir horizontalmente (arriba/abajo)", "<Primary><Shift>d"),
    ("split_v", "Dividir verticalmente (izquierda/derecha)", "<Primary><Shift>r"),
    ("close_pane", "Cerrar panel", "<Primary><Shift>x"),
    ("focus_left", "Panel de la izquierda", "<Alt>Left"),
    ("focus_right", "Panel de la derecha", "<Alt>Right"),
    ("focus_up", "Panel de arriba", "<Alt>Up"),
    ("focus_down", "Panel de abajo", "<Alt>Down"),
    ("open_project", "Abrir proyecto en este panel…", "<Primary><Shift>o"),
    ("open_project_split_v", "Abrir proyecto en nuevo panel (vertical)…", ""),
    ("open_project_split_h", "Abrir proyecto en nuevo panel (horizontal)…", ""),
    ("open_project_tab", "Abrir proyecto en nueva pestaña…", "<Primary><Shift>p"),
    ("open_file", "Abrir archivo en el editor…", "<Primary><Shift>f"),
    ("save_file", "Guardar archivo del editor", ""),
    ("close_file", "Cerrar archivo del editor", ""),
    ("copy", "Copiar", "<Primary><Shift>c"),
    ("paste", "Pegar", "<Primary><Shift>v"),
    ("select_all", "Seleccionar todo", "<Primary><Shift>a"),
    ("clear", "Limpiar terminal", "<Primary><Shift>l"),
    ("zoom_in", "Aumentar zoom", "<Primary>plus"),
    ("zoom_out", "Reducir zoom", "<Primary>minus"),
    ("zoom_reset", "Zoom normal", "<Primary>0"),
    ("toggle_menubar", "Mostrar barra de menú", "<Primary><Shift>m"),
    ("fullscreen", "Pantalla completa", "F11"),
    ("toggle_tree", "Árboles de proyecto en los paneles", "<Primary><Shift>e"),
    ("pin_tree", "Fijar carpeta del árbol de este panel", ""),
    ("tree_show_hidden", "Mostrar archivos ocultos en el árbol", ""),
    ("preferences", "Preferencias…", "<Primary><Shift>comma"),
]
ACTION_LABELS = {a[0]: a[1] for a in ACTIONS}
DEFAULT_SHORTCUTS = {a[0]: a[2] for a in ACTIONS}

# Diseños predefinidos: (etiqueta, filas, columnas)
LAYOUTS = [
    ("2 paneles verticales (izq/der)", 1, 2),
    ("2 paneles horizontales (arriba/abajo)", 2, 1),
    ("4 paneles (2×2)", 2, 2),
    ("6 paneles verticales (2 filas × 3)", 2, 3),
    ("6 paneles horizontales (3 filas × 2)", 3, 2),
    ("8 paneles verticales (2 filas × 4)", 2, 4),
    ("8 paneles horizontales (4 filas × 2)", 4, 2),
]

DEFAULT_CONFIG = {
    "font": "Monospace 11",
    "scheme": "Oscuro (qterminal)",
    "scrollback": 10000,
    "cursor_shape": "Bloque",
    "cursor_blink": True,
    "shell": "",
    "show_menubar": True,
    "show_pane_headers": True,
    "restore_scrollback": True,
    "restore_scrollback_lines": 5000,
    "show_tree": True,
    "tree_width": 220,
    "tree_show_hidden": False,
    "askpass": True,
    "editor_height": 340,
    "window_size": [1000, 620],
    "restore_session": True,
    "confirm_close": 2,
    "shortcuts": dict(DEFAULT_SHORTCUTS),
    "recent_projects": [],
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        with open(CONFIG_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        for k, v in data.items():
            if k == "shortcuts" and isinstance(v, dict):
                cfg["shortcuts"].update(v)
                # Migración: versiones anteriores asignaban a las divisiones las mismas
                # teclas que a "mover pestaña", y nunca llegaban a ejecutarse.
                for action, old, new in (("split_v", "<Primary><Shift>Right", "<Primary><Shift>r"),
                                         ("split_h", "<Primary><Shift>Down", "<Primary><Shift>d")):
                    if cfg["shortcuts"].get(action) == old:
                        cfg["shortcuts"][action] = new
            else:
                cfg[k] = v
    except (OSError, ValueError):
        pass
    return cfg


def ensure_askpass_helper():
    """Crea el script que sudo/ssh ejecutan cuando no hay terminal para pedir la contraseña.

    Devuelve su ruta, o None si no se pudo crear. En Flatpak el script corre en el
    anfitrión, así que invoca a Pytrol a través de `flatpak run`.
    """
    if IN_FLATPAK:
        launcher = f"exec flatpak run --command=pytrol {APP_ID} --askpass \"$@\""
    else:
        me = os.path.realpath(__file__)
        if not os.path.exists(me):
            return None
        launcher = f"exec {shlex.quote(sys.executable)} {shlex.quote(me)} --askpass \"$@\""
    script = f"#!/bin/sh\n# Generado por Pytrol: diálogo gráfico de contraseña para sudo/ssh sin terminal.\n{launcher}\n"
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        current = open(ASKPASS_HELPER, encoding="utf-8").read() if os.path.exists(ASKPASS_HELPER) else ""
        if current != script:
            with open(ASKPASS_HELPER, "w", encoding="utf-8") as fh:
                fh.write(script)
        os.chmod(ASKPASS_HELPER, 0o755)
        return ASKPASS_HELPER
    except OSError as exc:
        print(f"No se pudo crear el ayudante askpass: {exc}", file=sys.stderr)
        return None


def run_askpass(prompt):
    """Modo `pytrol --askpass`: muestra un diálogo de contraseña y la escribe en stdout."""
    prompt = (prompt or "Contraseña:").strip()
    dlg = Gtk.Dialog(title="Pytrol: autenticación")
    dlg.set_keep_above(True)
    dlg.set_position(Gtk.WindowPosition.CENTER)
    dlg.set_default_size(420, -1)
    dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
    ok = dlg.add_button("Aceptar", Gtk.ResponseType.OK)
    ok.get_style_context().add_class("suggested-action")
    box = dlg.get_content_area()
    box.set_spacing(8)
    box.set_border_width(12)
    icon = Gtk.Image.new_from_icon_name("dialog-password", Gtk.IconSize.DIALOG)
    label = Gtk.Label(label=prompt, xalign=0)
    label.set_line_wrap(True)
    head = Gtk.Box(spacing=12)
    head.pack_start(icon, False, False, 0)
    head.pack_start(label, True, True, 0)
    box.pack_start(head, False, False, 0)
    entry = Gtk.Entry()
    entry.set_visibility(False)
    entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
    entry.set_activates_default(True)
    box.pack_start(entry, False, False, 0)
    hint = Gtk.Label(label="Un programa sin terminal (p. ej. sudo desde un script) pide tu contraseña.", xalign=0)
    hint.get_style_context().add_class("dim-label")
    hint.set_line_wrap(True)
    box.pack_start(hint, False, False, 0)
    dlg.set_default_response(Gtk.ResponseType.OK)
    dlg.show_all()
    entry.grab_focus()
    response = dlg.run()
    password = entry.get_text()
    dlg.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    if response != Gtk.ResponseType.OK:
        return 1
    sys.stdout.write(password + "\n")
    sys.stdout.flush()
    return 0


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"No se pudo guardar la configuración: {exc}", file=sys.stderr)


_HOST_SHELL = None


def host_shell():
    """Shell de inicio del usuario en el sistema anfitrión (dentro de Flatpak, SHELL vale /bin/sh)."""
    global _HOST_SHELL
    if _HOST_SHELL is None:
        shell = ""
        if IN_FLATPAK:
            try:
                out = subprocess.run(
                    ["flatpak-spawn", "--host", "sh", "-c", 'getent passwd "$(id -un)" | cut -d: -f7'],
                    capture_output=True, text=True, timeout=5).stdout.strip()
                if out.startswith("/"):
                    shell = out
            except (OSError, subprocess.SubprocessError):
                pass
        _HOST_SHELL = shell or os.environ.get("SHELL") or "/bin/bash"
    return _HOST_SHELL


def load_session():
    try:
        with open(SESSION_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and data.get("tabs"):
            return data
    except (OSError, ValueError):
        pass
    return None


def write_session(data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = SESSION_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, ensure_ascii=False)
        os.replace(tmp, SESSION_FILE)
    except OSError as exc:
        print(f"No se pudo guardar la sesión: {exc}", file=sys.stderr)


def rgba(hexstr):
    c = Gdk.RGBA()
    c.parse(hexstr)
    return c


# ---------------------------------------------------------------- widgets
class SplitPaned(Gtk.Paned):
    """Paned que se coloca a una fracción del tamaño en la primera asignación."""

    def __init__(self, orientation, fraction=0.5):
        super().__init__(orientation=orientation)
        self.fraction = fraction
        self._placed = False
        self.connect("size-allocate", self._on_alloc)

    def _on_alloc(self, _w, alloc):
        if self._placed:
            return
        size = alloc.width if self.get_orientation() == Gtk.Orientation.HORIZONTAL else alloc.height
        if size > 1:
            self.set_position(int(size * self.fraction))
            self._placed = True

    @staticmethod
    def replace_child(parent, old, new):
        """Sustituye `old` por `new` dentro de un Paned o un Box."""
        if isinstance(parent, Gtk.Paned):
            first = parent.get_child1() is old
            parent.remove(old)
            if first:
                parent.pack1(new, True, False)
            else:
                parent.pack2(new, True, False)
        else:
            parent.remove(old)
            parent.pack_start(new, True, True, 0)
        new.show_all()


class Pane(Gtk.Box):
    """Un panel: cabecera opcional + terminal VTE + barra de desplazamiento."""

    def __init__(self, app, cwd=None, restore_text=None, project_root=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.restore_text = restore_text
        self.child_pid = None
        self.cd_from = self.cd_to = None
        self.project_root = project_root  # carpeta abierta con «Abrir proyecto» (o None)
        self.header = Gtk.Label(xalign=0)
        self.header.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.header.get_style_context().add_class("pane-header")
        self.header.set_no_show_all(True)
        self.pack_start(self.header, False, False, 0)

        self.term = Vte.Terminal()
        self.term.set_mouse_autohide(True)
        self.term.set_allow_hyperlink(True)
        self.term.set_scroll_on_keystroke(True)
        self.term.set_scroll_on_output(False)
        self.apply_config(app.cfg)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.term, True, True, 0)
        scrollbar = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL,
                                  adjustment=self.term.get_vadjustment())
        hbox.pack_start(scrollbar, False, False, 0)

        # Editor integrado (pestañas por archivo) encima del terminal; oculto si no hay archivos.
        self.editor_nb = Gtk.Notebook()
        self.editor_nb.set_scrollable(True)
        self.editor_nb.set_show_border(False)
        self.editor_nb.get_style_context().add_class("editor-tabs")
        self.editor_nb.set_no_show_all(True)
        self.vsplit = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.vsplit.pack1(self.editor_nb, True, False)
        self.vsplit.pack2(hbox, True, False)
        self.vsplit.set_position(int(app.cfg.get("editor_height", 340)))

        # Cada panel lleva su propio árbol de proyecto a la izquierda del terminal.
        self.tree = ProjectTree(app, self)
        self.tree_visible = None  # None = seguir la opción global
        self.body = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.body.pack1(self.tree, False, False)
        self.body.pack2(self.vsplit, True, False)
        self.body.set_position(int(app.cfg.get("tree_width", 220)))
        self.pack_start(self.body, True, True, 0)

        self.term.connect("focus-in-event", lambda *_: app.on_pane_focus(self))
        self.term.connect("button-press-event", lambda t, e: app.on_button(self, e))
        self.term.connect("window-title-changed", lambda *_: app.on_title_changed(self))
        self.term.connect("child-exited", lambda *_: app.close_pane(self, from_exit=True))
        self.spawn(cwd)

    def replay(self, text):
        """Vuelca el contenido de la sesión anterior en el terminal (solo visual)."""
        lines = text.split("\n")
        data = "\r\n".join(lines)
        sep = "\r\n\x1b[2m\u2500\u2500 sesi\u00f3n anterior restaurada \u2500\u2500\x1b[0m\r\n"
        self.term.feed((data + sep).encode("utf-8", "replace"))

    def scrollback_text(self, max_lines):
        """Texto de todo el terminal (historial + pantalla), sin l\u00edneas vac\u00edas finales."""
        t = self.term
        try:
            adj = t.get_vadjustment()
            first, last = int(adj.get_lower()), max(int(adj.get_upper()) - 1, 0)
            cols = t.get_column_count()
            if hasattr(t, "get_text_range_format"):
                res = t.get_text_range_format(Vte.Format.TEXT, first, 0, last, cols)
            else:
                res = t.get_text_range(first, 0, last, cols, None, None)
            text = res[0] if isinstance(res, (tuple, list)) else res
            if not (text or "").strip():
                # Tras `clear` (secuencia E3) la lectura por rango devuelve vacío aunque
                # la pantalla tenga texto nuevo: usar la pantalla visible como respaldo.
                if hasattr(t, "get_text_format"):
                    text = t.get_text_format(Vte.Format.TEXT)
                else:
                    text = t.get_text(None, None)[0]
        except Exception as exc:  # noqa: BLE001 - nunca romper el guardado por esto
            print(f"No se pudo leer el contenido del terminal: {exc}", file=sys.stderr)
            return ""
        if not text:
            return ""
        lines = [l.rstrip() for l in text.split("\n")]
        while lines and not lines[-1]:
            lines.pop()
        if max_lines and len(lines) > max_lines:
            lines = lines[-max_lines:]
        return "\n".join(lines)

    def spawn(self, cwd):
        cwd = cwd or os.path.expanduser("~")
        if not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")
        self.last_cwd = cwd
        shell = self.app.cfg.get("shell") or host_shell()
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        helper = ensure_askpass_helper() if self.app.cfg.get("askpass", True) else None
        if helper:
            # sudo/ssh usan este programa cuando no disponen de terminal (scripts,
            # herramientas como Claude Code, aplicaciones gráficas lanzadas desde aquí).
            env["SUDO_ASKPASS"] = helper
            env["SSH_ASKPASS"] = helper
            env.setdefault("SSH_ASKPASS_REQUIRE", "prefer")
        envv = [f"{k}={v}" for k, v in env.items()]
        flags = Vte.PtyFlags.DEFAULT
        if IN_FLATPAK:
            # El shell corre en el anfitrión. NO_CTTY: el proceso del sandbox no toma la
            # pty como terminal de control, para que la tome el shell del anfitrión y
            # tenga control de trabajos (sin el aviso "can't access tty").
            # --watch-bus: el shell termina si se cierra el panel.
            flags = Vte.PtyFlags.NO_CTTY
            argv = ["flatpak-spawn", "--host", "--watch-bus", "--env=TERM=xterm-256color",
                    "--env=COLORTERM=truecolor", f"--env=SHELL={shell}"]
            if helper:
                argv += [f"--env=SUDO_ASKPASS={helper}", f"--env=SSH_ASKPASS={helper}",
                         "--env=SSH_ASKPASS_REQUIRE=prefer"]
            argv += [f"--directory={cwd}"] + shlex.split(shell)
        else:
            argv = shlex.split(shell)
        self.term.spawn_async(flags, cwd, argv, envv,
                              GLib.SpawnFlags.SEARCH_PATH, None, None, -1, None, self._on_spawned, None)

    def _on_spawned(self, term, pid, error, *_):
        self.child_pid = pid if pid and pid > 0 else None
        # VTE reinicia el buffer al asignar la pty; por eso el contenido anterior se
        # vuelca aquí, ya con la pty asignada y antes de que el shell escriba su prompt.
        if self.restore_text:
            self.replay(self.restore_text)
            self.restore_text = None
        if error:
            print(f"No se pudo iniciar el shell: {error}", file=sys.stderr)

    def apply_config(self, cfg):
        for e in getattr(self, "editor_nb", None) and self.editors() or []:
            e.apply_config(cfg)
        t = self.term
        t.set_font(Pango.FontDescription(cfg["font"]))
        t.set_scrollback_lines(int(cfg["scrollback"]))
        fg, bg, palette = SCHEMES.get(cfg["scheme"], SCHEMES["Oscuro (qterminal)"])
        t.set_colors(rgba(fg), rgba(bg), [rgba(h) for h in palette])
        t.set_cursor_shape(CURSOR_SHAPES.get(cfg["cursor_shape"], Vte.CursorShape.BLOCK))
        t.set_cursor_blink_mode(Vte.CursorBlinkMode.ON if cfg["cursor_blink"]
                                else Vte.CursorBlinkMode.OFF)

    def title(self):
        return self.term.get_window_title() or os.path.basename(self.cwd() or "") or "Shell"

    _TITLE_RE = re.compile(r"^[^:@\s]+@[^:]+:\s*(\S.*?)\s*$")

    def cwd(self):
        """Directorio actual del shell.

        Orden: OSC 7 si el shell lo emite; /proc/<pid>/cwd del hijo (fuera de Flatpak);
        y como respaldo el título de la ventana («usuario@equipo: ~/ruta», el prompt
        por defecto de bash en Debian/Ubuntu).
        """
        uri = self.term.get_current_directory_uri()
        if uri:
            try:
                return GLib.filename_from_uri(uri)[0]
            except (GLib.Error, TypeError):
                pass
        if not IN_FLATPAK and self.child_pid:
            try:
                return os.readlink(f"/proc/{self.child_pid}/cwd")
            except OSError:
                pass
        m = self._TITLE_RE.match(self.term.get_window_title() or "")
        if m:
            path = os.path.expanduser(m.group(1))
            if os.path.isdir(path):
                return path
        return None

    def change_dir(self, path, clear=True):
        """Cambia el directorio del shell en marcha (sin matar el proceso)."""
        self.cd_from, self.cd_to = self.cwd(), path
        cmd = f" cd {shlex.quote(path)}" + (" && clear" if clear else "")
        self.term.feed_child((cmd + "\n").encode())
        self.last_cwd = path
        self.header.set_text(path)

    def tree_root(self):
        """Carpeta que debe mostrar el árbol para este panel."""
        if self.project_root and os.path.isdir(self.project_root):
            return self.project_root
        return self.cwd_or_last()

    # ---- editor integrado
    def editors(self):
        return [self.editor_nb.get_nth_page(i) for i in range(self.editor_nb.get_n_pages())]

    def current_editor(self):
        i = self.editor_nb.get_current_page()
        return self.editor_nb.get_nth_page(i) if i >= 0 else None

    def unsaved_files(self):
        return [e.path for e in self.editors() if e.is_modified()]

    def open_file(self, path):
        path = os.path.abspath(path)
        for e in self.editors():
            if e.path == path:
                self.editor_nb.set_current_page(self.editor_nb.page_num(e))
                e.view.grab_focus()
                return e
        editor = FileEditor(self, path)
        label = Gtk.Label(label=os.path.basename(path))
        label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        label.set_width_chars(min(len(os.path.basename(path)), 10))
        label.set_max_width_chars(28)
        label.set_tooltip_text(path)
        close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_focus_on_click(False)
        close.connect("clicked", lambda *_: self.close_editor(editor))
        box = Gtk.Box(spacing=4)
        box.pack_start(label, True, True, 0)
        box.pack_start(close, False, False, 0)
        box.show_all()
        editor.tab_label = label
        editor.show_all()
        idx = self.editor_nb.append_page(editor, box)
        self.editor_nb.set_tab_reorderable(editor, True)
        self.editor_nb.set_current_page(idx)
        self.editor_nb.show()
        editor.view.grab_focus()
        self.app.save_session()
        return editor

    def refresh_editor_tab(self, editor):
        name = os.path.basename(editor.path)
        editor.tab_label.set_text(("● " if editor.is_modified() else "") + name)

    def close_editor(self, editor, force=False):
        """Cierra una pestaña del editor; pregunta si tiene cambios sin guardar."""
        if editor.is_modified() and not force:
            choice = self.app.ask_save(os.path.basename(editor.path))
            if choice == "cancel":
                return False
            if choice == "save" and not editor.save():
                return False
        idx = self.editor_nb.page_num(editor)
        if idx >= 0:
            self.editor_nb.remove_page(idx)
        editor.destroy()
        if self.editor_nb.get_n_pages() == 0:
            self.editor_nb.hide()
            self.term.grab_focus()
        self.app.save_session()
        return True

    def tree_shown(self):
        return self.app.cfg.get("show_tree", True) if self.tree_visible is None else self.tree_visible

    def set_tree_visible(self, visible):
        """Muestra u oculta el árbol de este panel (None = volver a la opción global)."""
        self.tree_visible = visible
        if self.tree_shown():
            self.tree.show_all()
            self.sync_tree()
        else:
            self.tree.hide()

    def sync_tree(self):
        """El árbol muestra el proyecto del panel o, sin proyecto, el directorio actual."""
        if self.tree.get_visible():
            self.tree.set_root(self.tree_root())

    def cwd_or_last(self):
        cwd = self.cwd()
        # Justo después de un «cd» pedido por Pytrol, el shell puede no haberlo
        # ejecutado aún: hasta que cambie, damos por bueno el destino pedido.
        if getattr(self, "cd_to", None):
            if cwd is None or cwd == self.cd_from:
                return self.cd_to
            self.cd_to = None
        if cwd:
            self.last_cwd = cwd
        return self.last_cwd


class FileEditor(Gtk.Box):
    """Un archivo abierto en el editor integrado de un panel."""

    def __init__(self, pane, path):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.pane = pane
        self.path = os.path.abspath(path)
        self.readonly = False
        if HAVE_GTKSOURCE:
            self.buffer = GtkSource.Buffer()
            self.view = GtkSource.View(buffer=self.buffer)
            self.view.set_show_line_numbers(True)
            self.view.set_highlight_current_line(True)
            self.view.set_auto_indent(True)
            self.view.set_tab_width(4)
            self.view.set_smart_home_end(GtkSource.SmartHomeEndType.BEFORE)
            lang = GtkSource.LanguageManager.get_default().guess_language(self.path, None)
            if lang:
                self.buffer.set_language(lang)
        else:
            self.buffer = Gtk.TextBuffer()
            self.view = Gtk.TextView(buffer=self.buffer)
        self.view.set_monospace(True)
        self.view.set_left_margin(6)
        self.view.set_right_margin(6)
        self.apply_config(pane.app.cfg)
        self.view.connect("key-press-event", self.on_key)
        self.view.connect("focus-in-event", lambda *_: pane.app.on_pane_focus(pane))
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.view)
        self.pack_start(sw, True, True, 0)
        self.status = Gtk.Label(xalign=0)
        self.status.get_style_context().add_class("editor-status")
        self.pack_start(self.status, False, False, 0)
        self.load()
        self.buffer.connect("modified-changed", lambda *_: self.pane.refresh_editor_tab(self))
        self.buffer.connect("notify::cursor-position", lambda *_: self.update_status())

    # ---- archivo
    def load(self):
        try:
            with open(self.path, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            raw = b""
            self.readonly = True
            self.status.set_text(f"No se pudo leer: {exc}")
        if b"\0" in raw[:8000]:
            self.readonly = True
            text = f"(archivo binario, {len(raw)} bytes; no se puede editar aquí)"
        else:
            text = raw.decode("utf-8", errors="replace")
        self.buffer.begin_not_undoable_action() if HAVE_GTKSOURCE else None
        self.buffer.set_text(text)
        self.buffer.end_not_undoable_action() if HAVE_GTKSOURCE else None
        self.buffer.set_modified(False)
        self.view.set_editable(not self.readonly)
        self.buffer.place_cursor(self.buffer.get_start_iter())
        self.update_status()

    def save(self):
        if self.readonly:
            return False
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, True)
        try:
            tmp = self.path + ".pytrol-tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(text)
            try:
                os.chmod(tmp, os.stat(self.path).st_mode & 0o7777)
            except OSError:
                pass
            os.replace(tmp, self.path)
        except OSError as exc:
            self.pane.app.message(f"No se pudo guardar {self.path}", str(exc))
            return False
        self.buffer.set_modified(False)
        self.update_status("Guardado")
        return True

    def is_modified(self):
        return self.buffer.get_modified()

    # ---- interfaz
    def apply_config(self, cfg):
        self.view.override_font(Pango.FontDescription(cfg["font"]))
        if HAVE_GTKSOURCE:
            dark = cfg.get("scheme") != "Claro"
            sm = GtkSource.StyleSchemeManager.get_default()
            names = ("oblivion", "solarized-dark", "cobalt", "classic") if dark else ("tango", "classic", "kate")
            for name in names:
                scheme = sm.get_scheme(name)
                if scheme:
                    self.buffer.set_style_scheme(scheme)
                    break

    def update_status(self, note=""):
        it = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        parts = [f"Línea {it.get_line() + 1}, col {it.get_line_offset() + 1}"]
        if self.readonly:
            parts.append("solo lectura")
        if note:
            parts.append(note)
        parts.append(self.path)
        self.status.set_text("  ·  ".join(parts))

    def on_key(self, _view, event):
        mask = Gtk.accelerator_get_default_mod_mask()
        state = event.state & mask
        key = Gdk.keyval_to_lower(event.keyval)
        if state == Gdk.ModifierType.CONTROL_MASK and key == Gdk.KEY_s:
            self.save()
            return True
        if state == Gdk.ModifierType.CONTROL_MASK and key == Gdk.KEY_w:
            self.pane.close_editor(self)
            return True
        if event.keyval == Gdk.KEY_Escape:
            self.pane.term.grab_focus()
            return True
        return False


class ProjectTree(Gtk.Box):
    """Árbol de carpetas y archivos del proyecto de un panel (cada división tiene el suyo)."""

    COL_NAME, COL_PATH, COL_IS_DIR, COL_ICON, COL_LOADED = range(5)

    def __init__(self, app, pane):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
        self.pane = pane
        self.root = None
        self.pinned = False
        self._monitors = {}
        self._refresh_id = None

        header = Gtk.Box(spacing=2)
        header.get_style_context().add_class("tree-header")
        self.label = Gtk.Label(xalign=0)
        self.label.set_ellipsize(Pango.EllipsizeMode.START)
        self.label.set_tooltip_text("")
        header.pack_start(self.label, True, True, 4)
        self.pin_btn = Gtk.ToggleButton()
        self.pin_btn.set_image(Gtk.Image.new_from_icon_name("view-pin-symbolic", Gtk.IconSize.MENU))
        self.pin_btn.set_relief(Gtk.ReliefStyle.NONE)
        self.pin_btn.set_tooltip_text("Fijar esta carpeta (no seguir al directorio del terminal)")
        self.pin_btn.connect("toggled", lambda b: self.set_pinned(b.get_active()))
        self.get_style_context().add_class("project-tree")
        for icon, tip, cb in (("window-close-symbolic", "Ocultar el árbol de este panel", self.hide_me),
                              ("go-up-symbolic", "Subir a la carpeta superior", self.go_up)):
            b = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.MENU)
            b.set_relief(Gtk.ReliefStyle.NONE)
            b.set_tooltip_text(tip)
            b.connect("clicked", lambda _b, f=cb: f())
            header.pack_end(b, False, False, 0)
        header.pack_end(self.pin_btn, False, False, 0)
        self.pack_start(header, False, False, 0)

        self.store = Gtk.TreeStore(str, str, bool, str, bool)
        self.view = Gtk.TreeView(model=self.store)
        self.view.set_headers_visible(False)
        self.view.set_enable_search(True)
        self.view.set_search_column(self.COL_NAME)
        col = Gtk.TreeViewColumn("Archivo")
        pix = Gtk.CellRendererPixbuf()
        txt = Gtk.CellRendererText()
        txt.set_property("ellipsize", Pango.EllipsizeMode.END)
        col.pack_start(pix, False)
        col.pack_start(txt, True)
        col.add_attribute(pix, "icon-name", self.COL_ICON)
        col.add_attribute(txt, "text", self.COL_NAME)
        self.view.append_column(col)
        self.view.connect("row-expanded", self.on_row_expanded)
        self.view.connect("row-activated", self.on_row_activated)
        self.view.connect("button-press-event", self.on_button)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.view)
        self.pack_start(sw, True, True, 0)

    # ---- raíz
    def set_root(self, path, force=False):
        if not path or (self.pinned and not force):
            return
        path = os.path.abspath(path)
        if path == self.root or not os.path.isdir(path):
            return
        self.root = path
        self.label.set_text(os.path.basename(path.rstrip("/")) or path)
        self.label.set_tooltip_text(path)
        self.rebuild()

    def hide_me(self):
        self.pane.set_tree_visible(False)

    def set_pinned(self, value):
        self.pinned = bool(value)
        if self.pin_btn.get_active() != self.pinned:
            self.pin_btn.set_active(self.pinned)

    def go_up(self):
        if self.root and os.path.dirname(self.root) != self.root:
            self.set_root(os.path.dirname(self.root), force=True)

    def choose_root(self):
        path = self.app.choose_folder("Carpeta del árbol")
        if path:
            self.set_root(path, force=True)

    # ---- contenido
    def _icon_for(self, name, is_dir):
        if is_dir:
            return "folder"
        ctype, _ = Gio.content_type_guess(name, None)
        return Gio.content_type_get_generic_icon_name(ctype) or "text-x-generic"

    def _populate(self, parent_iter, path):
        show_hidden = self.app.cfg.get("tree_show_hidden", False)
        try:
            entries = list(os.scandir(path))
        except OSError:
            return
        def key(e):
            try:
                d = e.is_dir(follow_symlinks=True)
            except OSError:
                d = False
            return (not d, e.name.casefold())
        for e in sorted(entries, key=key):
            if e.name.startswith(".") and not show_hidden:
                continue
            try:
                is_dir = e.is_dir(follow_symlinks=True)
            except OSError:
                is_dir = False
            it = self.store.append(parent_iter, [e.name, e.path, is_dir, self._icon_for(e.name, is_dir), False])
            if is_dir:
                self.store.append(it, ["…", "", False, "", False])  # marcador para poder expandir

    def rebuild(self):
        expanded = self._expanded_paths()
        self._clear_monitors()
        self.store.clear()
        if not self.root:
            return
        self._populate(None, self.root)
        self._watch(self.root)
        self._reexpand(None, expanded)

    def _expanded_paths(self):
        out = set()
        def walk(it):
            while it is not None:
                if self.store[it][self.COL_IS_DIR] and self.view.row_expanded(self.store.get_path(it)):
                    out.add(self.store[it][self.COL_PATH])
                    walk(self.store.iter_children(it))
                it = self.store.iter_next(it)
        walk(self.store.get_iter_first())
        return out

    def _reexpand(self, parent, expanded):
        it = self.store.iter_children(parent)
        while it is not None:
            if self.store[it][self.COL_IS_DIR] and self.store[it][self.COL_PATH] in expanded:
                self.view.expand_row(self.store.get_path(it), False)
                self._reexpand(it, expanded)
            it = self.store.iter_next(it)

    def on_row_expanded(self, _view, it, _path):
        if self.store[it][self.COL_LOADED]:
            return
        # Primero se añaden los hijos reales y después se quita el marcador «…»:
        # si la fila se quedara sin hijos un instante, GTK la contraería.
        placeholders = []
        child = self.store.iter_children(it)
        while child is not None:
            placeholders.append(child)
            child = self.store.iter_next(child)
        path = self.store[it][self.COL_PATH]
        self._populate(it, path)
        for ph in placeholders:
            self.store.remove(ph)
        self.store[it][self.COL_LOADED] = True
        self._watch(path)

    def refresh(self):
        self.rebuild()

    # ---- vigilancia de cambios
    def _watch(self, path):
        if path in self._monitors:
            return
        try:
            mon = Gio.File.new_for_path(path).monitor_directory(Gio.FileMonitorFlags.NONE, None)
            mon.connect("changed", self._on_changed)
            self._monitors[path] = mon
        except GLib.Error:
            pass

    def _clear_monitors(self):
        for mon in self._monitors.values():
            mon.cancel()
        self._monitors.clear()

    def _on_changed(self, *_):
        if self._refresh_id:
            GLib.source_remove(self._refresh_id)
        self._refresh_id = GLib.timeout_add(400, self._deferred_refresh)

    def _deferred_refresh(self):
        self._refresh_id = None
        self.rebuild()
        return False

    # ---- acciones
    def _row_at(self, treepath):
        it = self.store.get_iter(treepath)
        return self.store[it][self.COL_PATH], self.store[it][self.COL_IS_DIR]

    def on_row_activated(self, _view, treepath, _col):
        path, is_dir = self._row_at(treepath)
        if not path:
            return
        if is_dir:
            self.app.terminal_cd(path, self.pane)
        else:
            self.pane.open_file(path)

    def open_with_default(self, path):
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(path).get_uri(), None)
        except GLib.Error as exc:
            print(f"No se pudo abrir {path}: {exc}", file=sys.stderr)

    def on_button(self, view, event):
        if event.button != 3:
            return False
        hit = view.get_path_at_pos(int(event.x), int(event.y))
        if hit:
            view.set_cursor(hit[0], None, False)
            path, is_dir = self._row_at(hit[0])
        else:
            path, is_dir = self.root, True
        self.show_context_menu(path, is_dir, event)
        return True

    def show_context_menu(self, path, is_dir, event):
        menu = Gtk.Menu()
        def add(label, cb, sensitive=True):
            it = Gtk.MenuItem(label=label)
            it.set_sensitive(sensitive)
            it.connect("activate", lambda *_: cb())
            menu.append(it)
        folder = path if is_dir else os.path.dirname(path)
        if is_dir:
            add("Ir a esta carpeta en el terminal", lambda: self.app.terminal_cd(path, self.pane))
            add("Hacer raíz del árbol", lambda: self.set_root(path, force=True))
            add("Abrir como proyecto de este panel", lambda: self.app.open_project_in(self.pane, path))
        else:
            add("Abrir en el editor de este panel", lambda: self.pane.open_file(path))
            add("Abrir con la aplicación predeterminada", lambda: self.open_with_default(path))
            add("Ir a su carpeta en el terminal", lambda: self.app.terminal_cd(folder, self.pane))
        add("Insertar ruta en el terminal", lambda: self.app.terminal_insert(path, self.pane))
        add("Copiar ruta", lambda: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(path, -1))
        menu.append(Gtk.SeparatorMenuItem())
        add("Nuevo panel aquí (vertical)", lambda: self.app.split(self.pane, Gtk.Orientation.HORIZONTAL, cwd=folder))
        add("Nuevo panel aquí (horizontal)", lambda: self.app.split(self.pane, Gtk.Orientation.VERTICAL, cwd=folder))
        add("Nueva pestaña aquí", lambda: self.app.new_tab(cwd=folder))
        menu.append(Gtk.SeparatorMenuItem())
        hidden = Gtk.CheckMenuItem(label="Mostrar archivos ocultos")
        hidden.set_active(self.app.cfg.get("tree_show_hidden", False))
        hidden.connect("toggled", lambda w: self.app.set_tree_hidden(w.get_active()))
        menu.append(hidden)
        add("Actualizar", self.refresh)
        add("Elegir carpeta…", self.choose_root)
        add("Ocultar el árbol de este panel", self.hide_me)
        menu.show_all()
        menu.popup_at_pointer(event)


class Tab(Gtk.Box):
    """Página del notebook: raíz del árbol de paneles."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.focused = None
        self.label = Gtk.Label(label="Shell")
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.label.set_max_width_chars(24)

    def panes(self):
        out = []

        def walk(w):
            if isinstance(w, Pane):
                out.append(w)
            elif isinstance(w, Gtk.Container):
                for c in w.get_children():
                    walk(c)
        walk(self)
        return out

    def root(self):
        kids = self.get_children()
        return kids[0] if kids else None


# ---------------------------------------------------------------- ventana principal
class Pytrol(Gtk.Window):
    def __init__(self):
        super().__init__(title=APP_TITLE)
        self.cfg = load_config()
        w, h = self.cfg.get("window_size", [1000, 620])
        self.set_default_size(int(w), int(h))
        self.set_icon_name(APP_ID)
        GLib.set_prgname(APP_ID)
        self._install_css()

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.vbox)
        self.menubar = None
        self.build_menubar()

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.notebook.set_show_border(False)
        self.notebook.connect("switch-page", self.on_switch_page)
        self.vbox.pack_start(self.notebook, True, True, 0)

        self.connect("key-press-event", self.on_key)
        self.connect("delete-event", self.on_delete_event)
        self.connect("destroy", self.on_destroy)
        self.connect("size-allocate", self._remember_size)

        self._quitting = False
        self._session_dirty = False
        restored = self.cfg.get("restore_session", True) and self.restore_session()
        if not restored:
            self.new_tab()
        self.show_all()
        self.menubar.set_visible(self.cfg["show_menubar"])
        self.apply_tree_visibility()

        # Guardado periódico de la sesión (protege ante cierres bruscos)
        GLib.timeout_add_seconds(SESSION_SAVE_SECONDS, self._periodic_save)
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            try:
                GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, self._on_unix_signal)
            except (AttributeError, ValueError):
                pass

    def _install_css(self):
        css = Gtk.CssProvider()
        css.load_from_data(b"""
            .pane-header { background: #2d2d2d; color: #bbbbbb; font-size: 0.85em;
                           padding: 1px 6px; border-bottom: 1px solid #444; }
            .pane-header.focused { background: #3b5a8a; color: #ffffff; }
            .tree-header { background: #2d2d2d; color: #dddddd; font-size: 0.85em;
                           border-bottom: 1px solid #444; }
            .tree-header button { padding: 0 2px; min-height: 18px; min-width: 18px; }
            .project-tree treeview { background-color: #232323; color: #d8d8d8; }
            .project-tree treeview:selected { background-color: #3b5a8a; color: #ffffff; }
            .project-tree scrolledwindow { border-right: 1px solid #444; }
            .editor-status { background: #2d2d2d; color: #bbbbbb; font-size: 0.8em; padding: 1px 6px; }
            .editor-tabs tab { padding: 1px 6px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    # ---------------------------------------------------------- árboles de proyecto
    def all_panes(self):
        for i in range(self.notebook.get_n_pages()):
            yield from self.notebook.get_nth_page(i).panes()

    def apply_tree_visibility(self):
        for p in self.all_panes():
            p.set_tree_visible(p.tree_visible)

    def toggle_tree(self):
        """Muestra u oculta los árboles de todos los paneles (y olvida ajustes por panel)."""
        self.cfg["show_tree"] = not self.cfg.get("show_tree", True)
        for p in self.all_panes():
            p.set_tree_visible(None)
        save_config(self.cfg)

    def set_tree_hidden(self, value):
        self.cfg["tree_show_hidden"] = bool(value)
        save_config(self.cfg)
        for p in self.all_panes():
            p.tree.rebuild()

    def terminal_cd(self, path, pane=None):
        pane = pane or self.current_pane()
        if pane is None or not path:
            return
        pane.change_dir(path, clear=False)
        pane.term.grab_focus()

    def terminal_insert(self, path, pane=None):
        pane = pane or self.current_pane()
        if pane is None or not path:
            return
        pane.term.feed_child((shlex.quote(path) + " ").encode())
        pane.term.grab_focus()

    def _remember_size(self, _w, alloc):
        if not (self.get_window() and self.get_window().get_state() & Gdk.WindowState.MAXIMIZED):
            self.cfg["window_size"] = [alloc.width, alloc.height]

    # ---------------------------------------------------------- sesión
    def _serialize_widget(self, w):
        if isinstance(w, Pane):
            node = {"type": "pane", "cwd": w.cwd_or_last()}
            if w.project_root:
                node["project"] = w.project_root
            if w.tree_visible is not None:
                node["tree"] = w.tree_visible
            node["tree_width"] = w.body.get_position()
            files = [e.path for e in w.editors()]
            if files:
                node["files"] = files
                node["editor_height"] = w.vsplit.get_position()
            if self.cfg.get("restore_scrollback", True):
                text = w.scrollback_text(int(self.cfg.get("restore_scrollback_lines", 5000)))
                if text:
                    node["screen"] = text
            return node
        if isinstance(w, Gtk.Paned):
            alloc = w.get_allocation()
            size = alloc.width if w.get_orientation() == Gtk.Orientation.HORIZONTAL else alloc.height
            frac = (w.get_position() / size) if size > 1 else getattr(w, "fraction", 0.5)
            return {"type": "split",
                    "orientation": "h" if w.get_orientation() == Gtk.Orientation.HORIZONTAL else "v",
                    "fraction": round(min(0.95, max(0.05, frac)), 3),
                    "a": self._serialize_widget(w.get_child1()),
                    "b": self._serialize_widget(w.get_child2())}
        return None

    def session_state(self):
        tabs = []
        for i in range(self.notebook.get_n_pages()):
            tab = self.notebook.get_nth_page(i)
            root = tab.root()
            if root is None:
                continue
            tabs.append({"layout": self._serialize_widget(root),
                         "focused": tab.panes().index(tab.focused) if tab.focused in tab.panes() else 0})
        return {"version": 1, "tabs": tabs, "current": max(0, self.notebook.get_current_page()),
                "window_size": self.cfg.get("window_size")}

    def save_session(self, *_):
        if self.notebook.get_n_pages() == 0:
            return
        write_session(self.session_state())
        self._session_dirty = False

    def mark_session_dirty(self):
        self._session_dirty = True

    def _periodic_save(self):
        # Las carpetas cambian sin aviso (cd en el shell), así que guardamos siempre.
        self.save_session()
        return True

    def _build_widget(self, node):
        if not node:
            return Pane(self)
        if node.get("type") == "pane":
            text = node.get("screen") if self.cfg.get("restore_scrollback", True) else None
            pane = Pane(self, node.get("cwd"), restore_text=text, project_root=node.get("project"))
            pane.tree_visible = node.get("tree")
            if node.get("tree_width"):
                pane.body.set_position(int(node["tree_width"]))
            files = [f for f in node.get("files", []) if os.path.isfile(f)]
            if files:
                if node.get("editor_height"):
                    pane.vsplit.set_position(int(node["editor_height"]))
                GLib.idle_add(self._reopen_files, pane, files)
            return pane
        orient = Gtk.Orientation.HORIZONTAL if node.get("orientation") == "h" else Gtk.Orientation.VERTICAL
        paned = SplitPaned(orient, float(node.get("fraction", 0.5)))
        paned.pack1(self._build_widget(node.get("a")), True, False)
        paned.pack2(self._build_widget(node.get("b")), True, False)
        return paned

    def _reopen_files(self, pane, files):
        for f in files:
            pane.open_file(f)
        pane.term.grab_focus()
        return False

    def restore_session(self):
        data = load_session()
        if not data:
            return False
        try:
            for tdata in data["tabs"]:
                tab = self.new_tab(root=self._build_widget(tdata.get("layout")))
                tab.show_all()
                panes = tab.panes()
                idx = int(tdata.get("focused", 0))
                tab.focused = panes[idx] if 0 <= idx < len(panes) else panes[0]
                self.update_headers(tab)
            cur = int(data.get("current", 0))
            if 0 <= cur < self.notebook.get_n_pages():
                self.notebook.set_current_page(cur)
            return self.notebook.get_n_pages() > 0
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            print(f"Sesión anterior no válida, se ignora: {exc}", file=sys.stderr)
            return False

    # ---------------------------------------------------------- cierre seguro
    def _count_panes(self):
        return sum(len(self.notebook.get_nth_page(i).panes()) for i in range(self.notebook.get_n_pages()))

    def _ask(self, title, text, ok_label):
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                buttons=Gtk.ButtonsType.NONE, text=title)
        dlg.format_secondary_text(text)
        dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dlg.add_button(ok_label, Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.CANCEL)
        resp = dlg.run()
        dlg.destroy()
        return resp == Gtk.ResponseType.OK

    def confirm_quit(self):
        """Pide confirmación tantas veces como diga la configuración (por defecto 2)."""
        times = int(self.cfg.get("confirm_close", 2))
        unsaved = [f for p in self.all_panes() for f in p.unsaved_files()]
        if unsaved and not self._ask("Hay archivos sin guardar",
                                     "\n".join(os.path.basename(f) for f in unsaved[:8])
                                     + ("\n…" if len(unsaved) > 8 else "")
                                     + "\n\nSi cierras ahora, esos cambios se perderán.",
                                     "Cerrar sin guardar"):
            return False
        n_tabs, n_panes = self.notebook.get_n_pages(), self._count_panes()
        prompts = [
            ("¿Cerrar Pytrol?", f"Hay {n_tabs} pestaña(s) y {n_panes} panel(es) abiertos. "
                                "La sesión se guardará y se restaurará al volver a abrir.", "Cerrar"),
            ("¿Seguro que quieres cerrar?", "Segunda confirmación: los procesos que estén "
                                            "ejecutándose en los paneles se terminarán.", "Sí, cerrar"),
        ]
        for i in range(min(times, len(prompts))):
            if not self._ask(*prompts[i]):
                return False
        return True

    def on_delete_event(self, *_):
        if self._quitting:
            return False
        if not self.confirm_quit():
            return True  # cancelar el cierre
        self._quitting = True
        self.save_session()
        return False

    def _on_unix_signal(self, *_):
        self.save_session()
        save_config(self.cfg)
        Gtk.main_quit()
        return False

    # ---------------------------------------------------------- menú
    def _item(self, action_id, label=None):
        it = Gtk.MenuItem()
        al = Gtk.AccelLabel(label=label or ACTION_LABELS[action_id], xalign=0)
        accel = self.cfg["shortcuts"].get(action_id, "")
        if accel:
            key, mods = Gtk.accelerator_parse(accel)
            al.set_accel(key, mods)
        it.add(al)
        it.connect("activate", lambda *_: self.do_action(action_id))
        return it

    def _submenu(self, title, items):
        top = Gtk.MenuItem(label=title)
        menu = Gtk.Menu()
        for it in items:
            menu.append(it if it is not None else Gtk.SeparatorMenuItem())
        top.set_submenu(menu)
        return top

    def build_menubar(self):
        if self.menubar is not None:
            visible = self.menubar.get_visible()
            self.vbox.remove(self.menubar)
        else:
            visible = self.cfg["show_menubar"]
        mb = Gtk.MenuBar()

        mb.append(self._submenu("Archivo", [
            self._item("new_tab"), self._item("open_project_tab"), None,
            self._item("open_file"), self._item("save_file"), self._item("close_file"), None,
            self._item("close_tab"), None, self._item("quit")]))

        layouts = Gtk.Menu()
        for idx, (label, _r, _c) in enumerate(LAYOUTS):
            it = Gtk.MenuItem(label=label)
            it.connect("activate", lambda _w, i=idx: self.apply_layout(i))
            layouts.append(it)
        layout_item = Gtk.MenuItem(label="Diseño de paneles")
        layout_item.set_submenu(layouts)

        recent = Gtk.Menu()
        for path in self.cfg["recent_projects"]:
            it = Gtk.MenuItem(label=path)
            it.connect("activate", lambda _w, p=path: self.open_project_in(self.current_pane(), p))
            recent.append(it)
        if self.cfg["recent_projects"]:
            recent.append(Gtk.SeparatorMenuItem())
            clear = Gtk.MenuItem(label="Vaciar lista")
            clear.connect("activate", self.clear_recent)
            recent.append(clear)
        else:
            empty = Gtk.MenuItem(label="(sin proyectos recientes)")
            empty.set_sensitive(False)
            recent.append(empty)
        recent_item = Gtk.MenuItem(label="Proyectos recientes")
        recent_item.set_submenu(recent)

        mb.append(self._submenu("Paneles", [
            self._item("split_v"), self._item("split_h"), layout_item, self._item("close_pane"), None,
            self._item("focus_left"), self._item("focus_right"),
            self._item("focus_up"), self._item("focus_down")]))

        mb.append(self._submenu("Proyectos", [
            self._item("open_project"), self._item("open_project_split_v"),
            self._item("open_project_split_h"), self._item("open_project_tab"), None,
            recent_item, None,
            self._item("toggle_tree"), self._item("pin_tree"), self._item("tree_show_hidden")]))

        mb.append(self._submenu("Edición", [
            self._item("copy"), self._item("paste"), self._item("select_all"), None,
            self._item("clear")]))

        mb.append(self._submenu("Ver", [
            self._item("prev_tab"), self._item("next_tab"),
            self._item("move_tab_left"), self._item("move_tab_right"), None,
            self._item("zoom_in"), self._item("zoom_out"), self._item("zoom_reset"), None,
            self._item("toggle_tree"), self._item("toggle_menubar"), self._item("fullscreen")]))

        mb.append(self._submenu("Preferencias", [self._item("preferences")]))

        about = Gtk.MenuItem(label="Acerca de Pytrol")
        about.connect("activate", self.show_about)
        mb.append(self._submenu("Ayuda", [about]))

        mb.show_all()
        mb.set_no_show_all(True)
        mb.set_visible(visible)
        self.vbox.pack_start(mb, False, False, 0)
        self.vbox.reorder_child(mb, 0)
        self.menubar = mb

    # ---------------------------------------------------------- pestañas
    def current_tab(self):
        page = self.notebook.get_current_page()
        return self.notebook.get_nth_page(page) if page >= 0 else None

    def current_pane(self):
        tab = self.current_tab()
        if tab is None:
            return None
        if tab.focused is None or tab.focused not in tab.panes():
            panes = tab.panes()
            tab.focused = panes[0] if panes else None
        return tab.focused

    def new_tab(self, cwd=None, inherit_cwd=True, root=None):
        """Nueva pestaña con un panel, o con un árbol de paneles ya construido (`root`)."""
        if root is None:
            if cwd is None and inherit_cwd and self.current_pane():
                cwd = self.current_pane().cwd()
            root = Pane(self, cwd)
        tab = Tab()
        tab.pack_start(root, True, True, 0)
        panes = tab.panes()
        tab.focused = panes[0] if panes else None
        pane = tab.focused

        close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_focus_on_click(False)
        close.connect("clicked", lambda *_: self.close_tab(tab))
        box = Gtk.Box(spacing=4)
        box.pack_start(tab.label, True, True, 0)
        box.pack_start(close, False, False, 0)
        box.show_all()

        idx = self.notebook.append_page(tab, box)
        self.notebook.set_tab_reorderable(tab, True)
        tab.show_all()
        for p in panes:
            p.set_tree_visible(p.tree_visible)
        self.notebook.set_current_page(idx)
        pane.term.grab_focus()
        self.update_tabs_visibility()
        self.update_headers(tab)
        self.save_session()
        return tab

    def close_tab(self, tab, force=False):
        if self._quitting:
            return
        if not force:
            if self.notebook.get_n_pages() == 1:
                # Última pestaña: cerrar la app, con la confirmación habitual.
                self.quit()
                return
            if len(tab.panes()) > 1 and not self._ask(
                    "¿Cerrar esta pestaña?", f"Tiene {len(tab.panes())} paneles abiertos.", "Cerrar pestaña"):
                return
        idx = self.notebook.page_num(tab)
        if idx >= 0:
            self.notebook.remove_page(idx)
            tab.destroy()
        if self.notebook.get_n_pages() == 0:
            self.quit(force=True)
        else:
            self.save_session()
            self.update_tabs_visibility()
            pane = self.current_pane()
            if pane:
                pane.term.grab_focus()

    def update_tabs_visibility(self):
        self.notebook.set_show_tabs(self.notebook.get_n_pages() > 1)

    def cycle(self, step):
        n = self.notebook.get_n_pages()
        if n:
            self.notebook.set_current_page((self.notebook.get_current_page() + step) % n)

    def move_tab(self, step):
        tab = self.current_tab()
        idx = self.notebook.page_num(tab)
        new = max(0, min(self.notebook.get_n_pages() - 1, idx + step))
        self.notebook.reorder_child(tab, new)

    # ---------------------------------------------------------- paneles
    def split(self, pane, orientation, cwd=None):
        """Divide `pane` en dos; devuelve el panel nuevo."""
        tab = self.current_tab()
        new_pane = Pane(self, cwd if cwd is not None else pane.cwd())
        parent = pane.get_parent()
        paned = SplitPaned(orientation, 0.5)
        SplitPaned.replace_child(parent, pane, paned)
        paned.pack1(pane, True, False)
        paned.pack2(new_pane, True, False)
        paned.show_all()
        new_pane.set_tree_visible(None)
        self.update_headers(tab)
        new_pane.term.grab_focus()
        self.save_session()
        return new_pane

    def close_pane(self, pane, from_exit=False):
        if self._quitting:
            return  # la ventana se está destruyendo: no reescribir la sesión panel a panel
        tab = pane.get_ancestor(Tab)
        if tab is None:
            return
        if pane.unsaved_files() and not self._ask(
                "Hay archivos sin guardar en este panel",
                "\n".join(os.path.basename(f) for f in pane.unsaved_files()[:8]) + "\n\nSe perderán los cambios.",
                "Cerrar sin guardar"):
            return
        parent = pane.get_parent()
        if isinstance(parent, Gtk.Paned):
            sibling = parent.get_child2() if parent.get_child1() is pane else parent.get_child1()
            parent.remove(pane)
            parent.remove(sibling)
            SplitPaned.replace_child(parent.get_parent(), parent, sibling)
            pane.destroy()
            parent.destroy()
            panes = tab.panes()
            tab.focused = panes[0] if panes else None
            self.update_headers(tab)
            if tab.focused:
                tab.focused.term.grab_focus()
            self.save_session()
        else:
            # El shell terminó por sí solo (exit): no pedimos confirmación.
            self.close_tab(tab, force=from_exit)

    def apply_layout(self, idx):
        """Aplica un diseño predefinido: en la pestaña actual si tiene un solo panel, si no en una nueva."""
        _label, rows, cols = LAYOUTS[idx]
        tab = self.current_tab()
        if tab is None or len(tab.panes()) != 1:
            tab = self.new_tab()
        first = tab.panes()[0]
        cwd = first.cwd()
        tab.remove(first)
        panes = [first] + [Pane(self, cwd) for _ in range(rows * cols - 1)]
        rows_widgets = []
        for r in range(rows):
            rows_widgets.append(self._nest(panes[r * cols:(r + 1) * cols], Gtk.Orientation.HORIZONTAL))
        root = self._nest(rows_widgets, Gtk.Orientation.VERTICAL)
        tab.pack_start(root, True, True, 0)
        tab.show_all()
        for p in panes:
            p.set_tree_visible(p.tree_visible)
        tab.focused = first
        self.update_headers(tab)
        first.term.grab_focus()
        self.save_session()

    def _nest(self, widgets, orientation):
        if len(widgets) == 1:
            return widgets[0]
        paned = SplitPaned(orientation, 1.0 / len(widgets))
        paned.pack1(widgets[0], True, False)
        paned.pack2(self._nest(widgets[1:], orientation), True, False)
        return paned

    def focus_direction(self, dx, dy):
        tab = self.current_tab()
        cur = self.current_pane()
        if not tab or not cur:
            return
        def center(w):
            a = w.get_allocation()
            res = w.translate_coordinates(tab, 0, 0)
            if not res:
                return (a.x + a.width / 2, a.y + a.height / 2)
            x, y = res[-2], res[-1]
            return (x + a.width / 2, y + a.height / 2)
        cx, cy = center(cur)
        best, best_d = None, None
        for p in tab.panes():
            if p is cur:
                continue
            px, py = center(p)
            proj = (px - cx) * dx + (py - cy) * dy
            if proj <= 0:
                continue
            ortho = abs((px - cx) * dy) + abs((py - cy) * dx)
            d = proj + 3 * ortho
            if best_d is None or d < best_d:
                best, best_d = p, d
        if best:
            best.term.grab_focus()

    def update_headers(self, tab):
        panes = tab.panes()
        show = self.cfg["show_pane_headers"] and len(panes) > 1
        for p in panes:
            p.header.set_text(p.cwd() or p.title())
            p.header.set_visible(show)
            ctx = p.header.get_style_context()
            if p is tab.focused:
                ctx.add_class("focused")
            else:
                ctx.remove_class("focused")
        self.refresh_tab_label(tab)

    def refresh_tab_label(self, tab):
        panes = tab.panes()
        if not panes:
            return
        focused = tab.focused or panes[0]
        title = focused.title()
        if len(panes) > 1:
            title = f"[{len(panes)}] {title}"
        tab.label.set_text(title)
        if tab is self.current_tab():
            self.set_title(f"{title} - {APP_TITLE}")

    # ---------------------------------------------------------- proyectos
    def choose_file(self, pane):
        dlg = Gtk.FileChooserDialog(title="Abrir archivo en el editor", parent=self,
                                    action=Gtk.FileChooserAction.OPEN)
        dlg.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Abrir", Gtk.ResponseType.OK)
        start = pane.tree_root() if pane else None
        if start and os.path.isdir(start):
            dlg.set_current_folder(start)
        path = dlg.get_filename() if dlg.run() == Gtk.ResponseType.OK else None
        dlg.destroy()
        return path

    def ask_save(self, name):
        """Devuelve 'save', 'discard' o 'cancel'."""
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                buttons=Gtk.ButtonsType.NONE, text=f"¿Guardar los cambios de «{name}»?")
        dlg.format_secondary_text("Si no los guardas, se perderán.")
        dlg.add_button("Descartar", 1)
        dlg.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dlg.add_button("Guardar", 2)
        dlg.set_default_response(2)
        resp = dlg.run()
        dlg.destroy()
        return {1: "discard", 2: "save"}.get(resp, "cancel")

    def message(self, title, text):
        dlg = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                buttons=Gtk.ButtonsType.OK, text=title)
        dlg.format_secondary_text(text)
        dlg.run()
        dlg.destroy()

    def choose_folder(self, title="Abrir proyecto"):
        dlg = Gtk.FileChooserDialog(title=title, parent=self,
                                    action=Gtk.FileChooserAction.SELECT_FOLDER)
        dlg.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Abrir", Gtk.ResponseType.OK)
        cur = self.current_pane()
        if cur and cur.cwd():
            dlg.set_current_folder(cur.cwd())
        path = dlg.get_filename() if dlg.run() == Gtk.ResponseType.OK else None
        dlg.destroy()
        return path

    def remember_project(self, path):
        rp = [p for p in self.cfg["recent_projects"] if p != path]
        rp.insert(0, path)
        self.cfg["recent_projects"] = rp[:12]
        save_config(self.cfg)
        self.build_menubar()

    def open_project_in(self, pane, path):
        if pane is None or not path:
            return
        pane.change_dir(path)
        pane.project_root = path
        self.remember_project(path)
        self.update_headers(self.current_tab())
        pane.tree.set_root(path, force=True)
        pane.term.grab_focus()

    def open_project_dialog(self, mode):
        path = self.choose_folder()
        if not path:
            return
        if mode == "here":
            self.open_project_in(self.current_pane(), path)
        elif mode == "tab":
            tab = self.new_tab(cwd=path)
            new_pane = tab.panes()[0]
            new_pane.project_root = path
            self.remember_project(path)
            new_pane.tree.set_root(path, force=True)
        else:
            orient = Gtk.Orientation.HORIZONTAL if mode == "split_v" else Gtk.Orientation.VERTICAL
            new_pane = self.split(self.current_pane(), orient, cwd=path)
            new_pane.project_root = path
            self.remember_project(path)
            new_pane.tree.set_root(path, force=True)

    def clear_recent(self, *_):
        self.cfg["recent_projects"] = []
        save_config(self.cfg)
        self.build_menubar()

    # ---------------------------------------------------------- señales
    def on_pane_focus(self, pane):
        tab = pane.get_ancestor(Tab)
        if tab is not None:
            tab.focused = pane
            self.update_headers(tab)
        return False

    def on_title_changed(self, pane):
        tab = pane.get_ancestor(Tab)
        if tab is not None:
            self.update_headers(tab)
            # Sin proyecto explícito, el árbol del panel sigue al directorio del shell
            if not pane.project_root:
                pane.sync_tree()

    def on_switch_page(self, _nb, tab, _idx):
        GLib.idle_add(self.refresh_tab_label, tab)
        GLib.idle_add(lambda: (tab.focused or tab.panes()[0]).term.grab_focus() if tab.panes() else None)

    def on_button(self, pane, event):
        if event.button == 3:
            self.show_context_menu(pane, event)
            return True
        return False

    def on_key(self, _win, event):
        mask = Gtk.accelerator_get_default_mod_mask()
        state = event.state & mask
        keyval = Gdk.keyval_to_lower(event.keyval)
        for action_id, accel in self.cfg["shortcuts"].items():
            if not accel:
                continue
            key, mods = Gtk.accelerator_parse(accel)
            if key and Gdk.keyval_to_lower(key) == keyval and mods == state:
                self.do_action(action_id)
                return True
            # Alias para teclas del teclado numérico y '=' como '+'
            if action_id == "zoom_in" and state == mods and event.keyval in (Gdk.KEY_equal, Gdk.KEY_KP_Add):
                self.do_action(action_id); return True
            if action_id == "zoom_out" and state == mods and event.keyval == Gdk.KEY_KP_Subtract:
                self.do_action(action_id); return True
        # Shift+Insert pega en el terminal (como en la mayoría de los terminales)
        if state == Gdk.ModifierType.SHIFT_MASK and event.keyval in (Gdk.KEY_Insert, Gdk.KEY_KP_Insert) \
                and isinstance(self.get_focus(), Vte.Terminal):
            self.do_action("paste"); return True
        return False

    def edit_action(self, action_id, term):
        """Copiar/pegar/seleccionar sobre el widget con foco: editor, campo de texto o terminal."""
        fw = self.get_focus()
        if isinstance(fw, Gtk.TextView):
            if action_id == "copy": fw.emit("copy-clipboard")
            elif action_id == "paste": fw.emit("paste-clipboard")
            else: fw.emit("select-all", True)
            return
        if isinstance(fw, Gtk.Editable):
            if action_id == "copy": fw.copy_clipboard()
            elif action_id == "paste": fw.paste_clipboard()
            else: fw.select_region(0, -1)
            return
        if term is None:
            return
        if action_id == "copy": term.copy_clipboard_format(Vte.Format.TEXT)
        elif action_id == "paste": term.paste_clipboard()
        else: term.select_all()

    def on_destroy(self, *_):
        if not self._quitting and self.notebook.get_n_pages() > 0:
            self.save_session()  # cierre no previsto por quit(): guardar ahora
        self._quitting = True
        save_config(self.cfg)
        Gtk.main_quit()

    # ---------------------------------------------------------- acciones
    def do_action(self, action_id):
        pane = self.current_pane()
        term = pane.term if pane else None
        a = action_id
        if a == "new_tab": self.new_tab()
        elif a == "close_tab": self.close_tab(self.current_tab())
        elif a == "next_tab": self.cycle(1)
        elif a == "prev_tab": self.cycle(-1)
        elif a == "move_tab_left": self.move_tab(-1)
        elif a == "move_tab_right": self.move_tab(1)
        elif a == "quit": self.quit()
        elif a == "split_h" and pane: self.split(pane, Gtk.Orientation.VERTICAL)
        elif a == "split_v" and pane: self.split(pane, Gtk.Orientation.HORIZONTAL)
        elif a == "close_pane" and pane: self.close_pane(pane)
        elif a == "focus_left": self.focus_direction(-1, 0)
        elif a == "focus_right": self.focus_direction(1, 0)
        elif a == "focus_up": self.focus_direction(0, -1)
        elif a == "focus_down": self.focus_direction(0, 1)
        elif a == "open_project": self.open_project_dialog("here")
        elif a == "open_project_split_v": self.open_project_dialog("split_v")
        elif a == "open_project_split_h": self.open_project_dialog("split_h")
        elif a == "open_project_tab": self.open_project_dialog("tab")
        elif a in ("copy", "paste", "select_all"): self.edit_action(a, term)
        elif a == "clear" and term: term.reset(True, True)
        elif a == "zoom_in" and term: self.zoom(term, 1.1)
        elif a == "zoom_out" and term: self.zoom(term, 1 / 1.1)
        elif a == "zoom_reset" and term: term.set_font_scale(1.0)
        elif a == "toggle_menubar": self.toggle_menubar()
        elif a == "toggle_tree": self.toggle_tree()
        elif a == "open_file" and pane:
            path = self.choose_file(pane)
            if path:
                pane.open_file(path)
        elif a == "save_file" and pane and pane.current_editor(): pane.current_editor().save()
        elif a == "close_file" and pane and pane.current_editor(): pane.close_editor(pane.current_editor())
        elif a == "pin_tree" and pane: pane.tree.set_pinned(not pane.tree.pinned)
        elif a == "tree_show_hidden": self.set_tree_hidden(not self.cfg.get("tree_show_hidden", False))
        elif a == "fullscreen": self.toggle_fullscreen()
        elif a == "preferences": self.show_preferences()

    def zoom(self, term, factor):
        term.set_font_scale(max(0.4, min(4.0, term.get_font_scale() * factor)))

    def toggle_menubar(self):
        self.cfg["show_menubar"] = not self.menubar.get_visible()
        self.menubar.set_visible(self.cfg["show_menubar"])
        save_config(self.cfg)

    def toggle_fullscreen(self):
        if self.get_window().get_state() & Gdk.WindowState.FULLSCREEN:
            self.unfullscreen()
        else:
            self.fullscreen()

    def quit(self, force=False):
        if self._quitting:
            return
        if not force and not self.confirm_quit():
            return
        self._quitting = True
        self.save_session()
        self.destroy()

    def show_context_menu(self, pane, event):
        menu = Gtk.Menu()
        for action_id in ("copy", "paste", None, "split_v", "split_h", "close_pane", None,
                          "open_project", "new_tab", "close_tab", None, "clear", "preferences"):
            if action_id is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue
            it = self._item(action_id)
            if action_id == "copy":
                it.set_sensitive(pane.term.get_has_selection())
            menu.append(it)
        menu.show_all()
        menu.popup_at_pointer(event)

    def show_about(self, *_):
        dlg = Gtk.AboutDialog(transient_for=self, program_name=APP_TITLE, version="0.6.1",
                              comments="Advanced Python Terminal: Power, Speed, Control.\nPaneles, proyectos y pestañas en un solo lugar.",
                              logo_icon_name=APP_ID, license_type=Gtk.License.MIT_X11)
        dlg.run()
        dlg.destroy()

    # ---------------------------------------------------------- preferencias
    def show_preferences(self):
        dlg = PreferencesDialog(self)
        if dlg.run() == Gtk.ResponseType.OK:
            dlg.apply_to(self.cfg)
            save_config(self.cfg)
            self.apply_config_everywhere()
        dlg.destroy()

    def apply_config_everywhere(self):
        for i in range(self.notebook.get_n_pages()):
            tab = self.notebook.get_nth_page(i)
            for p in tab.panes():
                p.apply_config(self.cfg)
            self.update_headers(tab)
        self.build_menubar()
        for p in self.all_panes():
            p.set_tree_visible(None)
            p.tree.rebuild()


class PreferencesDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Preferencias", transient_for=parent, modal=True)
        self.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Aceptar", Gtk.ResponseType.OK)
        self.set_default_size(560, 480)
        cfg = parent.cfg
        nb = Gtk.Notebook()
        self.get_content_area().pack_start(nb, True, True, 0)

        # --- General
        grid = Gtk.Grid(row_spacing=8, column_spacing=12, margin=12)
        row = 0

        def add(label, widget):
            nonlocal row
            grid.attach(Gtk.Label(label=label, xalign=1), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
            widget.set_hexpand(True)
            row += 1

        self.font = Gtk.FontButton(font=cfg["font"])
        add("Fuente", self.font)
        self.scheme = Gtk.ComboBoxText()
        for name in SCHEMES:
            self.scheme.append_text(name)
        self.scheme.set_active(list(SCHEMES).index(cfg["scheme"]) if cfg["scheme"] in SCHEMES else 0)
        add("Esquema de colores", self.scheme)
        self.cursor = Gtk.ComboBoxText()
        for name in CURSOR_SHAPES:
            self.cursor.append_text(name)
        self.cursor.set_active(list(CURSOR_SHAPES).index(cfg["cursor_shape"])
                               if cfg["cursor_shape"] in CURSOR_SHAPES else 0)
        add("Forma del cursor", self.cursor)
        self.blink = Gtk.CheckButton(label="Cursor parpadeante", active=cfg["cursor_blink"])
        add("", self.blink)
        self.scrollback = Gtk.SpinButton.new_with_range(100, 1_000_000, 100)
        self.scrollback.set_value(int(cfg["scrollback"]))
        add("Líneas de historial", self.scrollback)
        self.shell = Gtk.Entry(text=cfg["shell"], placeholder_text=host_shell())
        add("Comando del shell", self.shell)
        self.menubar = Gtk.CheckButton(label="Mostrar barra de menú", active=cfg["show_menubar"])
        add("", self.menubar)
        self.headers = Gtk.CheckButton(label="Mostrar cabecera con el proyecto en cada panel",
                                       active=cfg["show_pane_headers"])
        add("", self.headers)
        self.show_tree = Gtk.CheckButton(label="Mostrar el árbol del proyecto al iniciar",
                                         active=cfg.get("show_tree", True))
        add("", self.show_tree)
        self.askpass = Gtk.CheckButton(
            label="Pedir la contraseña en una ventana cuando sudo o ssh no tienen terminal",
            active=cfg.get("askpass", True))
        add("", self.askpass)
        self.tree_hidden = Gtk.CheckButton(label="Mostrar archivos ocultos en el árbol",
                                           active=cfg.get("tree_show_hidden", False))
        add("", self.tree_hidden)
        self.scrollback_restore = Gtk.CheckButton(
            label="Conservar lo escrito en cada terminal al cerrar y mostrarlo al reabrir",
            active=cfg.get("restore_scrollback", True))
        add("", self.scrollback_restore)
        self.restore = Gtk.CheckButton(label="Restaurar pestañas y paneles al iniciar",
                                       active=cfg.get("restore_session", True))
        add("", self.restore)
        self.confirm = Gtk.ComboBoxText()
        for label in ("No preguntar", "Preguntar una vez", "Preguntar dos veces"):
            self.confirm.append_text(label)
        self.confirm.set_active(max(0, min(2, int(cfg.get("confirm_close", 2)))))
        add("Confirmar al cerrar", self.confirm)
        nb.append_page(grid, Gtk.Label(label="General"))

        # --- Atajos
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, margin=12)
        self.store = Gtk.ListStore(str, str, str)  # id, etiqueta, atajo
        for aid, label, _d in ACTIONS:
            self.store.append([aid, label, cfg["shortcuts"].get(aid, "")])
        view = Gtk.TreeView(model=self.store)
        view.append_column(Gtk.TreeViewColumn("Acción", Gtk.CellRendererText(), text=1))
        accel_renderer = Gtk.CellRendererAccel(editable=True, accel_mode=Gtk.CellRendererAccelMode.GTK)
        col = Gtk.TreeViewColumn("Atajo", accel_renderer)
        col.set_cell_data_func(accel_renderer, self._accel_data)
        view.append_column(col)
        accel_renderer.connect("accel-edited", self._accel_edited)
        accel_renderer.connect("accel-cleared", self._accel_cleared)
        sw = Gtk.ScrolledWindow()
        sw.add(view)
        box.pack_start(sw, True, True, 0)
        hint = Gtk.Label(label="Haz clic en un atajo y pulsa la nueva combinación. Retroceso lo borra.",
                         xalign=0)
        hint.get_style_context().add_class("dim-label")
        box.pack_start(hint, False, False, 0)
        reset = Gtk.Button(label="Restaurar atajos por defecto")
        reset.connect("clicked", self._reset_shortcuts)
        box.pack_start(reset, False, False, 0)
        nb.append_page(box, Gtk.Label(label="Atajos de teclado"))
        self.show_all()

    def _accel_data(self, _col, cell, model, it, _data):
        accel = model[it][2]
        if accel:
            key, mods = Gtk.accelerator_parse(accel)
            cell.set_property("accel-key", key)
            cell.set_property("accel-mods", mods)
        else:
            cell.set_property("accel-key", 0)
            cell.set_property("accel-mods", 0)

    def _accel_edited(self, _r, path, key, mods, _hw):
        self.store[path][2] = Gtk.accelerator_name(key, mods)

    def _accel_cleared(self, _r, path):
        self.store[path][2] = ""

    def _reset_shortcuts(self, *_):
        for row in self.store:
            row[2] = DEFAULT_SHORTCUTS[row[0]]

    def apply_to(self, cfg):
        cfg["font"] = self.font.get_font()
        cfg["scheme"] = self.scheme.get_active_text()
        cfg["cursor_shape"] = self.cursor.get_active_text()
        cfg["cursor_blink"] = self.blink.get_active()
        cfg["scrollback"] = int(self.scrollback.get_value())
        cfg["shell"] = self.shell.get_text().strip()
        cfg["show_menubar"] = self.menubar.get_active()
        cfg["show_pane_headers"] = self.headers.get_active()
        cfg["restore_scrollback"] = self.scrollback_restore.get_active()
        cfg["show_tree"] = self.show_tree.get_active()
        cfg["tree_show_hidden"] = self.tree_hidden.get_active()
        cfg["askpass"] = self.askpass.get_active()
        cfg["restore_session"] = self.restore.get_active()
        cfg["confirm_close"] = self.confirm.get_active()
        cfg["shortcuts"] = {row[0]: row[2] for row in self.store}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--askpass":
        return run_askpass(" ".join(sys.argv[2:]))
    Pytrol()
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
