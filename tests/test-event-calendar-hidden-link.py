#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tests/test-event-calendars.py'
SPEC = importlib.util.spec_from_file_location('existing_event_calendar_tests', SOURCE)
assert SPEC and SPEC.loader
existing = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(existing)

event = existing.EventCalendarTests().timed_event()
html = existing.page_for(event)
assert html.count('data-calendar-download>') == 1

# La mutación conserva el href exacto, pero oculta su único enlace.
html = html.replace(
    'data-calendar-download>',
    'hidden data-calendar-download>',
    1,
)

expected, errors = existing.cal.expected_calendars(
    html,
    as_of=date(2026, 9, 1),
)

assert 'presentacion-manecillas.ics' in expected, (
    'El evento confirmado y futuro debe seguir generando su calendario'
)
assert any('no tiene enlace visible' in error for error in errors), (
    'Un enlace con hidden no satisface el contrato de descarga visible. '
    f'Errores obtenidos: {errors!r}'
)

print('test-event-calendar-hidden-link: OK')
