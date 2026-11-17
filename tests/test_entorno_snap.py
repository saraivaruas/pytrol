"""Pruebas del manejo del entorno cuando Pytrol corre dentro del snap.

El lanzador del snap cambia variables (PYTHONPATH, XDG_DATA_DIRS…) y guarda las originales;
Pytrol las devuelve al shell de cada panel y a las aplicaciones que abre. Necesitan
python3-gi, GTK 3 y VTE; en un servidor sin pantalla: xvfb-run -a python3 -m unittest discover -s tests
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytrol  # noqa: E402


class EntornoSnap(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        self._in_snap = pytrol.IN_SNAP

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)
        pytrol.IN_SNAP = self._in_snap

    def _como_snap(self):
        os.environ.update({
            "SNAP": "/snap/pytrol/1", "SNAP_NAME": "pytrol", "SNAP_REVISION": "1",
            "PYTROL_SNAP_SAVED": "PYTHONPATH XDG_DATA_DIRS",
            "PYTROL_SNAP_HAD_PYTHONPATH": "0",
            "PYTHONPATH": "/snap/pytrol/1/usr/lib/python3/dist-packages",
            "PYTROL_SNAP_HAD_XDG_DATA_DIRS": "1", "PYTROL_SNAP_ORIG_XDG_DATA_DIRS": "/usr/share",
            "XDG_DATA_DIRS": "/snap/pytrol/1/usr/share:/usr/share"})
        pytrol.IN_SNAP = True

    def test_fuera_del_snap_no_cambia_nada(self):
        pytrol.IN_SNAP = False
        self.assertEqual(pytrol.snap_env_overrides(), {})
        self.assertEqual(pytrol.snap_clean_argv(), [])
        self.assertIsNone(pytrol.launch_context())

    def test_devuelve_los_valores_originales(self):
        self._como_snap()
        cambios = pytrol.snap_env_overrides()
        self.assertIsNone(cambios["PYTHONPATH"])                    # no existía: se quita
        self.assertEqual(cambios["XDG_DATA_DIRS"], "/usr/share")    # existía: se restaura
        for propia in ("SNAP", "SNAP_NAME", "SNAP_REVISION", "PYTROL_SNAP_SAVED"):
            self.assertIsNone(cambios[propia])

    def test_env_recibe_las_opciones_antes_de_las_asignaciones(self):
        self._como_snap()
        argv = pytrol.snap_clean_argv()
        self.assertEqual(argv[0], "/usr/bin/env")
        self.assertIn("XDG_DATA_DIRS=/usr/share", argv)
        self.assertIn("PYTHONPATH", argv[argv.index("-u") + 1:])
        # env deja de leer opciones en la primera asignación: todos los -u van antes.
        primera = min(i for i, a in enumerate(argv) if "=" in a)
        self.assertNotIn("-u", argv[primera:])

    def test_ayudante_de_contrasena_usa_el_comando_del_snap(self):
        self._como_snap()
        os.environ["PYTROL_CONFIG_DIR"] = "/nonexistent"
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            pytrol.ASKPASS_HELPER = os.path.join(tmp, "askpass")
            pytrol.CONFIG_DIR = tmp
            ruta = pytrol.ensure_askpass_helper()
            with open(ruta, encoding="utf-8") as fh:
                self.assertIn("/snap/bin/pytrol --askpass", fh.read())


if __name__ == "__main__":
    unittest.main()
