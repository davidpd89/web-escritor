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

Sin relojes por tiempo (R5-9): antes de coger el turno, el juez solo descarta lo evidente (la última publicó o quedó
degradada, o van 3 fallidas). Lo que depende de «hay otra activa» se decide con el turno cogido, donde el grupo no
deja dos a la vez: un `en_curso` ajeno murió sin cerrar (se cierra fallido, clase `corte`) y un `pendiente` es un
despacho que GitHub desalojó del grupo (quien tiene el turno carga por él y hereda su motivo). La cadena o el
reintento que llegan sin su pendiente ya los cargó otro: no cargan.

  python scripts/noche.py juez           # reloj: imprime run=true|false
  python scripts/noche.py abrir --motivo cron|respaldo|manual   # intake: imprime cargar=true|false
  python scripts/noche.py cerrar --resultado success|failure|cancelled
  python scripts/noche.py cadena --aceptados N [--guardadas M] [--consulta-pendiente 0|1]   # código 0 si toca encadenar (y anota el pendiente)
  python scripts/noche.py reintento               # código 0 si toca reintentar (y anota el pendiente)

Mismo código, mismo fallo (25/11): la puerta de la PR de datos cayó en un test concreto (`FALLA: tests/...`) y los dos
relojes siguientes relanzaron con el mismo commit: el mismo fallo, 75 min cada vez, y la noche murió con MAX_FALLIDOS.
Ahora el publicador deja la firma del fallo determinista en $RUNNER_TEMP/carga-fallo.json, `cerrar` la anota con la
huella del código (scripts, tests, qa, workflows, dependencias) y:
- el reintento no se despacha (daría lo mismo);
- un reloj, respaldo o despacho con la misma huella no carga y deja el job en rojo, para que la autorreparación lo vea
  y lo repare (una ejecución verde que «no carga» la callaba). Con un arreglo en main la huella cambia y se carga.
Una carga manual carga siempre.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

MADRID = ZoneInfo('Europe/Madrid')
FICHERO = 'noche.json'
HORA_FIN = 6                 # la noche de carga acaba a las 06:00 de Madrid (después Actions es del código)
MAX_FALLIDOS = 3             # cargas fallidas por noche: con 3, ni relojes ni reintentos vuelven a cargar
DESPACHADOS = ('cadena', 'reintento')  # cargan si su pendiente sigue en el libro; manual carga siempre
DETERMINISTA = 'determinista'  # clase de un fallo que se repite igual con el mismo código (un test concreto)
CODIGO = ('scripts', 'tests', 'qa', '.github', 'package.json', 'package-lock.json')  # lo que decide si falla
FALLO = 'carga-fallo.json'     # en $RUNNER_TEMP; lo escribe el publicador (publish-radar-refresh.anotar_fallo)


def dia(now: datetime) -> str:
    return now.astimezone(MADRID).date().isoformat()


def iso(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def de_hoy(libro: dict | None, now: datetime) -> dict:
    """El libro de esta noche; el de otra noche no cuenta (se sustituye al primer apunte)."""
    if libro and libro.get('dia') == dia(now):
        return libro
    return {'dia': dia(now), 'intentos': []}


def resumen(libro: dict | None, now: datetime) -> dict:
    noche = de_hoy(libro, now)
    estados = [(i, i.get('resultado')) for i in noche['intentos']]
    cerrados = [(i, e) for i, e in estados if e in ('publicado', 'degradado', 'fallido', 'cancelado')]
    cerrados.sort(key=lambda par: (par[0].get('fin') or par[0]['inicio'], par[0].get('run') or 0))
    return {
        'pendientes': [i for i, e in estados if e == 'pendiente'],
        'ultimo': cerrados[-1] if cerrados else None,
        'fallidos': sum(e == 'fallido' for _, e in estados),
    }


def repetiria(ultimo: tuple | None, codigo: str | None) -> str | None:
    """La firma del fallo si la última carga cerrada cayó en un fallo determinista con este mismo código: relanzarla
    daría el mismo fallo. None si no (otro fallo, otro código o sin huella con que comparar)."""
    if not ultimo or not codigo:
        return None
    entrada, estado = ultimo
    if estado == 'fallido' and entrada.get('clase') == DETERMINISTA and entrada.get('codigo') == codigo:
        return entrada.get('firma') or 'un test concreto'
    return None


def decidir(libro: dict | None, now: datetime, codigo: str | None = None) -> tuple[bool, str]:
    """¿Carga un reloj (cron o respaldo)? Solo lo evidente: una carga en curso o pendiente no cuenta aquí, la
    resuelve el job intake con el turno cogido (`abrir`). Con `codigo` (la huella del código que correría) tampoco
    carga si la última cayó en un fallo determinista con ese mismo código."""
    r = resumen(libro, now)
    if r['fallidos'] >= MAX_FALLIDOS:
        return False, f"{r['fallidos']} cargas fallidas esta noche: no se insiste hasta mañana"
    if r['pendientes']:
        # Un despacho (cadena o reintento) anotado cuyo `gh workflow run` falló o se perdió: nadie más lo cargaría.
        # El job intake lo hereda en `abrir` («despacho desalojado») o, si el despacho llegó, no carga dos veces.
        return True, f"despacho {r['pendientes'][0].get('motivo')} pendiente: lo resuelve el turno"
    if r['ultimo'] and r['ultimo'][1] in ('publicado', 'degradado'):
        return False, f"la última carga de esta noche ({r['ultimo'][0].get('run')}) terminó {r['ultimo'][1]}"
    firma = repetiria(r['ultimo'], codigo)
    if firma:
        return False, (f"la última carga ({r['ultimo'][0].get('run')}) cayó en {firma} con este mismo código: "
                       'repetirla daría el mismo fallo; se carga cuando entre un arreglo en main')
    if r['ultimo']:
        return True, f"la última carga de esta noche ({r['ultimo'][0].get('run')}) terminó {r['ultimo'][1]}: se reintenta"
    return True, 'ninguna carga esta noche'


def toca_reintento(libro: dict | None, now: datetime, run: int | None = None, intento: int | None = None
                   ) -> tuple[bool, str]:
    """Tras una carga fallida (ya cerrada en el libro): un reintento si es de noche, no se llegó al tope, esta carga
    consta como fallida (no un paso posterior que falló tras publicar ni un cierre que no llegó a escribirse) y no
    hay otro despacho pendiente. Corre con el turno: un en_curso ajeno está muerto y no cuenta."""
    if now.astimezone(MADRID).hour >= HORA_FIN:
        return False, 'ya no es de noche'
    r = resumen(libro, now)
    if run is not None:
        propio = next((i for i in de_hoy(libro, now)['intentos']
                       if i.get('run') == run and i.get('intento') == intento), None)
        if propio is None or propio.get('resultado') != 'fallido':
            return False, f"esta carga no consta fallida en el libro ({(propio or {}).get('resultado', 'sin apunte')})"
        if propio.get('clase') == DETERMINISTA:
            return False, (f"cayó en {propio.get('firma') or 'un test concreto'}: con el mismo código el reintento daría "
                           'el mismo fallo; lo repara la autorreparación y lo carga el siguiente reloj')
    if r['pendientes']:
        return False, 'ya hay otra carga despachada'
    fallidos = r['fallidos']
    if fallidos >= MAX_FALLIDOS:
        return False, f'{fallidos} cargas fallidas esta noche'
    return True, f'{fallidos} cargas fallidas esta noche: se reintenta'


def toca_cadena(libro: dict | None, now: datetime, aceptados: int, guardadas: int = 0,
                consulta_pendiente: bool = False) -> tuple[bool, str]:
    """Encadena si el lote trajo altas o si quedan ramas de datos guardadas (Fable R4-11, F8): una carga recuperada
    o reanudada sin altas propias también sigue, en vez de esperar una noche por cada punto de control.

    `consulta_pendiente`: el lote salió de datos guardados, no de las fuentes; la noche aún debe su consulta aunque
    no trajera altas (21/11: un punto de guardado ya publicado gastó el turno y entraron 0 libros)."""
    if now.astimezone(MADRID).hour >= HORA_FIN:
        return False, 'ya no es de noche'
    if aceptados <= 0 and guardadas <= 0 and not consulta_pendiente:
        return False, 'el lote no trajo libros nuevos ni quedan ramas guardadas'
    if resumen(libro, now)['pendientes']:
        return False, 'ya hay otra carga despachada'
    return True, f'{aceptados} altas y {guardadas} ramas guardadas: se encadena el siguiente lote'


def abrir(libro, now, run, intento, sha, motivo, codigo=None):
    """Ya con el turno del grupo: cierra los muertos, decide y anota el intento en curso.
    Devuelve (cargar, motivo, libro)."""
    noche = de_hoy(libro, now)
    for ajeno in noche['intentos']:  # el grupo no deja dos a la vez: este murió sin cerrar
        if ajeno.get('resultado') == 'en_curso' and (ajeno.get('run'), ajeno.get('intento')) != (run, intento):
            ajeno.update(fin=iso(now), resultado='fallido', clase='corte')
    pendientes = [i for i in noche['intentos'] if i.get('resultado') == 'pendiente']
    if motivo == 'manual':
        cargar, porque = True, 'carga manual'
    elif (firma := repetiria(resumen(noche, now)['ultimo'], codigo)):
        # Antes que la cadena o un despacho desalojado: con el mismo código, cualquiera de ellos repetiría el fallo.
        cargar, porque = False, (f'la última carga cayó en {firma} con este mismo código: repetirla daría el mismo '
                                 'fallo; se carga cuando entre un arreglo en main')
    elif motivo in DESPACHADOS:
        cargar, porque = (True, f'carga {motivo}') if pendientes else (
            False, f'{motivo} sin despacho pendiente: ya la cargó quien tuvo el turno antes')
    elif pendientes:
        motivo = pendientes[0].get('motivo') or motivo
        cargar, porque = True, f'despacho {motivo} desalojado del grupo: lo carga este turno'
    else:
        cargar, porque = decidir(noche, now)
    if cargar:  # solo quien carga consume los despachos que esperaban
        noche['intentos'] = [i for i in noche['intentos'] if i.get('resultado') != 'pendiente']
        noche['intentos'].append({'run': run, 'intento': intento, 'sha': sha, 'motivo': motivo, 'inicio': iso(now),
                                  'fin': None, 'resultado': 'en_curso', 'clase': None, 'firma': None,
                                  'codigo': codigo})
    return cargar, porque, noche


RESULTADOS = {'success': 'publicado', 'failure': 'fallido', 'cancelled': 'cancelado', 'skipped': None}


def cerrar(libro, now, run, intento, resultado, clase=None, firma=None, sha=None, codigo=None):
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
                if sha:  # el segundo intento hace reset --hard origin/main: el código que acabó la carga
                    entrada['sha'] = sha
                if codigo:
                    entrada['codigo'] = codigo
            break
    else:
        # la escritura de apertura falló: el resultado se anota igual, así cuenta para reintentos y MAX_FALLIDOS
        if final is not None and not any(i.get('run') == run and i.get('intento') == intento
                                         for i in noche['intentos']):
            noche['intentos'].append({'run': run, 'intento': intento, 'sha': sha, 'motivo': None, 'inicio': iso(now),
                                      'fin': iso(now), 'resultado': final, 'clase': clase, 'firma': firma,
                                      'codigo': codigo})
    return noche


def huerfana(libro, now, run, intento):
    """Una carga que murió sin cerrar su apunte (el runner perdió la comunicación, el job llegó al límite): sus pasos
    de cierre y de reintento nunca corrieron. Si su apunte sigue en curso lo cierra como fallido de clase `corte` y
    devuelve (libro, True); si ya estaba cerrado (fallo normal: el propio job decidió el reintento) devuelve (libro, False)."""
    if not libro:
        return libro, False
    for entrada in libro.get('intentos', []):
        if entrada.get('run') == run and entrada.get('intento') == intento and entrada.get('resultado') == 'en_curso':
            entrada.update(fin=iso(now), resultado='fallido', clase='corte')
            return libro, True
    return libro, False


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


def _bytes(noche):
    return (json.dumps(noche, ensure_ascii=False, indent=1) + '\n').encode()


def escribir(noche, mensaje, rehacer=None):
    """Guarda el libro. Con `rehacer` (libro remoto -> libro nuevo) el cambio se rehace sobre lo que haya en la rama
    en ese momento, no sobre la lectura de antes: dos escritores a la vez (el segador y el abrir de la siguiente
    carga) ya no se pisan."""
    import contextlib
    import catalogo_estado
    extra = {}
    if rehacer:
        extra['rehacer'] = lambda datos: _bytes(rehacer(json.loads(datos) if datos else None))
    # stdout es del protocolo (cargar=, run=, que van a $GITHUB_OUTPUT): los avisos de git van a stderr.
    with contextlib.redirect_stdout(sys.stderr):
        catalogo_estado.escribir(FICHERO, _bytes(noche), mensaje, **extra)


def _head():
    """El commit del código que corre (no GITHUB_SHA: la carga puede hacer reset --hard origin/main)."""
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True,
                              timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return os.environ.get('GITHUB_SHA', '')


def _codigo():
    """Huella del código que decide si la carga falla (no el commit: un commit de datos o de redes no cambia el
    resultado de un test). None si git no responde: sin huella no se bloquea nada."""
    try:
        arbol = subprocess.run(['git', 'ls-tree', 'HEAD', '--', *CODIGO], capture_output=True, text=True, check=True,
                               timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return hashlib.sha1(arbol.encode()).hexdigest() if arbol.strip() else None


def _fallo_anotado():
    """(clase, firma) que dejó el publicador en $RUNNER_TEMP/carga-fallo.json; (None, None) si no hay o no se lee."""
    try:
        with open(os.path.join(os.environ['RUNNER_TEMP'], FALLO), encoding='utf-8') as fh:
            datos = json.load(fh)
        return datos.get('clase') or None, datos.get('firma') or None
    except (KeyError, OSError, ValueError, AttributeError):
        return None, None


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
    codigo, head = _codigo(), _head()
    decision = {}

    def decide(lib):  # se rehace sobre el libro remoto si otro escribió entretanto: vale la decisión guardada
        decision['r'] = abrir(lib, now, run, intento, head, args.motivo, codigo)
        return decision['r'][2]

    decide(libro)
    cargar, porque, noche = decision['r']
    try:
        if legible:  # un libro vacío pisaría el historial remoto que no se pudo leer
            escribir(noche, f'Noche {noche["dia"]}: {"empieza" if cargar else "no carga"} {run}', decide)
            cargar, porque, noche = decision['r']
    except Exception as exc:  # noqa: BLE001
        _resumen_job(f'Libro de la noche sin guardar ({type(exc).__name__}): la carga sigue.')
    repite = not cargar and repetiria(resumen(noche, now)['ultimo'], codigo) is not None
    if not legible and not cargar:  # sin libro no se sabe si otro ya la cargó: se carga
        cargar, porque, repite = True, 'libro ilegible: se carga', False
    print(f"cargar={'true' if cargar else 'false'}")
    _resumen_job(f"Libro de la noche: {'carga' if cargar else 'no carga'}, {porque}.")
    if repite:  # en rojo: la autorreparación vigila esta ejecución y repara el fallo antes del siguiente reloj
        print(f'::error::Carga bloqueada: {porque}.', file=sys.stderr)
        return 3
    return 0


def _cerrar(now, run, intento, args) -> int:
    # El cierre nunca cambia el resultado de la carga (ni la rama success()/failure() de la cadena): si no se
    # escribe, el intento queda en_curso y el siguiente turno lo cierra como corte.
    try:
        clase, firma = _fallo_anotado() if args.resultado == 'failure' else (None, None)
        sha, codigo = _head(), _codigo()

        def cierra(lib):
            return cerrar(lib, now, run, intento, args.resultado, clase=clase, firma=firma, sha=sha, codigo=codigo)
        noche = cierra(leer())
        escribir(noche, f'Noche {noche["dia"]}: {run} {args.resultado}', cierra)
    except Exception as exc:  # noqa: BLE001
        _resumen_job(f'Libro de la noche sin cerrar ({type(exc).__name__}): lo cerrará el siguiente turno.')
    return 0


def _despacho(now, run, intento, args) -> int:
    """cadena o reintento: 0 si toca despachar (y queda apuntado como pendiente), 1 si no. Sin libro legible o sin
    pendiente escrito no se despacha: un despacho sin apunte no lo podría heredar nadie."""
    decision = {}

    def decide(lib):  # el libro con el pendiente apuntado, o el mismo si no toca
        if args.accion == 'cadena':
            decision['r'] = toca_cadena(lib, now, args.aceptados, args.guardadas, args.consulta_pendiente)
        else:
            decision['r'] = toca_reintento(lib, now, run, intento)
        return pendiente(lib, now, args.accion) if decision['r'][0] else lib

    try:
        noche = decide(leer())
        toca, porque = decision['r']
        if toca:
            escribir(noche, f'Noche {noche["dia"]}: {args.accion} despachado tras {run}', decide)
            toca, porque = decision['r']  # si al rehacerlo otro ya había despachado, no se despacha dos veces
    except Exception as exc:  # noqa: BLE001
        toca, porque = False, f'libro de la noche no disponible ({type(exc).__name__}): no se despacha'
    _resumen_job(f'{args.accion.capitalize()}: {porque}.')
    return 0 if toca else 1


def _huerfana(now, _run, _intento, args) -> int:
    """Lo lanza el vigía de cargas muertas (reading-catalogue-reaper.yml) con la carga que terminó en rojo: 0 si toca
    despachar el reintento (ya apuntado como pendiente), 1 si no. Solo actúa sobre apuntes que quedaron en curso."""
    try:
        decision = {}

        def recoge(lib):
            lib, huerfano = huerfana(lib, now, args.run_muerto, args.intento_muerto)
            toca = toca_reintento(lib, now, args.run_muerto, args.intento_muerto) if huerfano else (False, '')
            decision['r'] = (huerfano, *toca)
            # El cierre como fallida se guarda siempre (cuenta para MAX_FALLIDOS y para los relojes), se despache o no.
            return pendiente(lib, now, 'reintento') if toca[0] else lib

        libro = recoge(leer())
        huerfano, toca, porque = decision['r']
        if not huerfano:
            _resumen_job(f'Carga {args.run_muerto}: su apunte ya estaba cerrado; no hay nada que recoger.')
            return 1
        escribir(libro, f'Noche {dia(now)}: {args.run_muerto} murió sin cerrar' + ('; reintento despachado' if toca else ''),
                 recoge)
        huerfano, toca, porque = decision['r']
        if not huerfano:  # al rehacerlo, el abrir de la siguiente carga ya lo había cerrado como corte
            _resumen_job(f'Carga {args.run_muerto}: la cerró otro mientras se guardaba; no hay nada que recoger.')
            return 1
    except Exception as exc:  # noqa: BLE001
        toca, porque = False, f'libro de la noche no disponible ({type(exc).__name__}): no se despacha'
    _resumen_job(f'Carga muerta {args.run_muerto}: {porque}.')
    return 0 if toca else 1


ACCIONES = {'juez': _juez, 'abrir': _abrir, 'cerrar': _cerrar, 'cadena': _despacho, 'reintento': _despacho, 'huerfana': _huerfana}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('accion', choices=list(ACCIONES))
    p.add_argument('--motivo', default='manual')
    p.add_argument('--resultado', default='failure')
    p.add_argument('--aceptados', type=int, default=0)
    p.add_argument('--guardadas', type=int, default=0)
    p.add_argument('--consulta-pendiente', type=int, default=0)
    p.add_argument('--run-muerto', type=int, default=0)
    p.add_argument('--intento-muerto', type=int, default=1)
    args = p.parse_args(argv)
    run = int(os.environ.get('GITHUB_RUN_ID') or 0)
    intento = int(os.environ.get('GITHUB_RUN_ATTEMPT') or 1)
    return ACCIONES[args.accion](datetime.now(timezone.utc), run, intento, args)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    raise SystemExit(main())
