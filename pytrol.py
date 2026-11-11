#!/usr/bin/env python3
"""Pytrol — Advanced Python Terminal: Power, Speed, Control (GTK3 + VTE)."""
import glob
import json
import os
import shlex
import signal
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gdk, GLib, Gtk, Pango, Vte  # noqa: E402

APP_TITLE = "Pytrol"
APP_ID = "io.github.saraivaruas.Pytrol"
IN_FLATPAK = os.path.exists("/.flatpak-info")
CONFIG_DIR = os.environ.get("PYTROL_CONFIG_DIR") or os.path.join(GLib.get_user_config_dir(), "pytrol")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SESSION_FILE = os.path.join(CONFIG_DIR, "session.json")
SESSION_SAVE_SECONDS = 5

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
    ("copy", "Copiar", "<Primary><Shift>c"),
    ("paste", "Pegar", "<Primary><Shift>v"),
    ("select_all", "Seleccionar todo", "<Primary><Shift>a"),
    ("clear", "Limpiar terminal", "<Primary><Shift>l"),
    ("zoom_in", "Aumentar zoom", "<Primary>plus"),
    ("zoom_out", "Reducir zoom", "<Primary>minus"),
    ("zoom_reset", "Zoom normal", "<Primary>0"),
    ("toggle_menubar", "Mostrar barra de menú", "<Primary><Shift>m"),
    ("fullscreen", "Pantalla completa", "F11"),
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


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        print(f"No se pudo guardar la configuración: {exc}", file=sys.stderr)


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

    def __init__(self, app, cwd=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.app = app
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
        self.pack_start(hbox, True, True, 0)

        self.term.connect("focus-in-event", lambda *_: app.on_pane_focus(self))
        self.term.connect("button-press-event", lambda t, e: app.on_button(self, e))
        self.term.connect("window-title-changed", lambda *_: app.on_title_changed(self))
        self.term.connect("child-exited", lambda *_: app.close_pane(self, from_exit=True))
        self.spawn(cwd)

    def spawn(self, cwd):
        cwd = cwd or os.path.expanduser("~")
        if not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")
        self.last_cwd = cwd
        shell = self.app.cfg.get("shell") or os.environ.get("SHELL", "/bin/bash")
        env = dict(os.environ)
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"
        envv = [f"{k}={v}" for k, v in env.items()]
        if IN_FLATPAK:
            argv = ["flatpak-spawn", "--host", "--env=TERM=xterm-256color",
                    "--env=COLORTERM=truecolor", f"--directory={cwd}", shell]
        else:
            argv = shlex.split(shell)
        self.term.spawn_async(Vte.PtyFlags.DEFAULT, cwd, argv, envv,
                              GLib.SpawnFlags.SEARCH_PATH, None, None, -1, None, None, None)

    def apply_config(self, cfg):
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

    def cwd(self):
        """Directorio actual del shell, buscando en /proc el proceso con nuestro pty."""
        pty = self.term.get_pty()
        if pty is None:
            return None
        try:
            tty = os.ttyname(pty.get_fd())
            for pdir in glob.glob("/proc/[0-9]*"):
                try:
                    if os.readlink(f"{pdir}/fd/0") == tty:
                        return os.readlink(f"{pdir}/cwd")
                except OSError:
                    continue
        except OSError:
            pass
        return None

    def change_dir(self, path):
        """Cambia el directorio del shell en marcha (sin matar el proceso)."""
        self.term.feed_child(f" cd {shlex.quote(path)} && clear\n".encode())
        self.last_cwd = path
        self.header.set_text(path)

    def cwd_or_last(self):
        cwd = self.cwd()
        if cwd:
            self.last_cwd = cwd
        return self.last_cwd


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
        """)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _remember_size(self, _w, alloc):
        if not (self.get_window() and self.get_window().get_state() & Gdk.WindowState.MAXIMIZED):
            self.cfg["window_size"] = [alloc.width, alloc.height]

    # ---------------------------------------------------------- sesión
    def _serialize_widget(self, w):
        if isinstance(w, Pane):
            return {"type": "pane", "cwd": w.cwd_or_last()}
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
            return Pane(self, node.get("cwd"))
        orient = Gtk.Orientation.HORIZONTAL if node.get("orientation") == "h" else Gtk.Orientation.VERTICAL
        paned = SplitPaned(orient, float(node.get("fraction", 0.5)))
        paned.pack1(self._build_widget(node.get("a")), True, False)
        paned.pack2(self._build_widget(node.get("b")), True, False)
        return paned

    def restore_session(self):
        data = load_session()
        if not data:
            return False
        try:
            for tdata in data["tabs"]:
                tab = self.new_tab(inherit_cwd=False)
                first = tab.panes()[0]
                tab.remove(first)
                first.destroy()
                root = self._build_widget(tdata.get("layout"))
                tab.pack_start(root, True, True, 0)
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
            recent_item]))

        mb.append(self._submenu("Edición", [
            self._item("copy"), self._item("paste"), self._item("select_all"), None,
            self._item("clear")]))

        mb.append(self._submenu("Ver", [
            self._item("prev_tab"), self._item("next_tab"),
            self._item("move_tab_left"), self._item("move_tab_right"), None,
            self._item("zoom_in"), self._item("zoom_out"), self._item("zoom_reset"), None,
            self._item("toggle_menubar"), self._item("fullscreen")]))

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

    def new_tab(self, cwd=None, inherit_cwd=True):
        if cwd is None and inherit_cwd and self.current_pane():
            cwd = self.current_pane().cwd()
        tab = Tab()
        pane = Pane(self, cwd)
        tab.pack_start(pane, True, True, 0)
        tab.focused = pane

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
        self.notebook.set_current_page(idx)
        pane.term.grab_focus()
        self.update_tabs_visibility()
        self.update_headers(tab)
        self.save_session()
        return tab

    def close_tab(self, tab, force=False):
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
        self.update_headers(tab)
        new_pane.term.grab_focus()
        self.save_session()
        return new_pane

    def close_pane(self, pane, from_exit=False):
        tab = pane.get_ancestor(Tab)
        if tab is None:
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
        self.remember_project(path)
        self.update_headers(self.current_tab())
        pane.term.grab_focus()

    def open_project_dialog(self, mode):
        path = self.choose_folder()
        if not path:
            return
        if mode == "here":
            self.open_project_in(self.current_pane(), path)
        elif mode == "tab":
            self.new_tab(cwd=path)
            self.remember_project(path)
        else:
            orient = Gtk.Orientation.HORIZONTAL if mode == "split_v" else Gtk.Orientation.VERTICAL
            self.split(self.current_pane(), orient, cwd=path)
            self.remember_project(path)

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
        return False

    def on_destroy(self, *_):
        if self.notebook.get_n_pages() > 0:
            self.save_session()
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
        elif a == "copy" and term: term.copy_clipboard_format(Vte.Format.TEXT)
        elif a == "paste" and term: term.paste_clipboard()
        elif a == "select_all" and term: term.select_all()
        elif a == "clear" and term: term.reset(True, True)
        elif a == "zoom_in" and term: self.zoom(term, 1.1)
        elif a == "zoom_out" and term: self.zoom(term, 1 / 1.1)
        elif a == "zoom_reset" and term: term.set_font_scale(1.0)
        elif a == "toggle_menubar": self.toggle_menubar()
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
        dlg = Gtk.AboutDialog(transient_for=self, program_name=APP_TITLE, version="0.2.0",
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
        self.shell = Gtk.Entry(text=cfg["shell"], placeholder_text=os.environ.get("SHELL", "/bin/bash"))
        add("Comando del shell", self.shell)
        self.menubar = Gtk.CheckButton(label="Mostrar barra de menú", active=cfg["show_menubar"])
        add("", self.menubar)
        self.headers = Gtk.CheckButton(label="Mostrar cabecera con el proyecto en cada panel",
                                       active=cfg["show_pane_headers"])
        add("", self.headers)
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
        cfg["restore_session"] = self.restore.get_active()
        cfg["confirm_close"] = self.confirm.get_active()
        cfg["shortcuts"] = {row[0]: row[2] for row in self.store}


def main():
    Pytrol()
    Gtk.main()


if __name__ == "__main__":
    sys.exit(main())
