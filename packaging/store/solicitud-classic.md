# Solicitud de confinamiento classic para Pytrol

Hay que crear **un tema nuevo** en https://forum.snapcraft.io/c/store-requests/classic-confinement/26
(categoría `classic-confinement`), con tu cuenta de Ubuntu One. Pega lo de abajo, sin los comentarios.
La revisión ya está subida a la Store (revisión 2, versión 0.6.4) y espera esta aprobación.

**Título:** `Classic confinement request for pytrol`

---

**Snap name:** pytrol
**Snap description:** terminal emulator (GTK 3 + VTE, written in Python) with split panes, one project per
pane, a file tree, a built-in editor and a persistent session.
**Upstream / source:** https://github.com/saraivaruas/pytrol (MIT)
**Revision uploaded:** 2 (0.6.4, amd64)

**Why classic is required**

Pytrol is a terminal emulator. Its whole purpose is to run the user's own shell and the programs the
user types, with the user's permissions and on the user's real file system: their projects, dotfiles,
SSH keys, package managers, compilers, `git`, `docker`, `sudo`, and any other tool installed on the host.

- Under strict confinement the shell would run inside the snap's sandbox, over the `core22` file system,
  without the user's tools and with no access to most of their files. A terminal in that state cannot do its job.
- The `home` and `removable-media` interfaces are not enough: a terminal must execute arbitrary host
  binaries and reach any path, not only the home directory.
- `personal-files` or `system-files` cannot enumerate what a user may legitimately open in a terminal.

**What the snap does and does not do**

- It starts the user's login shell in each pane and shows its output. It does not make network connections
  of its own, has no telemetry and does not send data anywhere.
- It saves its own settings and session in `~/.config/pytrol` (owner-only permissions).
- Python and the C library come from `core22`; GTK 3, VTE and GtkSourceView 4 are bundled in the snap. The
  launcher (`snap/local/pytrol-launcher`) gives the shell the user's original environment, so nothing from the
  snap leaks into the programs the user runs.
- A beta in `devmode` is already published in the `beta` channel only for testing (its shell runs over
  `core22` and cannot see the user's tools, which is exactly why a strict or devmode snap is not usable).

Happy to answer any questions or adjust the packaging.
