# Solicitud de confinamiento classic para Pytrol

> **Publicado el 17-11-2026:** https://forum.snapcraft.io/t/classic-confinement-request-for-pytrol/54260 (tema 54260).
> Quedó sin respuesta de los revisores; cuando la haya, se continúa ahí mismo.

Es el tema que se publica en https://forum.snapcraft.io/c/store-requests/classic-confinement/26 (categoría
`classic-confinement`), con el mismo formato que el de Sentinel
(https://forum.snapcraft.io/t/54253). Está en inglés porque es el idioma del foro.

**Título:** `Classic confinement request for pytrol`

**Cuerpo:**

- **name**: pytrol
- **description**: Advanced terminal emulator for Linux, written in Python with GTK 3 and VTE. It runs the user's own shell in each pane and adds split panes (2, 4, 6 or 8), one project per pane, a file tree, a built-in editor with syntax highlighting, tabs and a persistent session. No network access of its own and no telemetry.
- **snapcraft**: https://github.com/saraivaruas/pytrol/blob/main/snap/snapcraft.yaml
- **upstream**: https://github.com/saraivaruas/pytrol
- **upstream-relation**: I am the author and publisher of the upstream project (MIT license). It can also be installed from source with `install.sh`, and a Flatpak manifest is kept in the repository; the snap is another channel.
- **supported-category**: Terminal emulators, multiplexers and shells.
- **reasoning**: A terminal emulator exists to run the user's own shell and the programs the user types, with the user's permissions and on the user's real file system:
  1. The shell of every pane is the user's login shell on the host, with access to their projects, dotfiles, SSH keys, package managers, compilers, `git`, `docker`, `sudo` and any other tool installed on the system. Under strict confinement that shell would run over the `core22` file system, without those tools and without most of the user's files.
  2. The file tree and the built-in editor must open any path the user chooses, not only the home directory, and the project folders the user opens in each pane can be anywhere.
  3. It provides a graphical password helper (`SUDO_ASKPASS` / `SSH_ASKPASS`) that host programs such as `sudo` and `ssh` run when they have no terminal, so the helper must be executable from outside the snap.
  4. No existing interface lets a snap execute arbitrary host binaries, so `home`, `removable-media`, `personal-files` or `system-files` cannot cover what a terminal does.

  What it does not do: it makes no network connections of its own, has no telemetry, and keeps only its own settings and session in `~/.config/pytrol` (owner-only permissions). Python and the C library come from `core22`; GTK 3, VTE and GtkSourceView 4 are bundled. The launcher gives the shell the user's original environment, so nothing from the snap leaks into the programs the user runs.

  I have published a devmode build in the beta channel (amd64) so people can try it, but its shell runs over the `core22` file system and cannot see the user's tools, so it is not a real replacement. The classic build (revision 2, 0.6.4, amd64) is uploaded and waiting for this review.

- [x] I understand that strict confinement is generally preferred over classic.
- [ ] I've tried the existing interfaces to make the snap work under strict confinement. **Not as such**: the devmode build shows that a strict snap's shell runs over `core22` with no host tools, and I know of no interface that runs arbitrary host binaries; I am happy to follow the reviewers' guidance.

Note: parts of the project were developed with the help of AI tools (disclosed here for transparency).
