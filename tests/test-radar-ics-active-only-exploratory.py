from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
public = json.loads((ROOT / 'convocatorias-escritores/opportunities.json').read_text(encoding='utf-8'))
today = date.fromisoformat(public['generated_for'])
ics = (ROOT / 'convocatorias-escritores/deadlines.ics').read_text(encoding='utf-8-sig')
lines = ics.replace('\r\n', '\n').replace('\r', '\n').split('\n')
for line in lines:
    if line.startswith('DTSTART'):
        value = line.split(':', 1)[1]
        event_date = datetime.strptime(value[:8], '%Y%m%d').date()
        assert event_date >= today, f'Convocatoria vencida incluida en calendario: {event_date} < {today}'
print('radar ICS active-only: OK')
