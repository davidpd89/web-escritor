"""Todo lo que regeneran los constructores de la carga debe poder publicarse (17/11).

La carga del 17/11 terminó sus 138 contratos y paró en el último paso: build-editoriales.py reescribe
editoriales/index.html (lleva la fecha de hoy) y allowed_path solo admitía las fichas de cada sello. La clase de
fallo es «un constructor escribe una ruta que la lista blanca no conoce»: aquí se ejecuta el constructor en un
directorio vacío y se exige que cada fichero que escribe sea publicable.
"""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_publication_paths', ROOT / 'scripts/publish-reading-refresh.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublishPathsTest(unittest.TestCase):
    def test_build_editoriales_outputs_are_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, 'scripts/build-editoriales.py', '--data', 'data/editoriales.json', '--output', tmp],
                           cwd=ROOT, check=True, capture_output=True)
            written = sorted(p.relative_to(tmp).as_posix() for p in Path(tmp).rglob('*') if p.is_file())
        self.assertTrue(written)
        self.assertEqual([p for p in written if not publisher.allowed_path(p)], [])


if __name__ == '__main__':
    unittest.main()
