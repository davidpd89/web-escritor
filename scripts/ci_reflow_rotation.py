#!/usr/bin/env python3
"""Franja de fichas que audita este run del reflow completo (ver qa/reflow-detail-rotation.mjs).

La rotación reparte las fichas en K franjas y cada run recorre una. Tomar la franja de `run_number % K` no
garantiza la cobertura: el número avanza también con cada PR, y los últimos 7 runs de main del 07/11 cayeron
en 5 franjas, con 2 sin auditar. Aquí cada run de main elige la franja que lleva más tiempo sin auditarse,
según los artefactos `reflow-rotation-slot-<n>` de los runs anteriores de main (los que terminaron en verde
cuentan como cubiertos; los que siguen en curso, como reservados). El resumen deja la cobertura de los últimos
K runs completados.

Un PR usa `run_number % K` (su cobertura no cuenta para main). Si la API falla, el mismo cálculo: este paso
nunca bloquea el reflow.

Entorno: GITHUB_REPOSITORY, GITHUB_TOKEN, EVENT_NAME, RUN_NUMBER, RUN_ID, REFLOW_DETAIL_ROTATION (K).
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request

ARTIFACT = re.compile(r'^reflow-rotation-slot-(\d+)$')
WORKFLOW = 'sitewide-reflow-qa.yml'
MAIN_EVENTS = {'push', 'schedule', 'workflow_dispatch'}
LOOKBACK = 30


def pick_slot(history: list[dict], k: int) -> int:
    """history: runs de main, del más reciente al más antiguo, con `slot` (o None) y `state` ('done' o 'running').
    Primero una franja que nadie ha cubierto ni reservado; si no hay, la que lleva más tiempo sin cubrirse."""
    last_seen: dict[int, int] = {}
    for age, run in enumerate(history):
        slot = run.get('slot')
        if slot is not None and 0 <= slot < k:
            last_seen.setdefault(slot, age)
    unseen = [slot for slot in range(k) if slot not in last_seen]
    if unseen:
        return unseen[0]
    return max(range(k), key=lambda slot: (last_seen[slot], -slot))


def coverage(history: list[dict], k: int, slot: int) -> dict:
    """Franjas cubiertas por los últimos K runs completados en verde, sin contar este."""
    done = [run for run in history if run.get('state') == 'done'][:k]
    covered = sorted({run['slot'] for run in done if run.get('slot') is not None})
    return {'k': k, 'franja': slot, 'runs': [{'run': run['number'], 'franja': run.get('slot')} for run in done],
            'cubiertas': covered, 'faltan': [s for s in range(k) if s not in covered]}


def api(path: str, token: str) -> dict:
    req = urllib.request.Request(f'https://api.github.com{path}', headers={
        'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def main_history(repo: str, token: str, run_id: str) -> list[dict]:
    runs = api(f'/repos/{repo}/actions/workflows/{WORKFLOW}/runs?branch=main&per_page={LOOKBACK}', token)['workflow_runs']
    history = []
    for run in runs:
        if str(run['id']) == run_id or run.get('event') not in MAIN_EVENTS or run.get('head_branch') != 'main':
            continue
        if run.get('status') == 'completed':
            if run.get('conclusion') != 'success':
                continue
            state = 'done'
        else:
            state = 'running'
        names = [a['name'] for a in api(f"/repos/{repo}/actions/runs/{run['id']}/artifacts?per_page=100", token)['artifacts']]
        slots = [int(m.group(1)) for m in map(ARTIFACT.match, names) if m]
        history.append({'number': run['run_number'], 'state': state, 'slot': slots[0] if slots else None})
    return history


def main() -> int:
    k = int(os.environ.get('REFLOW_DETAIL_ROTATION') or 7)
    number = int(os.environ.get('RUN_NUMBER') or 0)
    slot, report, reason = number % k, None, 'pull_request: run_number % K (no cuenta para main)'
    if os.environ.get('EVENT_NAME') in MAIN_EVENTS:
        try:
            history = main_history(os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_TOKEN'], os.environ.get('RUN_ID', ''))
            slot = pick_slot(history, k)
            report = coverage(history, k, slot)
            reason = 'la franja que lleva más tiempo sin auditarse en main'
        except Exception as exc:  # noqa: BLE001 - la rotación nunca bloquea el reflow
            reason = f'API no disponible ({type(exc).__name__}): run_number % K'
    print(f'slot={slot} | {reason}')
    if report:
        print(json.dumps(report, ensure_ascii=False))
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
            fh.write(f'slot={slot}\n')
    with open('reflow-rotation.json', 'w', encoding='utf-8') as fh:
        json.dump(report or {'k': k, 'franja': slot, 'motivo': reason}, fh, ensure_ascii=False, indent=1)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as fh:
            fh.write(f'### Rotación de fichas: franja {slot} de {k}\n{reason}\n')
            if report:
                runs = ', '.join(f"#{r['run']}→{'?' if r['franja'] is None else r['franja']}" for r in report['runs'])
                fh.write(f"\nÚltimos {len(report['runs'])} runs completados de main: {runs or 'ninguno'}\n"
                         f"Cubiertas {len(report['cubiertas'])}/{k}; faltan {report['faltan'] or 'ninguna'}\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
