"""Un despliegue con más de 10.000 URL cambiadas avisa igual a IndexNow: primero las nuevas, recorte declarado.

Antes, `derive` lanzaba un error y el deploy publicaba con la lista vacía (una regeneración del catálogo cambia
>12.000 fichas a la vez: ninguna llegaba a Bing/Copilot)."""
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('indexnow', ROOT / 'scripts/indexnow.py')
indexnow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(indexnow)


class TruncadoTest(unittest.TestCase):
    def test_large_change_set_is_capped_with_new_urls_first(self):
        before = {f'/recomendaciones/libros/l{i:05d}/': f'b{i}' for i in range(12000)}
        after = dict(before) | {f'/recomendaciones/generos/g{i:02d}/': f'g{i}' for i in range(40)}
        routes = {'before': before, 'after': after}
        with mock.patch.object(indexnow, 'registry_routes', side_effect=lambda p: routes[p.name]), \
             mock.patch.object(indexnow, 'artifact_digest', side_effect=lambda dist, src: f'{dist.name}:{src}'):
            urls, counts = indexnow.derive_changed_urls(Path('before'), Path('before'), Path('after'), Path('after'))
        self.assertEqual(len(urls), indexnow.MAX_URLS)
        self.assertEqual(counts['added'], 40)
        self.assertEqual(counts['truncated'], 12040 - indexnow.MAX_URLS)
        self.assertTrue(all(indexnow.ORIGIN + f'/recomendaciones/generos/g{i:02d}/' in urls for i in range(40)))

    def test_small_change_set_is_untouched(self):
        routes = {'before': {'/a/': 'a'}, 'after': {'/a/': 'a', '/b/': 'b'}}
        with mock.patch.object(indexnow, 'registry_routes', side_effect=lambda p: routes[p.name]), \
             mock.patch.object(indexnow, 'artifact_digest', side_effect=lambda dist, src: f'{dist.name}:{src}'):
            urls, counts = indexnow.derive_changed_urls(Path('before'), Path('before'), Path('after'), Path('after'))
        self.assertEqual(urls, [indexnow.ORIGIN + '/a/', indexnow.ORIGIN + '/b/'])
        self.assertNotIn('truncated', counts)


if __name__ == '__main__':
    unittest.main()
