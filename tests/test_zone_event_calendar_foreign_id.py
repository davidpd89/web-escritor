import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_event_origin', ROOT / 'scripts/build-event-calendars.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

event = {'@type': 'Event', '@id': 'https://tercero.example/eventos.html#acto-2027',
         'name': 'Acto ajeno', 'startDate': '2027-05-05', 'endDate': '2027-05-05',
         'eventStatus': mod.EVENT_SCHEDULED}
html = ('<script type="application/ld+json">' + json.dumps({'@graph': [event]}) + '</script>'
        '<a data-calendar-download href="/assets/events/calendar/acto-2027.ics">Guardar</a>')
outputs, errors = mod.expected_calendars(html, as_of=date(2027, 5, 1))
assert errors and not outputs, 'Se publicó un ICS cuyo evento declara un dominio externo'
print('event calendar origin: OK')
