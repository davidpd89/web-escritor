#!/usr/bin/env python3
"""Resultado de una carga en tres estados y clase del fallo (Fable R4-5, D2 y F2).

  publicado  todo fue bien;
  degradado  la carga publicó, pero un paso (altas de Amazon, precios y portadas) falló y se descartó: código 0,
             la cadena sigue y el fallo queda en una issue `fallo` con su firma;
  fallido    no se publicó nada. Clase:
               transitorio  red, 5xx, límite de peticiones: un reintento sobre el mismo commit tiene sentido;
               codigo       todo lo demás (un contrato o una prueba que falla con este catálogo): reintentar sobre el
                            mismo código da el mismo fallo; se abre una issue `fallo` y espera al arreglo de día.
             (Un libro malo es *dato*: la cuarentena lo aparta y la carga no falla.)

La carga escribe `.ci/reading-intake/resultado.json`; el cierre del turno lo copia al libro de la noche
(scripts/noche.py) y el reintento decide con la clase y la firma, no con «main avanzó».
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import subprocess
import urllib.error
from pathlib import Path

FICHERO = Path('.ci/reading-intake/resultado.json')

# Mensajes de fallos de red o de servicio que se van solos (en `gh`, `git`, urllib y las API de las fuentes).
TRANSITORIO = re.compile(
    r'HTTP (?:Error )?(?:429|5\d\d)\b|\b(?:429|50[0-4]) (?:Too Many|Internal|Bad Gateway|Service|Gateway)'
    r'|timed? ?out|Connection (?:reset|refused|aborted)|Temporary failure in name resolution'
    r'|Could not resolve host|rate limit|secondary rate|RemoteDisconnected|EOF occurred|TLS|SSL',
    re.IGNORECASE)
TIPOS_TRANSITORIOS = (urllib.error.URLError, ConnectionError, TimeoutError, socket.timeout)


def cadena(exc: BaseException | None):
    """La excepción y sus causas (`raise ... from`), de fuera adentro."""
    vistos = set()
    while exc is not None and id(exc) not in vistos:
        vistos.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def _texto(exc: BaseException) -> str:
    partes = [str(exc)]
    if isinstance(exc, subprocess.CalledProcessError):
        partes += [str(exc.stderr or ''), str(exc.output or '')]
    return ' '.join(partes)


def clase(exc: BaseException) -> str:
    """transitorio si algún eslabón de la cadena es de red o de servicio; si no, codigo."""
    for e in cadena(exc):
        if isinstance(e, urllib.error.HTTPError):
            if e.code == 429 or e.code >= 500:
                return 'transitorio'
            continue  # un 4xx de una API (404, 400) no se arregla esperando
        if isinstance(e, TIPOS_TRANSITORIOS) or TRANSITORIO.search(_texto(e)):
            return 'transitorio'
    return 'codigo'


def firma(exc: BaseException) -> str:
    """Huella estable del fallo: tipos y mensajes de la cadena sin números, ids ni rutas temporales. Dos noches con
    el mismo fallo dan la misma firma aunque cambien el lote, los ISBN o la ejecución."""
    partes = []
    for e in cadena(exc):
        texto = str(e).splitlines()[0] if str(e) else ''
        texto = re.sub(r'[0-9a-f]{7,40}', 'H', texto)           # SHA y hashes
        texto = re.sub(r'\d+', 'N', texto)                       # ISBN, números de PR y de ejecución, cuentas
        texto = re.sub(r'(?:/tmp|[A-Z]:\\)[^\s\'"]*', 'P', texto)  # rutas temporales
        partes.append(f'{type(e).__name__}:{texto[:200]}')
    return hashlib.sha1('|'.join(partes).encode('utf-8')).hexdigest()[:12]


def _paso(nombre: str, exc: BaseException) -> dict:
    return {'paso': nombre, 'clase': clase(exc), 'firma': firma(exc),
            'error': f'{type(exc).__name__}: {str(exc)[:300]}'}


def degradado(fallos: dict[str, BaseException]) -> dict:
    """Publicó, pero estos pasos fallaron y se descartaron."""
    pasos = [_paso(nombre, exc) for nombre, exc in fallos.items()]
    return {'resultado': 'degradado' if pasos else 'publicado', 'clase': None, 'firma': None, 'degradado': pasos}


def fallido(exc: BaseException) -> dict:
    return {'resultado': 'fallido', 'clase': clase(exc), 'firma': firma(exc), 'degradado': [],
            'error': f'{type(exc).__name__}: {str(exc)[:300]}'}


def escribir(root: Path, resultado: dict) -> None:
    destino = root / FICHERO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def leer(root: Path) -> dict | None:
    try:
        return json.loads((root / FICHERO).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


# --- Issue `fallo` (una por firma) --------------------------------------------------------------------------------

def a_reportar(resultado: dict | None) -> list[dict]:
    """Lo que necesita un arreglo de día: cada paso descartado de una carga degradada y el fallo de código de una
    fallida. Un transitorio no abre issue (lo cubre el reintento)."""
    if not resultado:
        return []
    if resultado.get('resultado') == 'degradado':
        return list(resultado.get('degradado', []))
    if resultado.get('resultado') == 'fallido' and resultado.get('clase') == 'codigo':
        return [{'paso': 'carga', 'clase': 'codigo', 'firma': resultado['firma'], 'error': resultado.get('error', '')}]
    return []


def titulo(fallo: dict) -> str:
    return f"Carga nocturna: {fallo['paso']} falla [firma {fallo['firma']}]"


def reportar(resultado: dict | None, gh, enlace: str) -> list[str]:
    """Abre una issue `fallo` por firma o comenta en la que ya está abierta. `gh(args) -> stdout`."""
    hechos = []
    for fallo in a_reportar(resultado):
        abiertas = json.loads(gh(['issue', 'list', '--label', 'fallo', '--state', 'open', '--limit', '100',
                                  '--search', f"\"firma {fallo['firma']}\" in:title", '--json', 'number,title']))
        numero = next((i['number'] for i in abiertas if f"[firma {fallo['firma']}]" in i['title']), None)
        cuerpo = (f"Ejecución: {enlace}\n\nPaso: `{fallo['paso']}` · clase: `{fallo['clase']}` · "
                  f"firma: `{fallo['firma']}`\n\n```\n{fallo['error']}\n```\n")
        if numero:
            gh(['issue', 'comment', str(numero), '--body', 'Se repite.\n\n' + cuerpo])
            hechos.append(f'comentada #{numero}')
        else:
            gh(['issue', 'create', '--label', 'fallo', '--title', titulo(fallo), '--body',
                cuerpo + '\nLa abrió la carga nocturna (scripts/resultado_carga.py). Se arregla de día.'])
            hechos.append(f"abierta {fallo['firma']}")
    return hechos


def _gh(args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True, encoding='utf-8').stdout


if __name__ == '__main__':
    import os
    import sys
    enlace = f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/" \
             f"{os.environ.get('GITHUB_RUN_ID', '')}"
    if sys.argv[1:] != ['issue']:
        raise SystemExit('uso: resultado_carga.py issue')
    for linea in reportar(leer(Path.cwd()), _gh, enlace):
        print(linea)
