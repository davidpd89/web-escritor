import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('cal',ROOT/'scripts/build-event-calendars.py')
cal=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(cal)

def event(start,end):
    return {'@type':'Event','@id':'https://davidportodiaz.com/eventos.html#qa-zero-duration','name':'Firma de prueba','startDate':start,'endDate':end,'dateModified':'2026-01-01'}

invalid=[
    ('2026-11-03T19:00:00+01:00','2026-11-03T19:00:00+01:00'),
    ('2026-06-03T19:00:00+02:00','2026-06-03T18:59:59+02:00'),
]
for start,end in invalid:
    try:cal.build_ics(event(start,end))
    except ValueError:pass
    else:raise AssertionError(f'ICS aceptó intervalo no positivo: {start} -> {end}')

valid=cal.build_ics(event('2026-11-03T19:00:00+01:00','2026-11-03T19:01:00+01:00'))
assert b'BEGIN:VEVENT' in valid
print('OK: límites temporales del generador ICS')