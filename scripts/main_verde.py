#!/usr/bin/env python3
"""Antes de consultar las fuentes, la carga comprueba que main pasa sus contratos (caso 2 de la revisión GPT, 25/11).

La PR de datos corre en la puerta todos los contratos del repositorio. Si dos PR de código verdes por separado dejaron
main en rojo (24/11: #1564 + #1395), la carga gastaba ~2 h en consultar, validar y abrir la PR para caer en la puerta
con un test que ya fallaba en main, y el reintento repetía lo mismo. main-contratos.yml corre esos contratos tras cada
fusión de código; aquí la carga:

  1. espera (hasta ESPERA_MIN) si main-contratos está en curso o en cola: una reparación puede estar comprobándose;
  2. si la última comprobación terminada (sin contar las canceladas por una fusión posterior) es verde, sigue;
  3. si es roja, repite sobre su propio HEAD solo los `FALLA: tests/...` de esa ejecución (confirmar_fallos). Si
     siguen fallando, deja la firma en $RUNNER_TEMP/carga-fallo.json (clase determinista, como el publicador) y sale 1:
     el libro de la noche la anota y ni el reintento ni los relojes repiten la carga hasta que cambie el código. Si ya
     pasan (main se arregló con un commit que no relanzó el flujo, o fue inestable), sigue con un aviso.

Falla abierto: sin el flujo, sin registros legibles o con gh caído, la carga sigue como antes.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirmar_fallos  # noqa: E402

FLUJO = 'main-contratos.yml'
ACTIVOS = ('in_progress', 'queued', 'waiting', 'pending', 'requested')
ESPERA_MIN = 45
CADA_S = 60


def _gh(*args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=60).stdout


def gh_runs():
    salida = _gh('run', 'list', '--workflow', FLUJO, '--branch', 'main', '--limit', '20',
                 '--json', 'databaseId,status,conclusion,headSha,createdAt')
    return json.loads(salida or '[]')


def gh_firmas(run_id):
    ruta = Path(__file__).resolve().parent / 'publish-radar-refresh.py'
    spec = importlib.util.spec_from_file_location('publicador_firmas', ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.firmas_deterministas(os.environ.get('GH_REPO') or os.environ.get('GITHUB_REPOSITORY', ''), run_id)


def estado(runs):
    """('en_curso'|'verde'|'rojo'|'desconocido', run). Las canceladas las sustituyó una fusión posterior."""
    runs = sorted(runs, key=lambda r: r.get('createdAt') or '', reverse=True)
    if any(r.get('status') in ACTIVOS for r in runs):
        return 'en_curso', next(r for r in runs if r.get('status') in ACTIVOS)
    for r in runs:
        if r.get('conclusion') in ('cancelled', 'skipped', None, ''):
            continue
        return ('verde' if r['conclusion'] == 'success' else 'rojo'), r
    return 'desconocido', None


def modo_de(fichero):
    nombre = Path(fichero).name
    if nombre.endswith('.mjs'):
        return 'node'
    return 'unittest' if nombre.startswith('test_') else 'script'


def anotar(firmas, entorno):
    if not entorno.get('RUNNER_TEMP'):
        return
    try:
        Path(entorno['RUNNER_TEMP'], 'carga-fallo.json').write_text(
            json.dumps({'clase': 'determinista', 'firma': 'main rojo: ' + ', '.join(firmas)}, ensure_ascii=False),
            encoding='utf-8')
    except OSError:
        pass


def comprobar(consulta=gh_runs, firmas=gh_firmas, ejecutar=confirmar_fallos.ejecutar, dormir=time.sleep,
              reloj=time.monotonic, imprimir=print, entorno=None, existe=None):
    """0 si la carga puede seguir; 1 si main falla de verdad en su HEAD (con la firma anotada)."""
    entorno = os.environ if entorno is None else entorno
    existe = existe or (lambda f: Path(f).is_file())
    limite = reloj() + ESPERA_MIN * 60
    while True:
        try:
            situacion, run = estado(consulta())
        except Exception as exc:  # noqa: BLE001 - gh caído o sin el flujo: como antes
            imprimir(f'::warning::Sin estado de {FLUJO} ({exc}): la carga sigue.')
            return 0
        if situacion != 'en_curso':
            break
        if reloj() >= limite:
            imprimir(f'::warning::{FLUJO} sigue en curso tras {ESPERA_MIN} min (run {run.get("databaseId")}): la carga sigue.')
            return 0
        imprimir(f'{FLUJO} en curso (run {run.get("databaseId")}): espero {CADA_S}s.')
        dormir(CADA_S)
    if situacion != 'rojo':
        imprimir(f'main: {situacion} en {FLUJO}' + (f' (run {run["databaseId"]}).' if run else '.'))
        return 0
    try:
        fallidos = list(firmas(run['databaseId']))
    except Exception:  # noqa: BLE001
        fallidos = []
    if not fallidos:
        imprimir(f'::warning::{FLUJO} en rojo (run {run["databaseId"]}) sin `FALLA: tests/...` legible: la carga sigue.')
        return 0
    # Caso 8 de la ronda 2 GPT (25/11): un contrato rojo renombrado o borrado después no existe en este HEAD; repetirlo
    # daba «No such file» (script, node) y paraba la carga con un main correcto. No se puede repetir aquí: aviso y
    # fuera; la puerta de la PR de datos pasa los contratos reales.
    desaparecidos = [f for f in fallidos if not existe(f)]
    if desaparecidos:
        imprimir(f'::warning::Contratos rojos que ya no existen en este HEAD: {", ".join(desaparecidos)}; no se repiten.')
        fallidos = [f for f in fallidos if f not in desaparecidos]
        if not fallidos:
            return 0
    imprimir(f'{FLUJO} en rojo (run {run["databaseId"]}, {run.get("headSha", "")[:10]}): repito {len(fallidos)} '
             'contrato(s) sobre este HEAD.')
    siguen = []
    for modo in ('script', 'unittest', 'node'):
        grupo = [f for f in fallidos if modo_de(f) == modo]
        if grupo:
            siguen += confirmar_fallos.confirmar(modo, grupo, ejecutar, imprimir)[0]
    if not siguen:
        imprimir('::warning::Los contratos rojos de main ya pasan sobre este HEAD: la carga sigue.')
        return 0
    anotar(siguen, entorno)
    imprimir(f'::error title=Main en rojo::La PR de datos caería en la puerta con {", ".join(siguen)}. '
             'La carga no consulta las fuentes; la autorreparación de main-contratos lo arregla y el libro de la '
             'noche no la repite con este mismo código.')
    return 1


if __name__ == '__main__':
    sys.exit(comprobar())
