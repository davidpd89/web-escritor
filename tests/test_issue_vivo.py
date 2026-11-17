"""Issue vivo por etiqueta (scripts/issue_vivo.py): uno solo, se abre, se actualiza, se cierra y solo desde main."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import issue_vivo  # noqa: E402


def falso(abierto=''):
    llamadas = []

    def llamar(*args):
        llamadas.append(args)
        salida = abierto if args[:2] == ('issue', 'list') else ''
        return subprocess.CompletedProcess(args, 0, stdout=salida, stderr='')
    return llamar, llamadas


def ordenes(llamadas):
    return [a[:2] for a in llamadas if a[:2] != ('label', 'create')]


class IssueVivo(unittest.TestCase):
    def publicar(self, hay_aviso, abierto='', entorno=None, texto='informe'):
        llamar, llamadas = falso(abierto)
        issue_vivo.publicar('x', 'Título', texto, hay_aviso, 'o/r', 'limpio', llamar=llamar,
                            entorno={'GITHUB_REF_NAME': 'main'} if entorno is None else entorno)
        return llamadas

    def test_ciclo(self):
        self.assertEqual(ordenes(self.publicar(True)), [('issue', 'list'), ('issue', 'create')])
        self.assertEqual(ordenes(self.publicar(True, '7')), [('issue', 'list'), ('issue', 'edit')])
        cerrar = self.publicar(False, '7')
        self.assertEqual(ordenes(cerrar), [('issue', 'list'), ('issue', 'close')])
        self.assertIn('7', cerrar[-1])
        self.assertEqual(ordenes(self.publicar(False)), [('issue', 'list')])

    def test_solo_main(self):
        self.assertEqual(self.publicar(True, entorno={'GITHUB_REF_NAME': 'ci/prueba'}), [])
        self.assertTrue(issue_vivo.desde_main({}), 'en local, sin GITHUB_REF_NAME, publica')

    def test_cuerpo_largo_recortado(self):
        llamadas = self.publicar(True, texto='x' * 100000)
        cuerpo = llamadas[-1][llamadas[-1].index('--body') + 1]
        self.assertLess(len(cuerpo), 65536)
        self.assertIn('artefacto', cuerpo)

    def test_empleados_con_issue_lo_usan(self):
        """Clase de fallo: un empleado que reimplementa su issue a mano pierde la guardia de main y el recorte."""
        for nombre in ('empleados_latido.py', 'catalogo_duplicados.py'):
            texto = (ROOT / 'scripts' / nombre).read_text(encoding='utf-8')
            self.assertIn('issue_vivo.publicar(', texto, nombre)
            self.assertNotIn("'issue', 'create'", texto, f'{nombre}: usa issue_vivo.publicar')

    def test_checkout_disperso_trae_el_modulo(self):
        """Un checkout disperso sin scripts/issue_vivo.py rompe el import en Actions aunque en local pase."""
        usuarios = [p.name for p in (ROOT / 'scripts').glob('*.py') if 'import issue_vivo' in p.read_text(encoding='utf-8')]
        usuarios.append('issue_vivo.py')  # también se llama directamente desde los workflows en bash
        self.assertGreaterEqual(len(usuarios), 2)
        for wf in sorted((ROOT / '.github' / 'workflows').glob('*.yml')):
            texto = wf.read_text(encoding='utf-8')
            if 'sparse-checkout:' not in texto:
                continue
            for nombre in usuarios:
                if f'scripts/{nombre}' in texto:
                    # En la lista del checkout, no en un comentario que lo nombre.
                    self.assertRegex(texto, r'(?m)^\s+/?scripts/issue_vivo\.py$',
                                     f'{wf.name} ejecuta {nombre} sin traer issue_vivo.py')


if __name__ == '__main__':
    unittest.main()
