"""Caso 23 de la revisión GPT (25/11): la derivación de IndexNow reconstruye la web anterior antes de subir el artefacto
de Pages; si fallaba (BEFORE_SHA que no es ancestro, build antiguo roto, disco), no se desplegaba. Ahora se despliega
con la lista vacía y un aviso. Se ejecuta el bloque real del paso con un `python` simulado.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which('bash')


def paso():
    flujo = yaml.safe_load((ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8'))
    for job in flujo['jobs'].values():
        for step in job.get('steps', []):
            if step.get('name') == 'Derive changed public URLs for IndexNow':
                return step['run']
    raise AssertionError('falta el paso de IndexNow')


@unittest.skipUnless(BASH, 'sin bash')
class IndexNowNoBloqueaTest(unittest.TestCase):
    def correr(self, before):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_, temp = tmp / 'repo', tmp / 'bin', tmp / 'temp'
            for d in (repo, bin_, temp):
                d.mkdir()
            git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false']
            subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
            subprocess.run([*git, 'commit', '-q', '--allow-empty', '-m', 'x'], cwd=repo, check=True)
            stub = bin_ / 'python'
            stub.write_text('#!/bin/sh\nif [ "$2" = empty ]; then echo vacio > "$4"; exit 0; fi\nexit 3\n', encoding='utf-8')
            stub.chmod(0o755)
            env = {**os.environ, 'PATH': f'{bin_}{os.pathsep}{os.environ["PATH"]}', 'RUNNER_TEMP': str(temp),
                   'BEFORE_SHA': before}
            hecho = subprocess.run([BASH, '-c', paso()], cwd=repo, env=env, capture_output=True, text=True)
            salida = (temp / 'indexnow-urls.json').read_text().strip() if (temp / 'indexnow-urls.json').exists() else None
            return hecho.returncode, salida, hecho.stdout + hecho.stderr

    def test_sha_que_no_es_ancestro_despliega_sin_indexnow(self):
        rc, salida, log = self.correr('ab' * 20)
        self.assertEqual(rc, 0, log)
        self.assertEqual(salida, 'vacio')
        self.assertIn('IndexNow sin derivar', log)

    def test_sin_before_sigue_igual(self):
        self.assertEqual(self.correr('')[:2], (0, 'vacio'))


if __name__ == '__main__':
    unittest.main()
