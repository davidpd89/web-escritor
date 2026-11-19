#!/usr/bin/env python3
"""reverify_radar: renueva verified_at solo si la fuente sigue mostrando el plazo; nada más cambia."""
import copy
import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reverify_radar', ROOT / 'scripts' / 'reverify_radar.py')
rr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = rr
spec.loader.exec_module(rr)

fails = []
def check(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)

# Detección de fecha en formatos habituales
check(rr.fecha_en_texto('<p>Plazo hasta el 30 de noviembre de 2026</p>', '2026-11-30'), '«30 de noviembre de 2026»')
check(rr.fecha_en_texto('hasta el 30 noviembre', '2026-11-30'), '«30 noviembre»')
check(rr.fecha_en_texto('cierre 30/11/2026', '2026-11-30'), 'dd/mm/aaaa')
check(rr.fecha_en_texto('cierre 2026-11-30', '2026-11-30'), 'ISO')
check(not rr.fecha_en_texto('hasta el 130 de noviembre', '2026-11-30'), 'no confunde 130 con 30')
check(not rr.fecha_en_texto('hasta el 30 de diciembre', '2026-11-30'), 'otro mes no confirma')
check(not rr.fecha_en_texto('<script>var x="30 de noviembre"</script>nada', '2026-11-30'), 'el script no cuenta')

HOY = date(2026, 11, 19)
base = {'items': [
    {'id': 'a', 'deadline': '2026-11-30', 'verified_at': '2026-10-03', 'source_url': 'u/a', 'title': 'A'},
    {'id': 'b', 'deadline': '2026-12-15', 'verified_at': '2026-10-03', 'source_url': 'u/b', 'title': 'B'},
    {'id': 'c', 'deadline': '2026-12-20', 'verified_at': '2026-10-03', 'source_url': 'u/c', 'title': 'C'},
    {'id': 'd', 'deadline': '2026-11-01', 'verified_at': '2026-10-03', 'source_url': 'u/d', 'title': 'D'},  # vencida
    {'id': 'e', 'deadline': '2026-12-31', 'verified_at': '2026-11-15', 'source_url': 'u/e', 'title': 'E'},  # reciente
]}
paginas = {'u/a': 'hasta el 30 de noviembre', 'u/b': 'sin plazo ya'}
def fetch(url):
    if url == 'u/c':
        raise OSError('403')
    if url in ('u/d', 'u/e'):
        raise AssertionError('no debe consultarse ' + url)
    return paginas[url]

data = copy.deepcopy(base)
inf = rr.reverificar(data, HOY, fetch=fetch, pausa=0)
by = {i['id']: i for i in data['items']}
check(inf['confirmadas'] == ['a'] and by['a']['verified_at'] == '2026-11-19', 'confirmada: verified_at = hoy')
check(by['b']['verified_at'] == '2026-10-03' and by['c']['verified_at'] == '2026-10-03', 'sin confirmar y con error: no se renueva')
check({p['id'] for p in inf['sin_confirmar']} == {'b', 'c'}, 'informe de las no confirmadas')
check(by['d']['verified_at'] == '2026-10-03' and by['e']['verified_at'] == '2026-11-15', 'vencida y reciente: ni se consultan')
others = lambda d: [{k: v for k, v in i.items() if k != 'verified_at'} for i in d['items']]
check(others(data) == others(base), 'ningún otro campo cambia')
sys.exit(1 if fails else 0)
