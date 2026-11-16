"""Juez de los relojes de la ingesta (scripts/ci_intake_backup.py): desde R4-1 decide con el libro de la noche.

Las reglas están en tests/test_noche.py; aquí, que el wrapper delega en el libro y el contrato del workflow.
"""
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import noche  # noqa: E402

spec = importlib.util.spec_from_file_location('ci_intake_backup', ROOT / 'scripts/ci_intake_backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class JuezTest(unittest.TestCase):
    def juez(self, libro):
        out = io.StringIO()
        with mock.patch.object(noche, 'leer', return_value=libro), redirect_stdout(out), \
                mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
            self.assertEqual(noche.main(['juez']), 0)
        return out.getvalue().strip()

    def test_el_wrapper_usa_el_libro(self):
        self.assertIs(backup.noche, noche)
        self.assertFalse(hasattr(backup, 'api'), 'ya no consulta la API de Actions')

    def test_sin_cargas_esta_noche_carga(self):
        self.assertEqual(self.juez(None), 'run=true')

    def test_con_una_carga_en_curso_no_carga(self):
        libro = noche.abrir(None, noche.datetime.now(noche.timezone.utc), 1, 1, 's', 'cron')[2]
        self.assertEqual(self.juez(libro), 'run=false')


class ContratoWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.yaml = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8').replace('\r\n', '\n')

    def test_workflow_tiene_respaldos_y_concurrencia_en_el_job(self):
        for cron in ("'17 0 * * *'", "'47 1 * * *'", "'17 3 * * *'"):
            self.assertIn(f'cron: {cron}', self.yaml)
        # P0-4: el dispatch del reloj externo (workers/intake-dispatch.mjs) decide como un cron, antes que el
        # dispatch manual (que carga siempre), y descarga el script para hacerlo: sin carga doble.
        reloj = self.yaml.index('workflow_dispatch:true:*) python3 scripts/ci_intake_backup.py')
        self.assertLess(reloj, self.yaml.index('workflow_dispatch:*) echo run=true'))
        self.assertIn("if: github.event_name == 'schedule' || inputs.respaldo", self.yaml)
        # El grupo va en el job intake: un respaldo en cola nunca sustituye a la carga encadenada pendiente.
        self.assertNotIn('\nconcurrency:', self.yaml)
        self.assertIn('    concurrency:\n      group: reading-catalogue-intake', self.yaml)

    def test_un_ensayo_no_entra_en_el_libro(self):
        paso = self.yaml[self.yaml.index('name: Take the night turn'):self.yaml.index('uses: actions/setup-node')]
        self.assertIn('if: ${{ !inputs.dry_run }}', paso)


if __name__ == '__main__':
    unittest.main()
