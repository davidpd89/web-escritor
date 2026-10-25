import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_event_links', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

event = {'@type': 'Event', '@id': 'https://davidportodiaz.com/eventos.html#lectura-confirmada',
         'name': 'Lectura verificada', 'startDate': '2027-05-05', 'endDate': '2027-05-05',
         'eventStatus': mod.EVENT_SCHEDULED}
block = json.dumps({'@graph': [event]})
html = ('<script type="application/ld+json">' + block + '</script>'
        '<a data-calendar-download href="/assets/events/calendar/lectura-confirmada.ics">Guardar</a>'
        '<a data-calendar-download href="/assets/events/calendar/otro-evento.ics">Guardar otro</a>')
expected, errors = mod.expected_calendars(html, as_of=date(2027, 5, 1))
assert 'lectura-confirmada.ics' in expected
assert errors, 'Se aceptó un CTA para un ICS que no existe en el JSON-LD'
print('event orphan CTAs: OK')
