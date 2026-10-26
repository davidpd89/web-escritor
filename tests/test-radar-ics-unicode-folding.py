import importlib.util
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_ics_qa', ROOT / 'scripts/build-radar-opportunities.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
today = date(2026, 10, 23)
title = 'Premio Ñandú, imaginación; memoria\\archivo\nNueva línea ' + 'áéíóú😀' * 19
item = {'id': 'qa-ics-unicode', 'title': title, 'organizer': 'Editorial, autoría; España', 'deadline': '2026-11-15', 'verified_at': '2026-10-23', 'published': True, 'source_url': 'https://example.org/bases'}
ics = mod.build_ics([item], today)
assert '\r\n' in ics
physical = [line for line in ics.split('\r\n') if line]
assert all(len(line.encode('utf-8')) <= 75 for line in physical)
logical = []
for line in physical:
    if line.startswith((' ', '\t')):
        assert logical
        logical[-1] += line[1:]
    else:
        logical.append(line)
assert logical.count('BEGIN:VEVENT') == 1
assert logical.count('END:VEVENT') == 1
summary = next(line.split(':', 1)[1] for line in logical if line.startswith('SUMMARY:'))
def unescape(value):
    return re.sub(r'\\([nN,;\\])', lambda m: '\n' if m.group(1).lower() == 'n' else m.group(1), value)
assert unescape(summary) == title, (unescape(summary), title)
assert not any(line.startswith(('LOCATION:', 'ATTENDEE:', 'ORGANIZER:')) for line in logical)
assert 'DTSTART;VALUE=DATE:20261115' in logical
assert 'DTEND;VALUE=DATE:20261116' in logical
print('OK: folding Unicode y escapes ICS')
