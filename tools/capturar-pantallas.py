#!/usr/bin/env python3
"""Genera las capturas de docs/ con Pytrol de verdad y datos de ejemplo.

Cada escena abre Pytrol con una sesión armada a mano (proyectos de ejemplo, archivos
abiertos en el editor), escribe unos comandos reales en los paneles y fotografía la ventana.
Para que no aparezcan tu usuario ni tus carpetas, la aplicación corre en un espacio de
nombres temporal (unshare) donde /home es un directorio vacío con solo /home/demo, y con la
configuración aislada (PYTROL_CONFIG_DIR): no toca tu sesión ni tus preferencias.

Requisitos: Linux con X11, python3-gi/GTK/VTE, xdotool, ImageMagick (import) y git.
Uso:  tools/capturar-pantallas.py            # todas las escenas, escribe en docs/
      tools/capturar-pantallas.py paneles    # solo una (paneles, claro, dracula, preferencias)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
DOCS = AQUI / "docs"
TMP = Path(tempfile.mkdtemp(prefix="pytrol-capturas."))
HOME_SRC = TMP / "home"          # se copia a /home/demo dentro del espacio de nombres
H = "/home/demo/proyectos"

ARCHIVOS = {
    "api-tienda/app.py": '''"""API de la tienda: pedidos y productos."""
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__)
PEDIDOS = {}


@app.get("/pedidos/<int:pedido_id>")
def ver_pedido(pedido_id):
    pedido = PEDIDOS.get(pedido_id)
    if pedido is None:
        return jsonify(error="Pedido no encontrado"), 404
    return jsonify(pedido)


@app.post("/pedidos")
def crear_pedido():
    datos = request.get_json(force=True)
    nuevo_id = len(PEDIDOS) + 1
    PEDIDOS[nuevo_id] = {
        "id": nuevo_id,
        "cliente": datos["cliente"],
        "total": sum(i["precio"] * i["cantidad"] for i in datos["items"]),
        "creado": datetime.now().isoformat(timespec="seconds"),
    }
    return jsonify(PEDIDOS[nuevo_id]), 201


if __name__ == "__main__":
    app.run(debug=True)
''',
    "api-tienda/requirements.txt": "flask==3.0.3\npytest==8.3.2\n",
    "api-tienda/README.md": "# API de la tienda\n\nPedidos y productos de ejemplo con Flask.\n",
    "api-tienda/tests/test_pedidos.py": '''from app import app


def test_crear_y_ver_pedido():
    cliente = app.test_client()
    r = cliente.post("/pedidos", json={"cliente": "Ana", "items": [{"precio": 1500, "cantidad": 2}]})
    assert r.status_code == 201
    assert cliente.get("/pedidos/1").json["total"] == 3000
''',
    "web-landing/index.html": '''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Café del Sur</title>
  <link rel="stylesheet" href="css/estilos.css">
</head>
<body>
  <header class="portada">
    <h1>Café del Sur</h1>
    <p>Tostado artesanal, despachado en el día.</p>
    <a class="boton" href="#carta">Ver la carta</a>
  </header>
  <script src="js/app.js"></script>
</body>
</html>
''',
    "web-landing/css/estilos.css": '''.portada { text-align: center; padding: 4rem 1rem; background: #2b1d14; color: #f5e9dc; }
.boton { display: inline-block; padding: .6rem 1.4rem; border-radius: 999px; background: #d98c3f; color: #fff; }
''',
    "web-landing/js/app.js": 'document.querySelector(".boton").addEventListener("click", () => console.log("carta"));\n',
    "web-landing/package.json": '{\n  "name": "web-landing",\n  "version": "1.2.0",\n  "scripts": { "build": "vite build" }\n}\n',
    "scripts-datos/limpiar.py": '''#!/usr/bin/env python3
"""Quita filas vacías y normaliza los nombres de columna de un CSV."""
import csv
import sys


def limpiar(origen, destino):
    with open(origen, newline="", encoding="utf-8") as fin, open(destino, "w", newline="", encoding="utf-8") as fout:
        lector = csv.DictReader(fin)
        escritor = csv.DictWriter(fout, [c.strip().lower() for c in lector.fieldnames])
        escritor.writeheader()
        for fila in lector:
            if any(v.strip() for v in fila.values()):
                escritor.writerow({k.strip().lower(): v.strip() for k, v in fila.items()})


if __name__ == "__main__":
    limpiar(sys.argv[1], sys.argv[2])
''',
    "scripts-datos/datos/ventas.csv": "fecha,Producto ,Cantidad\n2026-11-10,Café molido,12\n,,\n2026-11-11,Té verde,7\n",
    "scripts-datos/respaldo.sh": '#!/usr/bin/env bash\nset -euo pipefail\nrsync -a --delete datos/ respaldo/\necho "Respaldo listo"\n',
    "docs-guia/README.md": "# Guía de usuario\n\nCapítulos en `capitulos/`.\n",
    "docs-guia/capitulos/01-introduccion.md": "# 1. Introducción\n\nBienvenida a la guía.\n",
    "docs-guia/capitulos/02-instalacion.md": "# 2. Instalación\n\n```bash\npip install -r requirements.txt\n```\n",
}


def crear_demo():
    base = HOME_SRC / "proyectos"
    for ruta, contenido in ARCHIVOS.items():
        f = base / ruta
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(contenido, encoding="utf-8")
    (base / "scripts-datos/respaldo.sh").chmod(0o755)
    (HOME_SRC / ".hushlogin").write_text("")                      # sin el aviso de sudo del shell
    (HOME_SRC / ".sudo_as_admin_successful").write_text("")
    (HOME_SRC / ".bashrc").write_text("export GIT_PAGER=cat\nPS1='\\[\\e[1;32m\\]\\w\\[\\e[0m\\] $ '\n")   # "$" fijo: en el espacio temporal eres root
    # Historial de git de ejemplo (identidad y fechas fijas; no toca tu configuración).
    api = base / "api-tienda"
    env = dict(os.environ, GIT_AUTHOR_NAME="Ana Soto", GIT_AUTHOR_EMAIL="ana@ejemplo.cl",
               GIT_COMMITTER_NAME="Ana Soto", GIT_COMMITTER_EMAIL="ana@ejemplo.cl",
               GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    pasos = [(["README.md", "requirements.txt"], "Estructura inicial de la API"),
             (["app.py"], "Agrega los endpoints de pedidos"),
             (["tests"], "Prueba de creación y consulta de pedidos")]
    for i, (archivos, mensaje) in enumerate(pasos):
        e = dict(env, GIT_AUTHOR_DATE=f"2026-11-1{i} 10:00:00", GIT_COMMITTER_DATE=f"2026-11-1{i} 10:00:00")
        if i == 0:
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=api, env=e, check=True)
        subprocess.run(["git", "add", *archivos], cwd=api, env=e, check=True)
        subprocess.run(["git", "commit", "-q", "-m", mensaje], cwd=api, env=e, check=True)


# ---------------------------------------------------------------- sesiones
def panel(proyecto, archivos=(), arbol_ancho=240, editor=330):
    nodo = {"type": "pane", "cwd": f"{H}/{proyecto}", "project": f"{H}/{proyecto}", "tree": True,
            "tree_width": arbol_ancho}
    if archivos:
        nodo["files"] = [f"{H}/{proyecto}/{a}" for a in archivos]
        nodo["editor_height"] = editor
    return nodo


def dividir(orientacion, fraccion, a, b):
    return {"type": "split", "orientation": orientacion, "fraction": fraccion, "a": a, "b": b}


# Cada escena: esquema, tamaño, diseño y lo que se escribe. Cada acción es
# (x, y, comandos): se hace clic en ese punto de la ventana (fracciones de su ancho y alto), que
# queda dentro del terminal de un panel, y se escriben los comandos.
ESCENAS = {
    "paneles": dict(
        esquema="Oscuro (qterminal)", ancho=1420, alto=800,
        diseno=dividir("h", 0.5,
                       dividir("v", 0.58, panel("api-tienda", ["app.py"], editor=250), panel("web-landing")),
                       dividir("v", 0.58, panel("scripts-datos", ["limpiar.py"], editor=250), panel("docs-guia"))),
        acciones=[(0.35, 0.5, ["git log --oneline", "git status -sb"]),
                  (0.35, 0.82, ["ls", "cat package.json"]),
                  (0.75, 0.82, ["wc -w capitulos/*.md"]),
                  (0.75, 0.5, ["python3 limpiar.py datos/ventas.csv datos/limpio.csv", "cat datos/limpio.csv"])],
        archivo="pytrol-paneles.png"),
    "claro": dict(
        esquema="Claro", ancho=1400, alto=800,
        diseno=dividir("h", 0.52, panel("web-landing", ["index.html", "css/estilos.css"]),
                       dividir("v", 0.5, panel("api-tienda"), panel("docs-guia"))),
        acciones=[(0.35, 0.6, ["ls"]), (0.8, 0.25, ["git log --oneline"]), (0.8, 0.75, ["ls capitulos"])],
        archivo="pytrol-claro.png"),
    "dracula": dict(
        esquema="Dracula", ancho=1400, alto=800,
        diseno=dividir("h", 0.5, panel("api-tienda", ["app.py", "tests/test_pedidos.py"]),
                       dividir("v", 0.5, panel("scripts-datos"), panel("web-landing"))),
        acciones=[(0.35, 0.6, ["git log --oneline -3"]), (0.8, 0.25, ["cat datos/ventas.csv"]),
                  (0.8, 0.75, ["ls", "cat package.json"])],
        archivo="pytrol-dracula.png"),
    "preferencias": dict(
        esquema="Oscuro (qterminal)", ancho=1300, alto=800,
        diseno=dividir("h", 0.5, panel("api-tienda", ["app.py"]), panel("web-landing")),
        acciones=[(0.3, 0.6, ["git status -sb"])], dialogo="Preferencias", archivo="pytrol-preferencias.png"),
}


def xdo(*args, check=True):
    return subprocess.run(["xdotool", *args], capture_output=True, text=True, check=check).stdout.strip()


def esperar_ventana(pid, nombre=None, intentos=30):
    for _ in range(intentos):
        time.sleep(1)
        cmd = ["search", "--pid", str(pid)] + (["--name", nombre] if nombre else [])
        ids = xdo(*cmd, check=False).split()
        if ids:
            return ids[-1]
    raise RuntimeError(f"No apareció la ventana ({nombre or 'principal'})")


def fotografiar(escena, nombre):
    cfg_dir = TMP / f"cfg-{nombre}"
    cfg_dir.mkdir()
    sesion = {"version": 1, "tabs": [{"layout": escena["diseno"], "focused": 0}], "current": 0,
              "window_size": [escena["ancho"], escena["alto"]]}
    (cfg_dir / "session.json").write_text(json.dumps(sesion, ensure_ascii=False))
    (cfg_dir / "config.json").write_text(json.dumps({
        "scheme": escena["esquema"], "font": "DejaVu Sans Mono 11",
        "window_size": [escena["ancho"], escena["alto"]]}))
    comando = (f"mount -t tmpfs tmpfs /home && mkdir -p /home/demo && cp -a {HOME_SRC}/. /home/demo/ "
               f"&& exec python3 {TMP}/pytrol.py")
    env = dict(os.environ, HOME="/home/demo", PYTROL_CONFIG_DIR=str(cfg_dir), USER="demo", LOGNAME="demo",
               SHELL="/bin/bash")
    proc = subprocess.Popen(["unshare", "-Ur", "--mount", "bash", "-c", comando], env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        wid = esperar_ventana(proc.pid)
        time.sleep(4)
        xdo("windowmove", wid, "0", "0")
        xdo("windowactivate", "--sync", wid, check=False)
        time.sleep(2)
        ancho, alto = (int(v) for v in xdo("getwindowgeometry", wid).split("Geometry:")[1].strip().split("x"))
        for fx, fy, comandos in escena["acciones"]:
            xdo("mousemove", "--window", wid, str(int(ancho * fx)), str(int(alto * fy)))
            xdo("click", "1")
            time.sleep(0.8)
            for c in comandos:
                xdo("type", "--delay", "40", c)
                time.sleep(0.3)
                xdo("key", "Return")
                time.sleep(1.5)
        destino = DOCS / escena["archivo"]
        if escena.get("dialogo"):
            # El atajo Ctrl+Mayús+coma no funciona con todos los teclados: se abre desde el menú.
            xdo("mousemove", "--window", wid, "372", "12")
            xdo("click", "1")
            time.sleep(0.8)
            xdo("key", "Down")
            xdo("key", "Return")
            time.sleep(1.5)
            wid = esperar_ventana(proc.pid, escena["dialogo"], 8)
            time.sleep(1)
        else:
            time.sleep(1)
        subprocess.run(["import", "-window", wid, str(destino)], check=True)
        print(f"  {destino.relative_to(AQUI)}")
    finally:
        proc.kill()
        time.sleep(1)


def main():
    for herramienta in ("xdotool", "import", "unshare", "git"):
        if not shutil.which(herramienta):
            sys.exit(f"Falta «{herramienta}».")
    elegidas = sys.argv[1:] or list(ESCENAS)
    for e in elegidas:
        if e not in ESCENAS:
            sys.exit(f"Escena desconocida: {e}. Opciones: {', '.join(ESCENAS)}")
    DOCS.mkdir(exist_ok=True)
    shutil.copy(AQUI / "pytrol.py", TMP / "pytrol.py")   # fuera de /home, que queda oculto en el espacio temporal
    try:
        crear_demo()
        for e in elegidas:
            print(f"Escena «{e}»")
            fotografiar(ESCENAS[e], e)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
