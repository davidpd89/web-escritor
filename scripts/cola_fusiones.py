"""Cola de fusiones en serie (sustituye a los `.ci/cola.sh` + `.ci/cola_estado.py` locales, que no estaban versionados).

Lee la primera PR de `.ci/cola.txt`, la pone al día con main (una PR cada vez: update-branch en serie), espera a que
los checks requeridos del ruleset estén presentes y terminados, espera a que main pueda moverse, fusiona y la quita
de la lista. Si una PR no sale en verde o no se puede fusionar, pasa a `.ci/cola-rojas.txt` y sigue. Log en
`.ci/cola.log`.

  python scripts/cola_fusiones.py            # procesa la cola hasta vaciarla
  python scripts/cola_fusiones.py --estado N # imprime pendiente / verde / roja <detalle> para la PR N
  echo N >> .ci/cola.txt                     # añadir una PR

Regla de main quieto (18/11): la carga nocturna de libros publica con una PR que repite su CI (~75 min) si main
avanza; y cada puesta al día lanza ~50 jobs que dejan la carga sin runner. La cola antigua esperaba con tope (200 min)
y al agotarlo FUSIONABA: #1433 entró en main a las 04:05Z con el lote 2 en curso y costó una hora más; de madrugada
dejó el `intake` 15 min en cola. Aquí `main_puede_moverse` decide las dos cosas (poner al día y fusionar), sin tope:
nunca en la ventana de carga ni con una carga en curso o en cola. Contrato: tests/test_cola_fusiones.py.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'davidpd89/web-escritor'
CARGA = 'reading-catalogue-sync.yml'
# Cron de la carga 00:17 UTC con respaldos 01:47 y 03:17; encadena lotes hasta ~05:30.
VENTANA_CARGA = (dt.time(0, 0), dt.time(5, 30))
LISTA, ROJAS, LOG = ROOT / '.ci/cola.txt', ROOT / '.ci/cola-rojas.txt', ROOT / '.ci/cola.log'
VALIDOS = ('SUCCESS', 'SKIPPED', 'NEUTRAL')


def main_puede_moverse(ahora_utc, cargas_vivas):
    """True si se puede poner al día o fusionar una PR: fuera de la ventana de carga y sin carga en curso/cola.

    `cargas_vivas` es None si no se pudo consultar (gh caído): entonces no se mueve nada.
    """
    inicio, fin = VENTANA_CARGA
    if inicio <= ahora_utc.time() < fin:
        return False
    return cargas_vivas == 0


def estado_checks(rollup, requeridos):
    """`pendiente <faltan>`, `verde` o `roja <malos>`. Un requerido ausente cuenta como pendiente (16/11: pa11y y
    reflow corren por shards y publican el agregado al final; `gh pr checks --required` no los lista hasta entonces)."""
    estado = {}
    # Un check relanzado aparece varias veces: manda el último que empezó.
    for c in sorted(rollup, key=lambda c: c.get('startedAt') or c.get('createdAt') or ''):
        nombre = c.get('name') or c.get('context')
        valor = (c.get('conclusion') or c.get('state') or '').upper()
        if c.get('status') and c['status'].upper() != 'COMPLETED':
            valor = 'PENDING'
        estado[nombre] = valor
    faltan = sorted(n for n in requeridos if estado.get(n, 'PENDING') in ('PENDING', 'EXPECTED', ''))
    if faltan:
        return 'pendiente ' + ','.join(faltan)
    malos = [f'{n}={estado[n]}' for n in sorted(requeridos) if estado[n] not in VALIDOS]
    return 'roja ' + ','.join(malos) if malos else 'verde'


def gh(*args, check=True):
    r = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8', cwd=ROOT)
    if check and r.returncode:
        raise RuntimeError(f'gh {" ".join(args)}: {r.stderr.strip()}')
    return r


def requeridos():
    nombres = set()
    for rs in json.loads(gh('api', f'repos/{REPO}/rulesets').stdout):
        for regla in json.loads(gh('api', f'repos/{REPO}/rulesets/{rs["id"]}').stdout).get('rules', []):
            if regla['type'] == 'required_status_checks':
                nombres |= {c['context'] for c in regla['parameters']['required_status_checks']}
    return nombres


def estado_pr(numero):
    rollup = json.loads(gh('pr', 'view', str(numero), '--json', 'statusCheckRollup').stdout)['statusCheckRollup']
    return estado_checks(rollup, requeridos())


def cargas_vivas():
    try:
        return sum(len(json.loads(gh('run', 'list', '--workflow', CARGA, '--status', s, '--json', 'databaseId').stdout))
                   for s in ('in_progress', 'queued'))
    except (RuntimeError, ValueError):
        return None


def say(msg):
    with LOG.open('a', encoding='utf-8') as f:
        f.write(f'{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} {msg}\n')


def esperar_main_libre(que):
    while not main_puede_moverse(dt.datetime.now(dt.timezone.utc), cargas_vivas()):
        say(f'ventana/carga activa: no {que}')
        time.sleep(300)


def quitar(numero):
    lineas = LISTA.read_text(encoding='utf-8').splitlines()
    if str(numero) in lineas:
        lineas.remove(str(numero))
    LISTA.write_text(''.join(f'{l}\n' for l in lineas), encoding='utf-8')


def apartar(numero, motivo):
    say(f'#{numero} {motivo}: apartada')
    with ROJAS.open('a', encoding='utf-8') as f:
        f.write(f'{numero}\n')


def procesar(numero):
    esperar_main_libre(f'pongo al día #{numero}')
    if gh('pr', 'update-branch', str(numero), check=False).returncode == 0:
        say(f'#{numero}: puesta al día con main')
    say(f'#{numero}: espero checks')
    time.sleep(90)
    e = 'pendiente'
    for _ in range(120):
        try:
            e = estado_pr(numero)
        except RuntimeError as err:
            e = f'pendiente ({err})'
        if not e.startswith('pendiente'):
            break
        time.sleep(120)
    if e != 'verde':
        return apartar(numero, f'no está en verde ({e})')
    esperar_main_libre(f'fusiono #{numero}')
    s = ''
    for _ in range(10):
        s = gh('pr', 'view', str(numero), '--json', 'mergeStateStatus', '-q', '.mergeStateStatus', check=False).stdout.strip()
        if s not in ('BLOCKED', 'UNKNOWN'):
            break
        time.sleep(60)
    if gh('pr', 'merge', str(numero), '--squash', check=False).returncode == 0:
        say(f'#{numero} fusionada')
    else:
        apartar(numero, f'no se pudo fusionar ({s})')


def bucle():
    while True:
        pendientes = [l for l in LISTA.read_text(encoding='utf-8').split() if l.isdigit()] if LISTA.exists() else []
        if not pendientes:
            say('cola vacía')
            return
        procesar(int(pendientes[0]))
        quitar(int(pendientes[0]))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--estado', type=int, metavar='N')
    a = p.parse_args()
    if a.estado:
        print(estado_pr(a.estado))
    else:
        bucle()
    sys.exit(0)
