import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('selector', ROOT / 'scripts/select-link-check-inputs.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)

class CaseRenameTests(unittest.TestCase):
    def test_case_only_rename_requires_complete_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE).decode().strip()
            git('init', '-q')
            git('config', 'user.name', 'QA')
            git('config', 'user.email', 'qa@example.invalid')
            (root / 'index.html').write_text('<a href="/books/">Libros</a>', encoding='utf-8')
            (root / 'books.html').write_text('<h1>Libros</h1>', encoding='utf-8')
            git('add', '.')
            git('commit', '-qm', 'initial')
            base = git('rev-parse', 'HEAD')
            git('mv', 'books.html', 'Books.html')
            git('commit', '-qm', 'rename')
            result = selector.select(root, 'push', {'before': base}, 'refs/heads/main')
            self.assertEqual(result['scope'], 'full-site')
            self.assertIn('Books.html', result['files'])
            self.assertIn('index.html', result['files'])

if __name__ == '__main__':
    unittest.main()
