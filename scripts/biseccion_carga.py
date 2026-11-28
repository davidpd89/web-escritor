"""Atribuye a un libro un fallo de contrato que no nombra ninguno, buscándolo entre los que cambian esta noche.

28/11: dos lotes (992 libros) se perdieron en la QA de la PR por tests de código que usaban el primer libro del
catálogo real como ejemplo ("Corsarios de Levante… Best Seller"); el fallo no nombraba ningún id, así que la
cuarentena no podía apartar nada y la carga entera paraba. La clase es «un fallo sin atribuir que desaparece si se
quita un libro concreto de los que trae la carga»: se encuentra por bisección, sin leer textos de fallo.

Supuesto (monótono): quitar más libros de la carga no rompe lo que quitar menos arreglaba. Con él basta buscar el
prefijo más corto de los candidatos cuya retirada hace pasar el contrato; el último de ese prefijo es culpable.
Coste: 1 + log2(n) sondas (1000 libros = 11). Si ni retirándolos todos pasa, no es un dato de esta noche: es
código o regla, y se devuelve None para que quien llama decida (la carga para o deja que decida la PR).
"""
from __future__ import annotations

import json
import re
import time


def candidatos(data, published):
    """Ids de la carga que son nuevos o distintos de su versión publicada, en el orden del catálogo (los tests que
    toman «el primero» caen pronto en la búsqueda)."""
    good = {b['id']: b for b in (published or {}).get('libros', [])}
    def generos(d):
        out = {}
        for r in (d or {}).get('libro_categorias', []):
            out.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        return out
    antes, ahora = generos(published), generos(data)
    return [b['id'] for b in data['libros'] if good.get(b['id']) != b or antes.get(b['id']) != ahora.get(b['id'])]


def retirar(data, published, quitar):
    """Copia de `data` sin la carga de `quitar`: un alta sale; un publicado vuelve a su versión (y sus géneros)."""
    quitar = set(quitar)
    good = {b['id']: b for b in (published or {}).get('libros', [])}
    out = json.loads(json.dumps(data))
    out['libros'] = [good.get(b['id'], b) if b['id'] in quitar else b
                     for b in out['libros'] if not (b['id'] in quitar and b['id'] not in good)]
    rel = [r for r in out.get('libro_categorias', []) if r['libro_id'] not in quitar]
    rel += [r for r in (published or {}).get('libro_categorias', []) if r['libro_id'] in quitar and r['libro_id'] in good]
    out['libro_categorias'] = rel
    return out


class SinTiempo(RuntimeError):
    pass


class SinResolver(RuntimeError):
    """La sonda no pudo decir ni «pasa» ni «falla» (la puerta no cargó, un módulo sin terminar): la búsqueda se
    abandona entera; contarlo como «falla» apartaría libros inocentes."""


def culpable(cands, falla, *, hasta=None, reloj=time.monotonic):
    """Primer candidato cuya retirada (junto con los anteriores) hace pasar el contrato, o None si ni retirándolos
    todos pasa. `falla(quitar)` -> True si con esos retirados sigue fallando. `hasta` (en la escala de `reloj`)
    corta con SinTiempo antes de comerse el plazo del job."""
    def probar(quitar):
        if hasta is not None and reloj() >= hasta:
            raise SinTiempo(f'bisección sin terminar: quedaban {hi - lo} candidatos')
        return falla(quitar)
    lo, hi = 0, len(cands)  # quitar cands[:lo] sigue fallando; quitar cands[:hi] pasa (por comprobar)
    if not cands or probar(cands):
        return None
    if len(cands) == 1:
        return cands[0]
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if probar(cands[:mid]):
            lo = mid
        else:
            hi = mid
    return cands[hi - 1]


def culpables(cands, falla, *, hasta=None, reloj=time.monotonic):
    """Todos los culpables: tras cada uno, se busca el siguiente con los hallados ya retirados, hasta que retirarlos
    baste. None si el fallo no se reproduce con la carga entera (inestable), si ni retirando todos los candidatos
    pasa (no es un dato de esta noche o no es monótono) o si el arreglo no aguanta una segunda comprobación."""
    def probar(quitar):  # todas las sondas, también la inicial y las de confirmación, respetan el plazo
        if hasta is not None and reloj() >= hasta:
            raise SinTiempo(f'bisección sin terminar: {len(found)} culpables hallados')
        return falla(quitar)
    found = []
    if not cands or not probar([]):
        return None
    while True:
        rest = [c for c in cands if c not in found]
        nxt = culpable(rest, lambda q: probar(found + q))
        if nxt is None:  # ni retirándolo todo pasa (o el contrato no es monótono / es inestable): no se aparta nada
            return None
        found.append(nxt)
        if not probar(found):
            return found if not probar(found) else None  # pasa dos veces seguidas: no es un acierto inestable


def ids_solo(failures):
    """Ids que `check-reading-data.py --solo` sabe repetir: sin el sufijo de subTest y, si el módulo no cargó, el
    módulo (unittest lo reporta como unittest.loader._FailedTest.<módulo>)."""
    out = []
    for f in failures:
        name = re.sub(r'\s*\(.*\)\s*$', '', f['test']).strip()
        name = name.removeprefix('unittest.loader._FailedTest.')
        if name and name not in out:
            out.append(name)
    return out
