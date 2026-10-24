#!/usr/bin/env python3
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
payload = json.loads((ROOT / 'convocatorias-escritores/opportunities.json').read_text(encoding='utf-8'))
text = (ROOT / 'convocatorias-escritores/deadlines.ics').read_text(encoding='utf-8')
lines = []
for line in text.splitlines():
    if line.startswith((' ', '\t')) and lines:
        lines[-1] += line[1:]
    else:
        lines.append(line)
events = []
current = None
for line in lines:
    if line == 'BEGIN:VEVENT':
        assert current is None
        current = {}
    elif line == 'END:VEVENT':
        assert current is not None
        events.append(current)
        current = None
    elif current is not None and ':' in line:
        key, value = line.split(':', 1)
        assert key not in current, f'Campo ICS duplicado: {key}'
        current[key] = value
assert current is None, 'VEVENT incompleto'
by_uid = {e['UID']: e for e in events}
assert len(by_uid) == len(events), 'UID duplicados'
assert len(events) == len(payload['items']), 'Número de eventos distinto del número de convocatorias activas'
for item in payload['items']:
    uid = item['id'] + '@davidportodiaz.com'
    assert uid in by_uid, f'Evento ausente: {uid}'
    event = by_uid[uid]
    deadline = date.fromisoformat(item['deadline'])
    assert event['DTSTART;VALUE=DATE'] == deadline.strftime('%Y%m%d'), uid
    assert event['DTEND;VALUE=DATE'] == (deadline + timedelta(days=1)).strftime('%Y%m%d'), uid
    assert event['URL'] == item['source_url'], uid
    assert event['SUMMARY'].replace('\\,', ',').replace('\\;', ';').replace('\\n', '\n') == item['title'], uid
print(f'OK ICS: {len(events)} eventos contrastados')
