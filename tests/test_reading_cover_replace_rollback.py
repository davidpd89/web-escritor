"""Una portada local que falla a medias (la miniatura no se escribe) deja los bytes viejos (Codex #1595, 26/11).

El mercado cambia la portada sobre una copia de la ficha y, si falla, conserva la ficha vieja; pero sin almacén
`replace_cover` sobrescribe el fichero en su sitio, así que sin esta vuelta atrás quedaba la imagen nueva con las
medidas y la fuente viejas.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_amazon_market as market  # noqa: E402


class ReplaceCoverRollback(unittest.TestCase):
    def test_failed_thumbnail_restores_the_old_cover(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {market.cover_store.STORE_DIR_ENV: ''}):
            root = Path(tmp)
            folder = root / 'assets/reading-covers'
            folder.mkdir(parents=True)
            (folder / 'lib-0001.webp').write_bytes(b'vieja')
            (folder / 'lib-0001-320.webp').write_bytes(b'vieja-320')
            book = {'id': 'lib-0001', 'portada_local': '/assets/reading-covers/lib-0001.webp', 'portada_ancho': 1}
            real = market.cover_store.put

            def put(root_, path, content):
                if path.endswith('-320.webp'):
                    raise OSError('disco lleno')
                return real(root_, path, content)

            with patch.object(market.cover_store, 'put', side_effect=put), self.assertRaises(OSError):
                market.replace_cover(book, root, b'nueva', b'nueva-320', (600, 900), 'https://x/y.jpg', '2026-11-26')
            self.assertEqual((folder / 'lib-0001.webp').read_bytes(), b'vieja')
            self.assertEqual((folder / 'lib-0001-320.webp').read_bytes(), b'vieja-320')
            self.assertEqual(book['portada_ancho'], 1)


if __name__ == '__main__':
    unittest.main()
