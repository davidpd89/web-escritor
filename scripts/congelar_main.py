#!/usr/bin/env python3
"""Congela main mientras una carga de libros o un refresco del radar están en marcha (check de PR «Main congelado»).

Cada avance de main durante la PR de datos repite su CI (~75 min) y la ingesta sale con código 75 (StaleMerge); el
24/11 una fusión durante el refresco del radar lo dejó sin regenerar y dos cargas salieron rojas. Hasta ahora era una
norma («consultar carga_en_curso.py antes de fusionar»); este check la hace vinculante: una PR ajena a la carga
espera aquí, sin gastar CI, hasta que no quede ninguna ejecución de los flujos que escriben en main, y solo entonces
se puede fusionar.

No bloquea: las PR de la propia carga (automation/…), la etiqueta `sin-congelar` (emergencias) ni cuando no se puede
mirar (abre en vez de cerrar: un fallo de gh no debe parar el repositorio). Pasado el tope (la carga más larga
observada tarda ~4 h) también abre, avisando.

    python scripts/congelar_main.py            # lee HEAD_REF y ETIQUETAS del entorno (las pone el workflow)
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # módulos hermanos también al cargarlo con importlib
import gh_listas  # noqa: E402

FLUJOS = ('reading-catalogue-sync.yml', 'radar-clock-refresh.yml')
ACTIVOS = ('in_progress', 'queued', 'waiting', 'pending', 'requested')
EXENTAS = ('automation/', 'revision/')  # la carga y su refresco publican por aquí; las de revisión no se fusionan
ETIQUETA = 'sin-congelar'
TOPE_MIN = 300
CADA_S = 120


def _gh(*args):
    return subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', check=True, timeout=120).stdout


def gh_runs(flujo):
    # Una ventana a propósito: las 20 ejecuciones más recientes del flujo; una en curso siempre está entre ellas.
    return gh_listas.ultimas(_gh, 'run', 'list', '-w', flujo, '--json', 'databaseId,status,createdAt,event', n=20)


def activas(consulta=gh_runs, flujos=FLUJOS):
    """[(flujo, id, estado, desde)] de las ejecuciones sin terminar. Propaga el error si no se puede mirar."""
    return [(f, r['databaseId'], r['status'], r['createdAt']) for f in flujos for r in consulta(f)
            if r.get('status') in ACTIVOS]


def exenta(head_ref, etiquetas):
    return head_ref.startswith(EXENTAS) or ETIQUETA in [e.strip() for e in etiquetas.split(',')]


def esperar(head_ref='', etiquetas='', consulta=gh_runs, dormir=time.sleep, ahora=time.monotonic,
            tope_s=TOPE_MIN * 60, cada_s=CADA_S, imprimir=print):
    """0 = se puede fusionar (libre, exenta, no se pudo mirar o tope agotado)."""
    if exenta(head_ref, etiquetas):
        imprimir(f'Exenta de la congelación ({head_ref or "sin rama"}; etiquetas: {etiquetas or "ninguna"}).')
        return 0
    inicio = ahora()
    avisadas = None
    while True:
        try:
            ocupadas = activas(consulta)
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            imprimir(f'::warning::No se pudo mirar si hay carga ({type(exc).__name__}); no se congela.')
            return 0
        if not ocupadas:
            imprimir('Main libre: no hay carga ni refresco del radar en marcha.')
            return 0
        if ahora() - inicio >= tope_s:
            imprimir(f'::warning::Congelación agotada tras {tope_s // 60} min con {len(ocupadas)} ejecución(es) activa(s); se abre.')
            return 0
        ids = sorted(o[1] for o in ocupadas)
        if ids != avisadas:
            avisadas = ids
            for flujo, ident, estado, desde in ocupadas:
                imprimir(f'Main congelado: {flujo} {ident} {estado} (desde {desde}). Espero a que acabe.')
        dormir(cada_s)


def main():
    return esperar(os.environ.get('HEAD_REF', ''), os.environ.get('ETIQUETAS', ''))


if __name__ == '__main__':
    sys.exit(main())
