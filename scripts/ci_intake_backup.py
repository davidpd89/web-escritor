#!/usr/bin/env python3
"""¿Carga hoy este cron de respaldo de la ingesta nocturna?

La carga tiene un cron principal (00:17 UTC) y dos de respaldo (01:47 y 03:17 UTC). GitHub descarta crons
cuando hay carga: el 07/11 el de las 00:17 no saltó y esa noche no entró ningún libro. Un respaldo carga
solo si desde las 00:00 UTC de hoy ninguna otra ejecución del workflow está en curso o en cola, ni ha
terminado con el job `intake` en verde. Si las cargas de esta noche fallaron, el respaldo reintenta.

Cuenta el job `intake` y no la ejecución entera: una ejecución en la que el reloj decidió no cargar
termina en verde sin haber cargado nada.

Si la API falla, carga: un intento de más (serializado por la concurrencia del job) es mejor que una noche
sin libros.

Escribe `run=true|false` en stdout (para $GITHUB_OUTPUT) y el motivo en stderr y en el resumen del job.
Entorno: GITHUB_REPOSITORY, GITHUB_TOKEN, RUN_ID; opcional GITHUB_STEP_SUMMARY.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request

WORKFLOW = 'reading-catalogue-sync.yml'
INTAKE_JOB = 'intake'


def decide(runs: list[dict]) -> tuple[bool, str]:
    """runs: ejecuciones de hoy sin contar esta, con `id`, `status` y, si terminaron, `intake` (conclusión del
    job intake o None si no llegó a correr)."""
    for run in runs:
        if run.get('status') != 'completed':
            return False, f"la ejecución {run['id']} sigue en curso ({run.get('status')})"
        if run.get('intake') == 'success':
            return False, f"la ejecución {run['id']} ya cargó esta noche"
    return True, f'ninguna carga en verde ni en curso esta noche ({len(runs)} ejecuciones previas)'


def api(path: str, token: str) -> dict:
    req = urllib.request.Request(f'https://api.github.com{path}', headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def tonight(repo: str, token: str, run_id: str, now: dt.datetime) -> list[dict]:
    since = now.strftime('%Y-%m-%dT00:00:00Z')
    found = api(f'/repos/{repo}/actions/workflows/{WORKFLOW}/runs?created=%3E%3D{since}&per_page=50', token)['workflow_runs']
    runs = []
    for run in found:
        if str(run['id']) == run_id:
            continue
        entry = {'id': run['id'], 'status': run.get('status')}
        if run.get('status') == 'completed':
            jobs = api(f"/repos/{repo}/actions/runs/{run['id']}/jobs?per_page=20", token)['jobs']
            entry['intake'] = next((job.get('conclusion') for job in jobs if job.get('name') == INTAKE_JOB), None)
        runs.append(entry)
    return runs


def main() -> int:
    try:
        runs = tonight(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'], os.environ.get('RUN_ID', ''),
                       dt.datetime.now(dt.timezone.utc))
        run, reason = decide(runs)
    except Exception as exc:  # noqa: BLE001 - sin API se carga: mejor un intento de más que una noche perdida
        run, reason = True, f'API no disponible ({type(exc).__name__}): se carga'
    print(f"run={'true' if run else 'false'}")
    message = f"Cron de respaldo: {'carga' if run else 'no carga'}, {reason}."
    print(message, file=sys.stderr)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as fh:
            fh.write(message + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
