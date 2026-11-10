"""Los builders escriben siempre LF.

En Windows, `write_text`/`open(..., 'w')` sin `newline=` traducen `\n` a `\r\n`: el mismo contenido sale con bytes
distintos en local y en CI. Mientras lo generado se versionaba, git lo tapaba (autocrlf); tras el corte de la fase 5
(lo generado ya no se versiona) la huella, la caché y las comparaciones byte a byte dependerían del sistema.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _escribe_texto(n: ast.Call) -> bool:
    f = n.func
    if isinstance(f, ast.Attribute) and f.attr == 'write_text':
        return True
    nombre = f.attr if isinstance(f, ast.Attribute) else getattr(f, 'id', '')
    if nombre in ('open', 'fdopen'):
        modo = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == 'mode'), None)
        return (isinstance(modo, ast.Constant) and isinstance(modo.value, str)
                and any(c in modo.value for c in 'wax') and 'b' not in modo.value)
    return False


class BuildersLF(unittest.TestCase):
    def test_ningun_builder_escribe_texto_sin_newline(self):
        malos = []
        for ruta in sorted((ROOT / 'scripts').glob('build-*.py')):
            for n in ast.walk(ast.parse(ruta.read_text(encoding='utf-8'))):
                if isinstance(n, ast.Call) and _escribe_texto(n) and not any(k.arg == 'newline' for k in n.keywords):
                    malos.append(f'{ruta.relative_to(ROOT).as_posix()}:{n.lineno}')
        self.assertEqual(malos, [], 'añade newline="\\n": en Windows saldría CRLF')

    def test_detecta_las_formas_habituales(self):
        def casa(codigo):
            return _escribe_texto(ast.parse(codigo).body[0].value)
        self.assertTrue(casa('p.write_text(t, encoding="utf-8")'))
        self.assertTrue(casa('open(p, "w", encoding="utf-8")'))
        self.assertTrue(casa('os.fdopen(fd, "a")'))
        self.assertFalse(casa('open(p, "wb")'))
        self.assertFalse(casa('open(p)'))
        self.assertFalse(casa('p.write_bytes(b)'))


if __name__ == '__main__':
    unittest.main()
