"""La puerta no se repite cuando falló un test concreto (mismo commit, mismo fallo); sí si se cortó la infraestructura."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('publish_radar_refresh', ROOT / 'scripts/publish-radar-refresh.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


def falso_gh(log, conclusion='failure'):
    def gh(*args):
        if args[1].split('?')[0].endswith('/jobs'):  # por recurso, no por la query (paginación)
            return json.dumps({'jobs': [{'id': 7, 'conclusion': conclusion}, {'id': 8, 'conclusion': 'success'}]})
        return log
    return gh


class FalloDeterministaTest(unittest.TestCase):
    def test_un_test_concreto_no_se_reintenta(self):
        log = '2026-11-23T11:52:14.5Z FALLA: tests/test-page-order.py\n2026-11-23T11:52:15Z exit 1'
        with mock.patch.object(pub, 'gh', falso_gh(log)):
            self.assertTrue(pub.fallo_determinista('o/r', 1))

    def test_un_corte_de_red_si_se_reintenta(self):
        log = '2026-11-23T11:34:12Z gh run cancel 77 failed: HTTP 502: Bad Gateway\nThe runner has received a shutdown signal'
        with mock.patch.object(pub, 'gh', falso_gh(log)):
            self.assertFalse(pub.fallo_determinista('o/r', 1))

    def test_un_job_cancelado_se_reintenta(self):
        with mock.patch.object(pub, 'gh', falso_gh('FALLA: tests/x.py', conclusion='cancelled')):
            self.assertFalse(pub.fallo_determinista('o/r', 1))

    def test_sin_poder_leer_los_registros_se_reintenta(self):
        def roto(*args):
            raise pub.subprocess.CalledProcessError(1, 'gh')
        with mock.patch.object(pub, 'gh', roto):
            self.assertFalse(pub.fallo_determinista('o/r', 1))


if __name__ == '__main__':
    unittest.main()
