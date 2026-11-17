"""Quien compara producción con el árbol fuente debe construir el árbol igual que el despliegue.

Clase de fallo (16/11, R4-4): deploy-pages empezó a rehacer lo generado con CATALOGO_HOY y postdeploy-deep-audit
siguió comparando producción con el commit en bruto. /recomendaciones/ derivaba cada día, la paridad semántica
fallaba y se saltaban todas las auditorías de producción posteriores.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / '.github' / 'workflows'
ACCION = './.github/actions/construir-como-despliegue'
# Auditorías que comparan lo servido con el árbol del checkout.
COMPARAN_CON_ARBOL = ('production-semantic-parity.mjs', 'production-professional-resources-audit.mjs',
                      'production-asset-parity.mjs', 'production-global-integrity-audit.mjs')


def jobs():
    for wf in sorted(WF.glob('*.yml')):
        datos = yaml.safe_load(wf.read_text(encoding='utf-8')) or {}
        for nombre, job in (datos.get('jobs') or {}).items():
            yield wf.name, nombre, job.get('steps') or []


class ConstruirComoDespliegue(unittest.TestCase):
    def test_la_cadena_del_dia_solo_vive_en_la_accion(self):
        for wf in sorted(WF.glob('*.yml')):
            texto = wf.read_text(encoding='utf-8')
            self.assertNotIn('--solo-construir', texto, f'{wf.name}: usa {ACCION}, no la cadena a mano')
        accion = (ROOT / ACCION / 'action.yml').read_text(encoding='utf-8')
        self.assertIn('CATALOGO_HOY: ${{ inputs.hoy }}', accion)
        self.assertIn('materializar_generados.py --solo-construir', accion)

    def test_despliegue_y_auditoria_usan_la_accion(self):
        usos = {(wf, job) for wf, job, pasos in jobs() if any(p.get('uses') == ACCION for p in pasos)}
        self.assertIn(('deploy-pages.yml', 'build'), usos)
        self.assertIn(('postdeploy-deep-audit.yml', 'production-parity'), usos)

    def test_quien_compara_con_el_arbol_construye_antes(self):
        for wf, job, pasos in jobs():
            ordenes = [str(p.get('run', '')) for p in pasos]
            # `node --check` solo comprueba sintaxis: no compara nada.
            comparan = [i for i, o in enumerate(ordenes) if any(f'node qa/{s}' in o for s in COMPARAN_CON_ARBOL)]
            if not comparan:
                continue
            construye = [i for i, p in enumerate(pasos) if p.get('uses') == ACCION]
            self.assertTrue(construye and construye[0] < comparan[0],
                            f'{wf}:{job} compara producción con el árbol sin construir antes como el despliegue')

    def test_el_dia_sale_de_version_json(self):
        pasos = next(p for wf, job, p in jobs() if (wf, job) == ('postdeploy-deep-audit.yml', 'production-parity'))
        uso = next(p for p in pasos if p.get('uses') == ACCION)
        self.assertRegex(uso['with']['hoy'], r'steps\.dia\.outputs\.hoy')
        dia = next(p for p in pasos if p.get('id') == 'dia')
        self.assertIn('/version.json', dia['run'])
        self.assertTrue(re.search(r'\["hoy"\]', dia['run']))


if __name__ == '__main__':
    unittest.main()
