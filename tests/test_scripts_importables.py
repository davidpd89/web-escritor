"""Un script que un test carga como librería no puede salir al importarse.

Origen (28/11): la carga 46117573426 cayó entera con «check-reading-data salió con 1 sin fallos de contrato (error de
carga de los tests)». tests/test_reading_text_encoding.py (el contrato que aparta libro a libro lo que tenga
mojibake) importa scripts/check-public-text-encoding.py para usar `mojibake_hits`; ese script recorría el HTML público
y hacía `sys.exit(1)` a nivel de módulo, así que con un � en las páginas el contrato moría al importarlo y la puerta
de datos no podía apartar el libro: se perdió el lote. Lo mismo valía para check-public-time-semantics.py, que
cuatro tests cargan con runpy.run_path.

Regla: los módulos importables de scripts/ (nombre con guion bajo) y todo script que un test cargue por ruta
(spec_from_file_location / run_path sin run_name="__main__") no salen fuera de `if __name__ == "__main__":`.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
LOAD = re.compile(r'(spec_from_file_location|run_path)\(.*?scripts["\']?\s*[/,]\s*["\']?(?:scripts/)?([\w.-]+\.py)')


def main_guard(node):
    return isinstance(node, ast.If) and '__main__' in ast.unparse(node.test)


def exits_at_import(source):
    """Líneas de nivel de módulo (fuera de funciones, clases y del bloque __main__) que terminan el proceso."""
    found = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) or main_guard(node):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and ast.unparse(sub.func) in ('sys.exit', 'exit', 'quit', 'os._exit'):
                found.append(sub.lineno)
            elif isinstance(sub, ast.Raise) and sub.exc is not None and 'SystemExit' in ast.unparse(sub.exc):
                found.append(sub.lineno)
    return found


def loaded_by_path():
    names = set()
    for test in (ROOT / 'tests').glob('*.py'):
        for line in test.read_text(encoding='utf-8', errors='ignore').splitlines():
            if 'run_name="__main__"' in line or "run_name='__main__'" in line:
                continue  # se ejecuta como programa a propósito
            names.update(m.group(2) for m in LOAD.finditer(line))
    return {n for n in names if (SCRIPTS / n).is_file()}


def library_scripts():
    importable = {f.name for f in SCRIPTS.glob('*.py') if f.stem.isidentifier()}
    return sorted(importable | loaded_by_path())


class ScriptsImportablesTest(unittest.TestCase):
    def test_library_scripts_do_not_exit_at_import(self):
        bad = {}
        for name in library_scripts():
            try:
                lines = exits_at_import((SCRIPTS / name).read_text(encoding='utf-8'))
            except SyntaxError:
                continue  # otro test vigila la sintaxis
            if lines:
                bad[name] = lines
        self.assertEqual(bad, {}, 'salen al importarse: mover el recorrido a main() bajo if __name__ == "__main__"')

    def test_the_known_cases_are_covered(self):
        covered = set(library_scripts())
        self.assertIn('check-public-text-encoding.py', covered)
        self.assertIn('check-public-time-semantics.py', covered)

    def test_detector(self):
        self.assertTrue(exits_at_import('import sys\nif errors:\n    sys.exit(1)\n'))
        self.assertTrue(exits_at_import('raise SystemExit(2)\n'))
        self.assertFalse(exits_at_import('import sys\ndef main():\n    sys.exit(1)\nif __name__ == "__main__":\n    sys.exit(main())\n'))


if __name__ == '__main__':
    unittest.main()
