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
    python scripts/congelar_main.py congelar   # al empezar una carga: las PR abiertas ajenas pasan a borrador
    python scripts/congelar_main.py descongelar  # al acabar una carga (segador): vuelven, si no queda otra

El check solo corre al abrir o actualizar la PR: una PR que ya estaba verde antes de la carga se podía fusionar en
mitad de ella (caso 6 de la revisión GPT, 25/11; el 23/11 se fusionaron dos con una carga en marcha). Al empezar,
la carga pasa a borrador las PR abiertas que no son de la carga, con la etiqueta ETIQUETA_CARGA (un borrador no
se fusiona, ni a mano ni con auto-merge, y no gasta runners esperando); al acabar la última carga de la cola
vuelven a «lista para revisar» solo las que llevan esa etiqueta (los borradores del autor siguen siéndolo). Pasar a
borrador y volver no dispara la CI (los flujos no escuchan converted_to_draft ni ready_for_review).
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
ETIQUETA_CARGA = 'congelada-por-carga'
# Pasar a borrador desactiva el auto-merge y volver a «lista» no lo reactiva: sin anotarlo, una reparación que iba a
# entrar sola se quedaba abierta tras la noche (caso 1 de la ronda 2 GPT, 25/11).
ETIQUETA_AUTO = 'congelada-con-auto-merge'
# El listado de Actions puede tardar en mostrar la carga que la anterior acaba de despachar (caso 2 de la ronda 2):
# el segador mira dos veces, con esta pausa, antes de devolver las PR.
CONFIRMAR_S = 90
CARGA = 'reading-catalogue-sync.yml'
ERRORES = 3  # consultas fallidas seguidas antes de abrir: un 502 suelto de gh no abre main en plena carga


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
    errores = 0
    while True:
        try:
            ocupadas = activas(consulta)
            errores = 0
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            errores += 1
            if errores >= ERRORES or ahora() - inicio >= tope_s:
                imprimir(f'::warning::No se pudo mirar si hay carga ({type(exc).__name__}, {errores} veces); no se congela.')
                return 0
            imprimir(f'No se pudo mirar si hay carga ({type(exc).__name__}); reintento en {cada_s} s.')
            dormir(cada_s)
            continue
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


def _abiertas(gh=_gh):
    return gh_listas.lista(gh, 'pr', 'list', '--base', 'main', '--state', 'open',
                           '--json', 'number,headRefName,isDraft,labels,autoMergeRequest')


def _nombres(pr):
    return [e.get('name', '') for e in pr.get('labels') or []]


def congelar(gh=_gh, imprimir=print):
    """Pasa a borrador las PR abiertas ajenas a la carga. Falla abierto: un error deja la PR como estaba."""
    hechas = []
    try:
        prs = _abiertas(gh)
    except (subprocess.SubprocessError, OSError, ValueError, gh_listas.Truncada) as exc:
        imprimir(f'::warning::No se pudieron listar las PR para congelarlas ({type(exc).__name__}).')
        return hechas
    # `gh pr edit --add-label` falla si la etiqueta no existe: sin esto no se congelaba ninguna PR (25/11).
    for nombre in (ETIQUETA_CARGA, ETIQUETA_AUTO):
        try:
            gh('label', 'create', nombre, '--force', '--color', 'BFD4F2', '--description', 'scripts/congelar_main.py')
        except (subprocess.SubprocessError, OSError) as exc:
            imprimir(f'::warning::No se pudo asegurar la etiqueta {nombre} ({type(exc).__name__}).')
    for pr in prs:
        if pr.get('isDraft') or exenta(pr.get('headRefName', ''), ','.join(_nombres(pr))):
            continue
        numero = str(pr['number'])
        try:  # la etiqueta primero: si falla el borrador, descongelar la vuelve a dejar como estaba
            etiquetas = ETIQUETA_CARGA + (',' + ETIQUETA_AUTO if pr.get('autoMergeRequest') else '')
            gh('pr', 'edit', numero, '--add-label', etiquetas)
            gh('pr', 'ready', numero, '--undo')
            hechas.append(pr['number'])
        except (subprocess.SubprocessError, OSError) as exc:
            imprimir(f'::warning::PR #{numero} sin congelar ({type(exc).__name__}).')
    imprimir(f'Congeladas durante la carga: {hechas or "ninguna"}.')
    return hechas


def descongelar(gh=_gh, consulta=gh_runs, imprimir=print, dormir=time.sleep, pausa_s=CONFIRMAR_S):
    """Devuelve a «lista para revisar» las PR que congeló la carga, si no queda ninguna carga activa ni en cola.

    Con auto-merge anotado al congelar, lo vuelve a activar. Las etiquetas solo se quitan si todo salió bien: una PR a
    medias la retoma el final de la siguiente carga."""
    try:
        quedan = activas(consulta, (CARGA,))
        if not quedan and pausa_s:
            dormir(pausa_s)
            quedan = activas(consulta, (CARGA,))
        prs = [pr for pr in _abiertas(gh) if ETIQUETA_CARGA in _nombres(pr)]
    except (subprocess.SubprocessError, OSError, ValueError, gh_listas.Truncada) as exc:
        imprimir(f'::warning::No se pudo descongelar ({type(exc).__name__}); lo hará el final de la próxima carga.')
        return []
    if quedan:
        imprimir(f'Queda carga activa ({[q[1] for q in quedan]}): siguen congeladas {[p["number"] for p in prs]}.')
        return []
    hechas = []
    for pr in prs:
        numero = str(pr['number'])
        try:
            if pr.get('isDraft'):
                gh('pr', 'ready', numero)
            if ETIQUETA_AUTO in _nombres(pr) and not pr.get('autoMergeRequest'):
                gh('pr', 'merge', numero, '--auto', '--squash')
            gh('pr', 'edit', numero, '--remove-label',
               ETIQUETA_CARGA + (',' + ETIQUETA_AUTO if ETIQUETA_AUTO in _nombres(pr) else ''))
            hechas.append(pr['number'])
        except (subprocess.SubprocessError, OSError) as exc:
            imprimir(f'::warning::PR #{numero} sigue congelada ({type(exc).__name__}).')
    imprimir(f'Descongeladas: {hechas or "ninguna"}.')
    return hechas


def main(argv=None):
    accion = (argv if argv is not None else sys.argv[1:])[:1]
    if accion == ['congelar']:
        congelar()
        return 0
    if accion == ['descongelar']:
        descongelar()
        return 0
    return esperar(os.environ.get('HEAD_REF', ''), os.environ.get('ETIQUETAS', ''))


if __name__ == '__main__':
    sys.exit(main())
