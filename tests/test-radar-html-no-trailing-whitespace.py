"""El HTML del radar nunca deja espacios al final de una linea.

El 19/11 el radar se quedo sin activas ni vigilancia: la seccion vacia dejo su
sangria sola en una linea, `git diff --check` rechazo el refresco y la puerta de
todas las PR quedo roja por frescura. Se prueba con el radar vacio y con el real.
"""
import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('br', ROOT / 'scripts' / 'build-radar-opportunities.py')
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)


def sobrantes(html):
    return [n for n, linea in enumerate(html.split('\n'), 1) if linea != linea.rstrip()]


items = br.load_items(ROOT / 'data' / 'radar-opportunities.json')
casos = {'vacio': ([], []), 'real': (items, None)}
for nombre, (lista, vigilancia) in casos.items():
    for dia in (date(2026, 10, 1), date(2026, 11, 19), date(2027, 6, 1)):
        malas = sobrantes(br.build_html(lista, dia, vigilancia))
        assert not malas, f'{nombre} {dia}: espacios finales en las lineas {malas[:5]}'
print('PASS: radar HTML sin espacios finales')
