"""Contrato de la cola de fusiones: main no se mueve durante la carga nocturna de libros.

18/11: la cola local fusionó #1433 con el lote 2 en curso (tope de espera que acababa fusionando) y el publicador
tuvo que cerrar su PR y repetir la CI. Aquí se fija la regla y que toda puesta al día y toda fusión pasan por ella.
"""
import ast
import datetime as dt
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('cola_fusiones', ROOT / 'scripts/cola_fusiones.py')
cola = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cola)


def a(hhmm):
    h, m = map(int, hhmm.split(':'))
    return dt.datetime(2026, 11, 18, h, m, tzinfo=dt.timezone.utc)


def test_ventana_de_carga_bloquea_aunque_no_haya_carga():
    for hora in ('00:00', '00:17', '03:17', '05:29'):
        assert not cola.main_puede_moverse(a(hora), 0), hora


def test_carga_viva_bloquea_de_dia_y_sin_tope():
    for vivas in (1, 2):
        assert not cola.main_puede_moverse(a('09:00'), vivas)
    assert not cola.main_puede_moverse(a('09:00'), None), 'si gh falla no se sabe si hay carga: no se mueve main'
    assert cola.main_puede_moverse(a('05:30'), 0)
    assert cola.main_puede_moverse(a('23:59'), 0)


def test_crons_de_la_carga_caen_en_la_ventana():
    wf = yaml.safe_load((ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8'))
    disparos = (wf.get('on') or wf.get(True))['schedule']
    inicio, fin = cola.VENTANA_CARGA
    for d in disparos:
        minuto, hora = d['cron'].split()[:2]
        t = dt.time(int(hora), int(minuto))
        assert inicio <= t < fin, f'cron {d["cron"]} fuera de VENTANA_CARGA: amplía la ventana o mueve el cron'


def test_toda_puesta_al_dia_y_fusion_espera_a_main_libre():
    arbol = ast.parse((ROOT / 'scripts/cola_fusiones.py').read_text(encoding='utf-8'))
    for f in (n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)):
        espera = None
        for nodo in sorted((n for n in ast.walk(f) if isinstance(n, ast.Call)), key=lambda n: (n.lineno, n.col_offset)):
            nombre = getattr(nodo.func, 'id', getattr(nodo.func, 'attr', ''))
            if nombre == 'esperar_main_libre':
                espera = nodo.lineno
            args = [x.value for x in nodo.args if isinstance(x, ast.Constant)]
            if nombre == 'gh' and ('merge' in args or 'update-branch' in args):
                assert espera is not None, f'{f.name}:{nodo.lineno} mueve main sin esperar_main_libre antes'
                espera = None  # cada movimiento necesita su propia espera (la carga puede empezar entre medias)


def test_estado_checks_requerido_ausente_es_pendiente():
    req = {'A', 'B'}
    assert cola.estado_checks([{'name': 'A', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}], req) == 'pendiente B'
    rollup = [{'name': 'A', 'status': 'COMPLETED', 'conclusion': 'FAILURE', 'startedAt': '1'},
              {'name': 'A', 'status': 'COMPLETED', 'conclusion': 'SUCCESS', 'startedAt': '2'},
              {'context': 'B', 'state': 'SUCCESS'}]
    assert cola.estado_checks(rollup, req) == 'verde'
    rollup[2] = {'context': 'B', 'state': 'FAILURE'}
    assert cola.estado_checks(rollup, req) == 'roja B=FAILURE'

