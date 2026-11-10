"""La sincronización del directorio del Atlas publica las páginas de destino que reciben lugares nuevos."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_atlas_directory', ROOT / 'scripts/refresh-atlas-directory.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AllowedPath(unittest.TestCase):
    def test_destination_pages_hub_sitemap_and_search_index(self):
        # 02/11 y 09/11: falló con atlas-literario/dublin y oxford, que muestran lugares del directorio.
        for path in ('atlas-literario/dublin/index.html', 'atlas-literario/oxford/index.html', 'atlas-literario/index.html',
                     'data/atlas/directory.json', 'sitemap.xml', 'pagefind/fragment/es_1.pf_fragment'):
            with self.subTest(path):
                self.assertTrue(mod.allowed_path(path))

    def test_anything_else_stays_out(self):
        for path in ('index.html', 'atlas-literario/../index.html', 'atlas-literario/dublin/app.js',
                     'data/atlas/catalogue.json', 'scripts/build-atlas-pages.py', 'pagefind/../x'):
            with self.subTest(path):
                self.assertFalse(mod.allowed_path(path))


class PendingBotPr(unittest.TestCase):
    """09/11: la PR #1250 cayó en broken-links y se conservaba, así que bloqueaba cada sincronización siguiente."""

    def _refresh(self, merge_state, checks):
        import json
        from unittest import mock
        calls = []

        def gh(*args):
            calls.append(args)
            if args[:2] == ('pr', 'list'):
                return json.dumps([{'headRefName': 'automation/atlas-directory-2026-11-09-1'}])
            if args[:2] == ('pr', 'view'):
                return json.dumps({'number': 1250, 'mergeStateStatus': merge_state, 'statusCheckRollup': checks,
                                   'author': {'is_bot': True, 'login': 'app/github-actions'}})
            return ''

        class Stop(Exception):
            pass

        def command(*args):
            raise Stop   # tras decidir sobre la PR pendiente, la regeneración no interesa aquí
        with mock.patch.object(mod.publication, 'gh', gh), mock.patch.object(mod, 'command', command):
            try:
                mod.refresh(publish=False)
            except Stop:
                pass
        return [c for c in calls if c[:2] == ('pr', 'close')]

    def test_a_red_check_closes_and_regenerates(self):
        self.assertTrue(self._refresh('BLOCKED', [{'name': 'check-links', 'conclusion': 'FAILURE'}]))

    def test_a_pr_still_running_is_kept(self):
        self.assertFalse(self._refresh('BLOCKED', [{'name': 'check-links', 'conclusion': None, 'status': 'IN_PROGRESS'}]))

    def test_behind_main_closes(self):
        self.assertTrue(self._refresh('BEHIND', []))


if __name__ == '__main__':
    unittest.main()
