import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'scripts/build-sitemap.py'


class SitemapSilentErrors(unittest.TestCase):
    def test_publication_generator_does_not_silence_input_errors(self):
        source = PATH.read_text(encoding='utf-8')
        tree = ast.parse(source, filename=str(PATH))
        problems = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == 'errors' and isinstance(keyword.value, ast.Constant) and keyword.value.value == 'ignore':
                        problems.append((node.lineno, 'lectura con errors=ignore'))
            if isinstance(node, ast.ExceptHandler):
                if any(isinstance(statement, (ast.Pass, ast.Continue)) for statement in node.body):
                    problems.append((node.lineno, 'excepción descartada sin diagnóstico'))
        self.assertFalse(problems, '\n'.join(f'{PATH.relative_to(ROOT)}:{line}: {message}' for line, message in problems))


if __name__ == '__main__':
    unittest.main()