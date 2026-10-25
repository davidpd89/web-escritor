from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'convocatorias-escritores/deadlines.ics'
raw = path.read_bytes()
assert raw, 'Calendario vacío'
text = raw.decode('utf-8-sig')
lines = text.replace('\r\n', '\n').splitlines()
assert lines[0] == 'BEGIN:VCALENDAR'
assert lines[-1] == 'END:VCALENDAR'
assert any(line.startswith('VERSION:2.0') for line in lines)
assert lines.count('BEGIN:VEVENT') == lines.count('END:VEVENT')

inside = False
records = []
current = []
for line in lines:
    if line == 'BEGIN:VEVENT':
        assert not inside, 'VEVENT anidado'
        inside = True
        current = []
    elif line == 'END:VEVENT':
        assert inside, 'END:VEVENT sin apertura'
        records.append(current)
        inside = False
    elif inside:
        current.append(line)
assert not inside, 'VEVENT sin cierre'
assert records, 'No hay eventos ICS'

uids = []
for event in records:
    for field in ('UID:', 'DTSTAMP:', 'SUMMARY:', 'DTSTART'):
        assert any(line.startswith(field) and line.split(':', 1)[-1].strip() for line in event), f'Campo obligatorio ausente: {field}'
    uid = next(line[4:] for line in event if line.startswith('UID:'))
    uids.append(uid)
assert len(uids) == len(set(uids)), 'UID duplicados'
print('ICS structural integrity: OK')