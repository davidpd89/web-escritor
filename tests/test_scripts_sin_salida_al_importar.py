"""Un script que los tests cargan como módulo no puede salir del proceso al importarse.

Origen (28/11): la carga 46117573426 publicó siete fichas con «�» y su puerta de datos no apartó ninguna.
tests/test_reading_text_encoding.py cargaba scripts/check-public-text-encoding.py con exec_module para reutilizar
su detector, pero ese script recorría la web entera al importarse y terminaba con sys.exit(1): el SystemExit mató
check-reading-data antes de escribir sus fallos y la carga perdió el lote con «error de carga de los tests».
Este guardián cubre la clase (cualquier script cargado así), y check-reading-data trata un contrato que no carga
como un fallo más en vez de morir con él."""
import ast
import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOADS = re.compile(r'scripts/([A-Za-z0-9_.-]+\.py)')
EXITS = {'sys.exit', 'exit', 'quit', 'os._exit'}

_spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


def is_main_guard(node):
    """Solo `if __name__ == '__main__'` (en cualquier orden); `!=` sí corre al importar."""
    test = node.test if isinstance(node, ast.If) else None
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
        return False
    sides = [test.left, test.comparators[0]]
    return (any(isinstance(s, ast.Name) and s.id == '__name__' for s in sides)
            and any(isinstance(s, ast.Constant) and s.value == '__main__' for s in sides))


def exits_on_import(tree):
    """Líneas que corren al importar (fuera de funciones y del bloque __main__; el cuerpo de una clase sí corre)."""
    hits = []

    def visit(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return
        if isinstance(node, ast.Call) and ast.unparse(node.func) in EXITS:
            hits.append(node.lineno)
        if isinstance(node, ast.Raise) and node.exc is not None and 'SystemExit' in ast.unparse(node.exc):
            hits.append(node.lineno)
        for child in ast.iter_child_nodes(node):
            visit(child)

    for node in tree.body:
        if is_main_guard(node):
            for other in node.orelse:
                visit(other)
        else:
            visit(node)
    return hits


def scripts_loaded_as_modules():
    found = set()
    for test in (ROOT / 'tests').glob('*.py'):
        text = test.read_text(encoding='utf-8', errors='ignore')
        if 'exec_module' in text or 'run_path' in text:
            found |= set(LOADS.findall(text))
    return sorted(n for n in found if (ROOT / 'scripts' / n).is_file())


class ScriptsDoNotExitOnImport(unittest.TestCase):
    def test_scripts_loaded_by_tests_do_not_exit_when_imported(self):
        names = scripts_loaded_as_modules()
        self.assertIn('check-public-text-encoding.py', names)  # el caso que originó esto sigue cubierto
        bad = {n: lines for n in names
               if (lines := exits_on_import(ast.parse((ROOT / 'scripts' / n).read_text(encoding='utf-8'))))}
        self.assertEqual(bad, {}, 'mover el trabajo a main() bajo if __name__ == "__main__"')

    def test_detector_sees_exits_outside_the_main_guard(self):
        self.assertEqual(exits_on_import(ast.parse('import sys\nif 1:\n    sys.exit(1)\n')), [3])
        self.assertEqual(exits_on_import(ast.parse('raise SystemExit(2)\n')), [1])
        self.assertEqual(exits_on_import(ast.parse('import sys\nclass C:\n    sys.exit(1)\n')), [3])
        self.assertEqual(exits_on_import(ast.parse('import sys\nif __name__ != "__main__":\n    sys.exit(1)\n')), [3])
        self.assertEqual(exits_on_import(ast.parse('class C:\n    def f(self):\n        raise SystemExit(1)\n')), [])
        self.assertEqual(exits_on_import(ast.parse(
            'def main():\n    raise SystemExit(1)\nif __name__ == "__main__":\n    raise SystemExit(main())\n')), [])

    def test_encoding_detector_imports_without_scanning_the_site(self):
        spec = importlib.util.spec_from_file_location('enc', ROOT / 'scripts/check-public-text-encoding.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # antes: SystemExit(1) si la web tenía un «�»
        self.assertTrue(list(module.mojibake_hits('Ave C�sar')))


class ContractThatDoesNotLoad(unittest.TestCase):
    def test_a_contract_that_exits_on_import_is_one_more_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'contrato_que_sale.py').write_text('import sys\nsys.exit(1)\n', encoding='utf-8')
            (Path(tmp) / 'contrato_sano.py').write_text(
                'import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n', encoding='utf-8')
            sys.path.insert(0, tmp)
            try:
                suite, broken = check.load(['contrato_que_sale', 'contrato_sano'])
            finally:
                sys.path.remove(tmp)
                sys.modules.pop('contrato_que_sale', None)
                sys.modules.pop('contrato_sano', None)
        self.assertEqual([b['test'] for b in broken], ['contrato_que_sale'])
        self.assertIn('SystemExit', broken[0]['texto'])
        self.assertEqual(suite.countTestCases(), 1)  # el sano sigue corriendo y apartando sus libros


if __name__ == '__main__':
    unittest.main()
