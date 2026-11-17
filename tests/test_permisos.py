"""La sesión y la configuración solo pueden leerlas el usuario (carpeta 700, archivos 600)."""
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytrol  # noqa: E402


def modo(ruta):
    return stat.S_IMODE(os.stat(ruta).st_mode)


class PermisosPrivados(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self._tmp.name, "pytrol")
        self._orig = (pytrol.CONFIG_DIR, pytrol.CONFIG_FILE, pytrol.SESSION_FILE)
        pytrol.CONFIG_DIR = self.dir
        pytrol.CONFIG_FILE = os.path.join(self.dir, "config.json")
        pytrol.SESSION_FILE = os.path.join(self.dir, "session.json")

    def tearDown(self):
        pytrol.CONFIG_DIR, pytrol.CONFIG_FILE, pytrol.SESSION_FILE = self._orig
        self._tmp.cleanup()

    def test_archivos_nuevos_son_privados(self):
        pytrol.write_session({"version": 1, "tabs": []})
        pytrol.save_config({"scheme": "Dracula"})
        self.assertEqual(modo(self.dir), 0o700)
        self.assertEqual(modo(pytrol.SESSION_FILE), 0o600)
        self.assertEqual(modo(pytrol.CONFIG_FILE), 0o600)
        self.assertEqual(sorted(os.listdir(self.dir)), ["config.json", "session.json"])   # sin temporales

    def test_corrige_una_instalacion_anterior(self):
        os.makedirs(self.dir, mode=0o775)
        os.chmod(self.dir, 0o775)
        for ruta in (pytrol.CONFIG_FILE, pytrol.SESSION_FILE):
            Path(ruta).write_text("{}")
            os.chmod(ruta, 0o664)
        pytrol.ensure_config_dir()
        self.assertEqual(modo(self.dir), 0o700)
        self.assertEqual(modo(pytrol.CONFIG_FILE), 0o600)
        self.assertEqual(modo(pytrol.SESSION_FILE), 0o600)

    def test_el_contenido_se_conserva(self):
        pytrol.write_session({"version": 1, "tabs": [], "nota": "áé"})
        self.assertIn("áé", Path(pytrol.SESSION_FILE).read_text(encoding="utf-8"))

    def test_un_temporal_viejo_con_permisos_abiertos_no_se_hereda(self):
        os.makedirs(self.dir, mode=0o700)
        viejo = pytrol.SESSION_FILE + ".tmp"
        Path(viejo).write_text("x")
        os.chmod(viejo, 0o666)
        pytrol.write_session({"version": 1, "tabs": []})
        self.assertEqual(modo(pytrol.SESSION_FILE), 0o600)


if __name__ == "__main__":
    unittest.main()
