#!/usr/bin/env python3
"""Resultado de una carga en tres estados y clase del fallo (Fable R4-5, D2 y F2).

  publicado  todo fue bien;
  degradado  la carga publicó, pero un paso (altas de Amazon, precios y portadas) falló y se descartó: código 0,
             la cadena sigue y el fallo queda en una issue `fallo` con su firma;
  fallido    no se publicó nada; la clase sale de la etapa en la que saltó (ver CLASE_DE_ETAPA).
             (Un libro malo lo aparta la cuarentena y la carga no falla: `dato` es solo el contrato que no pudo.)

La carga escribe `.ci/reading-intake/resultado.json`; el cierre del turno lo copia al libro de la noche
(scripts/noche.py) y el reintento decide con la clase y la firma, no con «main avanzó».
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import urllib.error
from contextlib import contextmanager
from pathlib import Path

FICHERO = Path('.ci/reading-intake/resultado.json')

# R5-12 (Fable, hallazgos 7 y 8): la clase sale de la ETAPA en la que saltó el fallo, no del texto del mensaje. Antes
# era una expresión regular sobre mensajes (`TLS|SSL` casaba palabras normales, `timed? ?out`...) y la firma salía
# del primer renglón, que en un subproceso es la orden entera. Ahora:
#   transitorio  consulta externa o escritura remota (fuentes, gh, git push): reintentar tiene sentido;
#   dato         un contrato de datos que la cuarentena no pudo resolver: mismo lote, mismo fallo;
#   entorno      la cuarentena o la preparación no encontraron lo que esperaban (versión publicada, checkout):
#                cuenta para el tope de 3 fallidas y no se trata como dato;
#   codigo       construcción y publicación: reintentar sobre el mismo código da lo mismo;
#   desconocido  un fallo fuera de toda etapa declarada: no se da por código sin más; se reintenta dentro del tope
#                y se abre issue para mirarlo de día.
CLASE_DE_ETAPA = {
    'remoto': 'transitorio',
    'consulta': 'transitorio',
    'contrato': 'dato',
    'cuarentena': 'entorno',
    'preparacion': 'entorno',
    'construccion': 'codigo',
    'publicacion': 'codigo',
}
CLASES = (*sorted(set(CLASE_DE_ETAPA.values())), 'desconocido')
# Tipos que dicen «red o servicio» sea cual sea la etapa (por tipo, nunca por texto).
TIPOS_TRANSITORIOS = (urllib.error.URLError, ConnectionError, TimeoutError, socket.timeout)
# Se reintenta de noche (dentro del tope y la guarda por firma) / se abre issue `fallo` para el arreglo de día.
SE_REINTENTA = ('transitorio', 'entorno', 'desconocido')
SE_REPORTA = ('codigo', 'dato', 'desconocido')


@contextmanager
def etapa(nombre: str, regla: str | None = None):
    """Marca la excepción que salga del bloque con su etapa (y su regla, si la hay) sin cambiar su tipo: quien la
    captura por tipo (StaleMerge) la sigue viendo igual. Manda la etapa más interior: no se pisa una ya puesta."""
    if nombre not in CLASE_DE_ETAPA:
        raise ValueError(f'etapa sin clase: {nombre}')
    try:
        yield
    except Exception as exc:
        if getattr(exc, 'etapa', None) is None:
            try:
                exc.etapa, exc.regla = nombre, regla
            except AttributeError:  # una excepción sin __dict__: se envuelve, con la original como causa
                raise RuntimeError(type(exc).__name__) from exc
        raise


def cadena(exc: BaseException | None):
    """La excepción y sus causas (`raise ... from`), de fuera adentro."""
    vistos = set()
    while exc is not None and id(exc) not in vistos:
        vistos.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def _etapa(exc: BaseException) -> tuple[str | None, str | None]:
    for e in cadena(exc):
        if getattr(e, 'etapa', None):
            return e.etapa, getattr(e, 'regla', None)
    return None, None


def clase(exc: BaseException) -> str:
    """Por tipo primero (red, 429 o 5xx en cualquier eslabón ⇒ transitorio; un 4xx no se arregla esperando ⇒
    codigo), y si no, por la etapa."""
    for e in cadena(exc):
        if isinstance(e, urllib.error.HTTPError):
            return 'transitorio' if e.code == 429 or e.code >= 500 else 'codigo'
        if isinstance(e, TIPOS_TRANSITORIOS):
            return 'transitorio'
    nombre, _ = _etapa(exc)
    return CLASE_DE_ETAPA.get(nombre, 'desconocido')


def _identidad(e: BaseException) -> str:
    """Lo estructurado de un eslabón: su tipo y, si lo tiene, el código HTTP o el programa que falló."""
    if isinstance(e, urllib.error.HTTPError):
        return f'{type(e).__name__}:{e.code}'
    if isinstance(e, subprocess.CalledProcessError):
        orden = e.cmd if isinstance(e.cmd, (list, tuple)) else [e.cmd]
        programa = next((Path(str(a)).name for a in orden if str(a).endswith(('.py', '.mjs', '.js', '.sh'))),
                        Path(str(orden[0])).name if orden else '')
        return f'{type(e).__name__}:{programa}'
    return type(e).__name__


def firma(exc: BaseException) -> str:
    """(etapa, tipos de la cadena, regla), sin texto libre: dos noches con el mismo fallo dan la misma firma aunque
    cambien el lote, los ISBN, la ejecución o la redacción del mensaje."""
    nombre, regla = _etapa(exc)
    partes = [nombre or '-', regla or '-', *(_identidad(e) for e in cadena(exc))]
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
    fallida de clase SE_REPORTA. Un transitorio o de entorno no abre issue (lo cubren el reintento y el tope)."""
    if not resultado:
        return []
    if resultado.get('resultado') == 'degradado':
        return list(resultado.get('degradado', []))
    if resultado.get('resultado') == 'fallido' and resultado.get('clase') in SE_REPORTA:
        return [{'paso': 'carga', 'clase': resultado['clase'], 'firma': resultado['firma'], 'error': resultado.get('error', '')}]
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
