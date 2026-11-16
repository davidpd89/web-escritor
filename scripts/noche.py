#!/usr/bin/env python3
"""Libro de la noche (Fable R4-1): el único registro de qué cargas hubo esta noche y cómo acabaron.

Hasta el 16/11 tres decisiones deducían «esta noche» de listas de ejecuciones de Actions, cada una a su manera:
el juez de los relojes (desde las 00:00 UTC, 50 ejecuciones), el reintento (desde medianoche de Madrid, 30) y la
cadena (solo la hora). Una ejecución entre las 23:00 y las 00:00 UTC contaba para una y no para la otra, y en
noches largas las listas se truncaban. Ahora todas leen `noche.json` de la rama `catalogo-estado`:

  {"dia": "2026-11-16",                      # día civil de Madrid
   "intentos": [{"run": 123, "intento": 1, "sha": "<commit del código>", "motivo": "cron|respaldo|cadena|...",
                 "inicio": "<UTC ISO>", "fin": "<UTC ISO>|null",
                 "resultado": "en_curso|publicado|degradado|fallido|cancelado|pendiente",
                 "clase": null, "firma": null}]}

Solo lo escribe el job `intake` (y la cadena/el reintento, que anotan un `pendiente` justo antes de despachar).
Como todos los jobs `intake` comparten grupo de concurrencia, «leer y anotar» al empezar es atómico entre cargas:
dos relojes que deciden a la vez cargar nunca cargan dos veces (el segundo vuelve a decidir y ve el primero).

  python scripts/noche.py juez           # reloj: imprime run=true|false
  python scripts/noche.py abrir --motivo cron|respaldo|manual   # intake: imprime cargar=true|false
  python scripts/noche.py cerrar --resultado success|failure|cancelled
  python scripts/noche.py cadena --aceptados N   # código 0 si toca encadenar (y anota el pendiente)
  python scripts/noche.py reintento               # código 0 si toca reintentar (y anota el pendiente)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

MADRID = ZoneInfo('Europe/Madrid')
FICHERO = 'noche.json'
HORA_FIN = 6                 # la noche de carga acaba a las 06:00 de Madrid (después Actions es del código)
MAX_FALLIDOS = 3             # cargas fallidas por noche: con 3, ni relojes ni reintentos vuelven a cargar
SIN_CIERRE = timedelta(minutes=250)  # el job tiene 240 min: un en_curso más viejo murió sin cerrar (corte)
PENDIENTE_CADUCA = timedelta(minutes=20)  # un despacho que no arrancó en 20 min se perdió
FORZADOS = ('manual', 'cadena', 'reintento')  # cargan siempre; cron y respaldo deciden con el libro


def dia(now: datetime) -> str:
    return now.astimezone(MADRID).date().isoformat()


def iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _cuando(texto: str) -> datetime:
    return datetime.strptime(texto, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def de_hoy(libro: dict | None, now: datetime) -> dict:
    """El libro de esta noche; el de otra noche no cuenta (se sustituye al primer apunte)."""
    if libro and libro.get('dia') == dia(now):
        return libro
    return {'dia': dia(now), 'intentos': []}


def efectivo(intento: dict, now: datetime) -> str | None:
    """Resultado contando el tiempo: un en_curso sin cerrar tras el tope del job fue un corte (fallido) y un
    pendiente que nunca arrancó caduca (no cuenta)."""
    resultado = intento.get('resultado')
    edad = now - _cuando(intento['inicio'])
    if resultado == 'en_curso' and edad > SIN_CIERRE:
        return 'fallido'
    if resultado == 'pendiente' and edad > PENDIENTE_CADUCA:
        return 'caducado'
    return resultado


def resumen(libro: dict | None, now: datetime) -> dict:
    noche = de_hoy(libro, now)
    estados = [(i, efectivo(i, now)) for i in noche['intentos']]
    cerrados = [(i, e) for i, e in estados if e in ('publicado', 'degradado', 'fallido', 'cancelado')]
    cerrados.sort(key=lambda par: (par[0].get('fin') or par[0]['inicio'], par[0].get('run') or 0))
    return {
        'activos': [i for i, e in estados if e in ('en_curso', 'pendiente')],
        'ultimo': cerrados[-1] if cerrados else None,
        'fallidos': sum(e == 'fallido' for _, e in estados),
    }


def decidir(libro: dict | None, now: datetime) -> tuple[bool, str]:
    """¿Carga un reloj (cron o respaldo)? La misma regla dentro del job intake, ya con el turno cogido."""
    r = resumen(libro, now)
    if r['activos']:
        a = r['activos'][0]
        return False, f"hay una carga {a['resultado']} esta noche (ejecución {a.get('run') or 'por arrancar'})"
    if r['fallidos'] >= MAX_FALLIDOS:
        return False, f"{r['fallidos']} cargas fallidas esta noche: no se insiste hasta mañana"
    if r['ultimo'] and r['ultimo'][1] in ('publicado', 'degradado'):
        return False, f"la última carga de esta noche ({r['ultimo'][0].get('run')}) terminó {r['ultimo'][1]}"
    if r['ultimo']:
        return True, f"la última carga de esta noche ({r['ultimo'][0].get('run')}) terminó {r['ultimo'][1]}: se reintenta"
    return True, 'ninguna carga esta noche'


def toca_reintento(libro: dict | None, now: datetime, run: int | None = None, intento: int | None = None
                   ) -> tuple[bool, str]:
    """Tras una carga fallida (ya cerrada en el libro): un reintento si es de noche, no se llegó al tope, esta carga
    consta como fallida (no un paso posterior que falló tras publicar ni un cierre que no llegó a escribirse) y no
    hay otra en marcha."""
    if now.astimezone(MADRID).hour >= HORA_FIN:
        return False, 'ya no es de noche'
    r = resumen(libro, now)
    if run is not None:
        propio = next((i for i in de_hoy(libro, now)['intentos']
                       if i.get('run') == run and i.get('intento') == intento), None)
        if propio is None or efectivo(propio, now) != 'fallido':
            return False, f"esta carga no consta fallida en el libro ({(propio or {}).get('resultado', 'sin apunte')})"
    if [i for i in r['activos'] if i.get('run') != run]:
        return False, 'ya hay otra carga en marcha o despachada'
    fallidos = r['fallidos']
    if fallidos >= MAX_FALLIDOS:
        return False, f'{fallidos} cargas fallidas esta noche'
    return True, f'{fallidos} cargas fallidas esta noche: se reintenta'


def toca_cadena(libro: dict | None, now: datetime, aceptados: int) -> tuple[bool, str]:
    if now.astimezone(MADRID).hour >= HORA_FIN:
        return False, 'ya no es de noche'
    if aceptados <= 0:
        return False, 'el lote no trajo libros nuevos'
    activos = [i for i in resumen(libro, now)['activos'] if i.get('run') != int(os.environ.get('GITHUB_RUN_ID') or 0)]
    if activos:
        return False, 'ya hay otra carga en marcha o despachada'
    return True, f'{aceptados} altas: se encadena el siguiente lote'


def abrir(libro, now, run, intento, sha, motivo):
    """Coge el turno: decide (si es un reloj) y anota el intento en curso. Devuelve (cargar, motivo, libro)."""
    noche = de_hoy(libro, now)
    cargar, porque = (True, f'carga {motivo}') if motivo in FORZADOS else decidir(noche, now)
    # El despacho que esperaba a esta carga ya arrancó (o se perdió): fuera los pendientes.
    noche['intentos'] = [i for i in noche['intentos'] if i.get('resultado') != 'pendiente']
    if cargar:
        noche['intentos'].append({'run': run, 'intento': intento, 'sha': sha, 'motivo': motivo, 'inicio': iso(now),
                                  'fin': None, 'resultado': 'en_curso', 'clase': None, 'firma': None})
    return cargar, porque, noche


RESULTADOS = {'success': 'publicado', 'failure': 'fallido', 'cancelled': 'cancelado', 'skipped': None}


def cerrar(libro, now, run, intento, resultado, clase=None, firma=None):
    """Cierra el apunte de esta carga en el libro donde se abrió, aunque haya cruzado la medianoche de Madrid
    (abierta a las 23:50, cerrada a las 00:10): el resultado nunca se pierde. El libro de la noche siguiente
    empieza de cero al primer apunte, como siempre."""
    abierta = libro and any(i.get('run') == run and i.get('intento') == intento for i in libro.get('intentos', []))
    noche = libro if abierta else de_hoy(libro, now)
    final = RESULTADOS.get(resultado, resultado)
    for entrada in noche['intentos']:
        if entrada.get('run') == run and entrada.get('intento') == intento and entrada.get('resultado') == 'en_curso':
            if final is None:
                noche['intentos'].remove(entrada)
            else:
                entrada.update(fin=iso(now), resultado=final, clase=clase, firma=firma)
            break
    return noche


def pendiente(libro, now, motivo):
    noche = de_hoy(libro, now)
    noche['intentos'].append({'run': None, 'intento': None, 'sha': None, 'motivo': motivo, 'inicio': iso(now),
                              'fin': None, 'resultado': 'pendiente', 'clase': None, 'firma': None})
    return noche


# --- E/S: la rama catalogo-estado -------------------------------------------------------------------------------

def leer():
    import catalogo_estado
    data = catalogo_estado.leer(FICHERO)
    return json.loads(data) if data else None


def escribir(noche, mensaje):
    import contextlib
    import catalogo_estado
    # stdout es del protocolo (cargar=, run=, que van a $GITHUB_OUTPUT): los avisos de git van a stderr.
    with contextlib.redirect_stdout(sys.stderr):
        catalogo_estado.escribir(FICHERO, (json.dumps(noche, ensure_ascii=False, indent=1) + '\n').encode(), mensaje)


def _resumen_job(texto):
    print(texto, file=sys.stderr)
    destino = os.environ.get('GITHUB_STEP_SUMMARY')
    if destino:
        with open(destino, 'a', encoding='utf-8') as fh:
            fh.write(texto + '\n')


def _juez(now, _run, _intento, _args) -> int:
    try:
        cargar, porque = decidir(leer(), now)
    except Exception as exc:  # noqa: BLE001 - sin libro se carga: el job intake vuelve a decidir con el turno
        cargar, porque = True, f'libro de la noche ilegible ({type(exc).__name__}): decide el job intake'
    print(f"run={'true' if cargar else 'false'}")
    _resumen_job(f"Reloj: {'carga' if cargar else 'no carga'}, {porque}.")
    return 0


def _abrir(now, run, intento, args) -> int:
    # Como el juez: sin libro legible o escribible se carga. El turno del grupo de concurrencia ya garantiza
    # una sola carga a la vez; lo que se pierde es el apunte, no la noche.
    legible = True
    try:
        libro = leer()
    except Exception as exc:  # noqa: BLE001
        libro, legible = None, False
        _resumen_job(f'Libro de la noche ilegible ({type(exc).__name__}): se decide sin él y no se reescribe.')
    cargar, porque, noche = abrir(libro, now, run, intento, os.environ.get('GITHUB_SHA', ''), args.motivo)
    try:
        if legible:  # un libro vacío pisaría el historial remoto que no se pudo leer
            escribir(noche, f'Noche {noche["dia"]}: {"empieza" if cargar else "no carga"} {run}')
    except Exception as exc:  # noqa: BLE001
        _resumen_job(f'Libro de la noche sin guardar ({type(exc).__name__}): la carga sigue.')
    print(f"cargar={'true' if cargar else 'false'}")
    _resumen_job(f"Libro de la noche: {'carga' if cargar else 'no carga'}, {porque}.")
    return 0


def _cerrar(now, run, intento, args) -> int:
    noche = cerrar(leer(), now, run, intento, args.resultado)
    escribir(noche, f'Noche {noche["dia"]}: {run} {args.resultado}')
    return 0


def _despacho(now, run, intento, args) -> int:
    """cadena o reintento: 0 si toca despachar (y queda apuntado como pendiente), 1 si no."""
    libro = leer()
    if args.accion == 'cadena':
        toca, porque = toca_cadena(libro, now, args.aceptados)
    else:
        toca, porque = toca_reintento(libro, now, run, intento)
    _resumen_job(f'{args.accion.capitalize()}: {porque}.')
    if toca:
        noche = pendiente(libro, now, args.accion)
        escribir(noche, f'Noche {noche["dia"]}: {args.accion} despachado tras {run}')
    return 0 if toca else 1


ACCIONES = {'juez': _juez, 'abrir': _abrir, 'cerrar': _cerrar, 'cadena': _despacho, 'reintento': _despacho}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('accion', choices=list(ACCIONES))
    p.add_argument('--motivo', default='manual')
    p.add_argument('--resultado', default='failure')
    p.add_argument('--aceptados', type=int, default=0)
    args = p.parse_args(argv)
    run = int(os.environ.get('GITHUB_RUN_ID') or 0)
    intento = int(os.environ.get('GITHUB_RUN_ATTEMPT') or 1)
    return ACCIONES[args.accion](datetime.now(timezone.utc), run, intento, args)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    raise SystemExit(main())
