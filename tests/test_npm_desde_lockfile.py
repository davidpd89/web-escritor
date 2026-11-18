"""Los workflows instalan desde el lockfile lo que ya está en package.json.

Clase de fallo (#1420, 17/11): `npm install --global pa11y-ci@5.0.0` ignoraba el lockfile y resolvía la última
versión de puppeteer-core del rango; mientras npm propagaba una recién publicada, un shard cayó con 404. Con
`npm ci` y `npx --no-install` las versiones son las fijadas y la CI es reproducible.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAQUETES = set()
_pkg = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
for _campo in ('dependencies', 'devDependencies'):
    PAQUETES |= set(_pkg.get(_campo, {}))

INSTALAR_FUERA = re.compile(r'npm\s+(?:install|i|add)\s+(?:--global|-g)\b([^\n]*)')
NPX_BAJANDO = re.compile(r'npx\s+(?:--yes|-y)\s+(@?[\w./-]+)')


def _nombre(spec):
    """«pa11y-ci@5.0.0» -> «pa11y-ci»; «@scope/x@1» -> «@scope/x»."""
    return spec[:spec.index('@', 1)] if '@' in spec[1:] else spec


def _ficheros():
    for carpeta in ('.github/workflows', '.github/actions'):
        yield from sorted((ROOT / carpeta).rglob('*.yml'))


class NpmDesdeLockfileTest(unittest.TestCase):
    def test_hay_paquetes(self):
        self.assertIn('pa11y-ci', PAQUETES)

    def test_ningun_workflow_instala_fuera_del_lockfile_un_paquete_fijado(self):
        fuera = []
        for f in _ficheros():
            texto = f.read_text(encoding='utf-8')
            for m in INSTALAR_FUERA.finditer(texto):
                for spec in m.group(1).split():
                    if not spec.startswith('-') and _nombre(spec) in PAQUETES:
                        fuera.append(f'{f.relative_to(ROOT)}: npm install --global {spec}')
            for m in NPX_BAJANDO.finditer(texto):
                if _nombre(m.group(1)) in PAQUETES:
                    fuera.append(f'{f.relative_to(ROOT)}: npx --yes {m.group(1)}')
        self.assertEqual(fuera, [], 'usar `npm ci` y `npx --no-install`')

    def test_detecta_el_caso_original(self):
        m = INSTALAR_FUERA.search('run: npm install --global pa11y-ci@5.0.0')
        self.assertEqual(_nombre(m.group(1).split()[0]), 'pa11y-ci')
        self.assertEqual(_nombre('@scope/x@1'), '@scope/x')


if __name__ == '__main__':
    unittest.main()
