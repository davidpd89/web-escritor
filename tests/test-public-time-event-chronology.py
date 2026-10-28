#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'eventos.html'
CHECKER = ROOT / 'scripts/check-public-time-semantics.py'

OLD = '"endDate": "2026-06-10T20:00:00+02:00"'
BROKEN = '"endDate": "2026-06-10T18:00:00+02:00"'

html = SOURCE.read_text(encoding='utf-8')
assert html.count(OLD) == 1, 'La fixture real de Madrid ha cambiado'
assert '"startDate": "2026-06-10T19:00:00+02:00"' in html

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'scripts').mkdir()
    (root / 'data').mkdir()

    # Se conserva el checker de producción y solo se fija el reloj.
    checker = CHECKER.read_text(encoding='utf-8')
    clock = 'TODAY = date.today()'
    assert checker.count(clock) == 1
    checker = checker.replace(clock, 'TODAY = date(2026, 10, 23)')
    target = root / 'scripts/check-public-time-semantics.py'
    target.write_text(checker, encoding='utf-8')

    (root / 'eventos.html').write_text(
        html.replace(OLD, BROKEN, 1), encoding='utf-8'
    )
    registry = {
        'defaults': {},
        'entries': [{'sourceFile': 'eventos.html', 'status': 'public'}],
    }
    (root / 'data/content-registry.json').write_text(
        json.dumps(registry), encoding='utf-8'
    )

    result = subprocess.run(
        [sys.executable, str(target)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, (
        'El checker aceptó endDate 18:00 anterior a startDate 19:00 '
        'en un Event real de eventos.html:\n' + output
    )
    assert 'endDate precedes startDate' in output, (
        'El rechazo debe deberse a la cronología inversa, '
        'no a un error incidental:\n' + output
    )

print('test-public-time-event-chronology: OK')
