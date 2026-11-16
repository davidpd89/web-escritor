#!/usr/bin/env python3
"""Listas de GitHub que no se cortan en silencio (Fable R4-12, F9).

`gh run|pr|issue list` devuelve como mucho `--limit` elementos (30 o 20 si no se pone) y la API REST, `per_page`;
ninguno avisa de que quedan más. Una lista cortada parecía completa: una PR de la carga que no se veía, una
ejecución en curso que no contaba. Toda lista pasa por aquí y dice qué quiere:

  lista(gh, *args, tope)        todas; si llegan `tope`, `Truncada` (mejor fallar que decidir con media lista);
  ultimas(gh, *args, n)         las n más recientes a propósito (gh ordena de nueva a antigua): una ventana;
  rest_todas(api, ruta, clave)  REST página a página hasta una página corta;
  rest_ultimas(api, ruta, clave, n)  REST, la primera página de n a propósito.

tests/test_gh_listas.py exige que ningún script use `--limit` o `per_page` fuera de este módulo.
"""
from __future__ import annotations

import json

TOPE = 200
POR_PAGINA = 100
MAX_PAGINAS = 50


class Truncada(RuntimeError):
    """La lista llegó al tope: puede haber más elementos que no se ven."""


def _json(salida):
    return json.loads(salida or '[]') if isinstance(salida, (str, bytes)) else (salida or [])


def lista(gh, *args, tope: int = TOPE) -> list:
    """`gh <args> --limit tope` completa. `gh(*args)` devuelve el stdout (o el JSON ya leído)."""
    items = _json(gh(*args, '--limit', str(tope)))
    if len(items) >= tope:
        raise Truncada(f'gh {" ".join(args[:2])} llegó al tope de {tope}: la lista puede estar incompleta')
    return items


def ultimas(gh, *args, n: int) -> list:
    """Las `n` más recientes, a propósito: una ventana, no la lista entera."""
    return _json(gh(*args, '--limit', str(n)))


def _con(ruta: str, **params) -> str:
    return ruta + ('&' if '?' in ruta else '?') + '&'.join(f'{k}={v}' for k, v in params.items())


def rest_todas(api, ruta: str, clave: str | None = None, por_pagina: int = POR_PAGINA,
               max_paginas: int = MAX_PAGINAS) -> list:
    """Todas las páginas de un listado REST. `api(ruta)` devuelve el JSON; `clave` es la lista dentro del objeto
    (`workflow_runs`, `jobs`, `artifacts`) o None si la respuesta ya es una lista."""
    todo = []
    for pagina in range(1, max_paginas + 1):
        datos = api(_con(ruta, per_page=por_pagina, page=pagina))
        items = datos[clave] if clave else datos
        todo += items
        if len(items) < por_pagina:
            return todo
    raise Truncada(f'{ruta}: más de {max_paginas} páginas')


def rest_ultimas(api, ruta: str, clave: str | None, n: int) -> list:
    """Los `n` primeros (los más recientes en los listados de Actions), a propósito."""
    datos = api(_con(ruta, per_page=n))
    return datos[clave] if clave else datos
