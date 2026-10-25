import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('link_unicode_selector', ROOT / 'scripts/select-link-check-inputs.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class UnicodeLinkSelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'QA')
        self.git('config', 'user.email', 'qa@example.invalid')
        (self.root / 'index.html').write_text('<p>inicio</p>', encoding='utf-8')
        self.commit()
        self.base = self.git('rev-parse', 'HEAD').strip()

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, stderr=subprocess.PIPE).decode('utf-8')

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')

    def test_unicode_public_pages_are_not_dropped(self):
        for filename in ('reseñas.html', 'niñez.html', 'café.html'):
            with self.subTest(filename=filename):
                path = self.root / filename
                path.write_text('<p>contenido</p>', encoding='utf-8')
                self.commit()
                result = mod.select(self.root, 'push', {'before': self.base}, 'refs/heads/main')
                self.assertIn(filename, result['files'])

    def test_unsafe_paths_remain_rejected(self):
        for path in ('../escape.html', 'bad;command.html', '$(touch-pwned).html'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                mod.public_html([path])


if __name__ == '__main__':
    unittest.main()
