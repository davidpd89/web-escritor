"""Un fichero de textos roto no tumba el lote (CodeRabbit #1439): se ignora con aviso y el resto sigue."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
_spec = importlib.util.spec_from_file_location('build_reading_catalogue_r', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


class TextosPropiosRotosTest(unittest.TestCase):
    def test_modulo_desconocido_o_id_ajeno_se_ignoran_sin_parar(self):
        modulo = next(iter(builder.MODULE_TITLES))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / builder.TEXTS_DIR
            folder.mkdir(parents=True)
            (folder / 'bueno.json').write_text(json.dumps({'id': 'bueno', 'bloques': [{'modulo': modulo}]}), encoding='utf-8')
            (folder / 'roto.json').write_text(json.dumps({'id': 'roto', 'bloques': [{'modulo': 'inventado'}]}), encoding='utf-8')
            (folder / 'ajeno.json').write_text(json.dumps({'id': 'otro', 'bloques': [{'modulo': modulo}]}), encoding='utf-8')
            self.assertEqual(set(builder.load_own_texts(root)), {'bueno'})


if __name__ == '__main__':
    unittest.main()


class PaginasDerivadasHuerfanasTest(unittest.TestCase):
    """CodeRabbit #1439: apartar un libro nuevo dejaba la página N+1 del catálogo sin publicar y el builder la
    rechazaba como huérfana. Las derivadas que nunca se publicaron se quitan; las publicadas se conservan."""

    def test_quita_solo_las_derivadas_que_nunca_se_publicaron(self):
        import subprocess
        from unittest.mock import patch
        _s = importlib.util.spec_from_file_location('refresh_reading_r', ROOT / 'scripts/refresh-reading-catalogue.py')
        refresh = importlib.util.module_from_spec(_s)
        _s.loader.exec_module(refresh)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def put(rel):
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text('x', encoding='utf-8')
            def git(*a):
                subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', *a], cwd=root, check=True, capture_output=True)
            git('init', '-q')
            put('data/reading-catalogue.json')
            put('recomendaciones/pagina/2/index.html')
            git('add', '-A')
            git('commit', '-qm', 'base')
            put('recomendaciones/pagina/3/index.html')
            put('recomendaciones/autores/nuevo/index.html')
            git('add', '-A')
            with patch.object(refresh, 'ROOT', root), patch.object(refresh, 'read_json', lambda p: {'libros': []}):
                refresh.drop_orphan_pages([])
            self.assertTrue((root / 'recomendaciones/pagina/2/index.html').exists())
            self.assertFalse((root / 'recomendaciones/pagina/3/index.html').exists())
            self.assertFalse((root / 'recomendaciones/autores/nuevo/index.html').exists())
