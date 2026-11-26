"""Caso 11 de la revisión GPT (25/11): la cuarentena repite validate() por cada libro apartado y cada vuelta releía
el manifiesto del almacén una vez por libro y resumía y decodificaba todas las portadas (42 s con 7.900 libros, hasta
88 vueltas). Ahora se leen una vez por versión del fichero; cualquier reescritura invalida lo memorizado.
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_cover_store as cs  # noqa: E402

spec = importlib.util.spec_from_file_location('build_memoria', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def png(color, size=(4, 6)):
    out = io.BytesIO()
    Image.new('RGB', size, color).save(out, 'PNG')
    return out.getvalue()


def manifiesto(root, nombres):
    path = root / cs.MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({'base_url': 'https://cdn.example.org/c', 'archivos': nombres,
                                'sha256': {n: 'a' * 64 for n in nombres}}), encoding='utf-8')


class ValidacionMemoriaTest(unittest.TestCase):
    def test_el_manifiesto_se_lee_una_vez_por_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifiesto(root, ['a.jpg'])
            leidas, original = [], Path.read_text

            def contar(self, *a, **k):
                if self.name == Path(cs.MANIFEST).name:
                    leidas.append(1)
                return original(self, *a, **k)
            Path.read_text = contar
            try:
                for _ in range(500):
                    cs.stored_digest('/assets/reading-covers/a.jpg', root)
                    cs.is_stored('/assets/reading-covers/a.jpg', root)
                self.assertEqual(len(leidas), 1)
                manifiesto(root, ['a.jpg', 'bb.jpg'])
                self.assertTrue(cs.is_stored('/assets/reading-covers/bb.jpg', root), 'la escritura invalida la caché')
                self.assertEqual(len(leidas), 2)
            finally:
                Path.read_text = original

    def test_load_devuelve_una_copia(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifiesto(root, ['a.jpg'])
            cs.load(root)['archivos'].append('x.jpg')
            cs.load(root)['sha256']['x.jpg'] = 'b' * 64
            self.assertEqual(cs.load(root)['archivos'], ['a.jpg'])
            self.assertFalse(cs.is_stored('/assets/reading-covers/x.jpg', root))

    def test_una_portada_reescrita_se_vuelve_a_comprobar(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp, 'p.png')
            file.write_bytes(png('red'))
            primera = build._huella_portada(file)
            self.assertIsNone(primera[3])
            self.assertEqual((primera[1], primera[2]), ((4, 6), 'PNG'))
            self.assertIs(build._huella_portada(file), primera, 'misma versión: memorizada')
            file.write_bytes(b'\x89PNG roto' * 3)
            os.utime(file, ns=(1, 1))  # aunque el reloj no avance, cambia la firma
            rota = build._huella_portada(file)
            self.assertIsInstance(rota[3], OSError)
            self.assertNotEqual(rota[0], primera[0])
            file.write_bytes(png('blue', (5, 7)))
            self.assertEqual(build._huella_portada(file)[1], (5, 7), 'restaurada: se vuelve a decodificar')


if __name__ == '__main__':
    unittest.main()
