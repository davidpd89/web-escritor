"""Ningún fichero de código lleva bytes de control invisibles.

Al escribir parches con heredoc, `\\b`, `\\t` o `\\0` acabaron como bytes reales (0x08, 0x09, 0x00). Dentro de un
`r'...'` el `\\b` de límite de palabra pasaba a ser un retroceso literal: la regex no coincidía nunca y nadie lo
veía (`<a\\b` en build-reading-catalogue dejó `newtab` sin efecto tres semanas; dos tests no comprobaban nada).
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODIGO = ('*.py', '*.mjs', '*.js', '*.cjs', '*.ts', '*.yml', '*.yaml', '*.sh', '*.ps1', '*.css', '*.toml')
FUERA = ('pagefind/', 'node_modules/', 'vendor/')
# Tabulador, salto de línea y retorno de carro son normales; cualquier otro byte < 0x20 o 0x7f no.
CONTROL = re.compile(rb'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def ficheros():
    salida = subprocess.run(['git', 'ls-files', '-z', '--', *CODIGO], cwd=ROOT, capture_output=True, check=True).stdout
    return [r for r in salida.decode('utf-8').split('\0') if r and not r.startswith(FUERA)]


def hallazgos(rutas):
    malos = []
    for ruta in rutas:
        try:
            datos = (ROOT / ruta).read_bytes()
        except FileNotFoundError:
            continue
        for n, linea in enumerate(datos.split(b'\n'), 1):
            m = CONTROL.search(linea)
            if m:
                malos.append(f'{ruta}:{n}: byte 0x{m.group(0)[0]:02x}')
                break
    return malos


class SourceControlBytesTest(unittest.TestCase):
    def test_code_has_no_invisible_control_bytes(self):
        rutas = ficheros()
        self.assertGreater(len(rutas), 100)
        self.assertEqual(hallazgos(rutas), [])

    def test_detects_a_backspace_inside_a_raw_regex(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            malo = Path(tmp) / 'malo.py'
            malo.write_bytes(b"import re\nre.sub(r'<a\x08[^>]*>', '', x)\n")
            self.assertEqual(hallazgos([malo.relative_to(ROOT).as_posix()]),
                             [f'{malo.relative_to(ROOT).as_posix()}:2: byte 0x08'])


if __name__ == '__main__':
    unittest.main()
