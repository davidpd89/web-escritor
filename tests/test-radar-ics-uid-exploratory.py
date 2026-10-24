from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'convocatorias-escritores/deadlines.ics').read_text(encoding='utf-8-sig')
lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
assert lines.count('BEGIN:VCALENDAR') == 1
assert lines.count('END:VCALENDAR') == 1
assert lines.count('BEGIN:VEVENT') == lines.count('END:VEVENT')
uids = []
inside = False
current = []
for line in lines:
    if line == 'BEGIN:VEVENT':
        assert not inside
        inside = True
        current = []
    elif line == 'END:VEVENT':
        assert inside
        ids = [entry[4:] for entry in current if entry.startswith('UID:')]
        assert len(ids) == 1 and ids[0], f'UID inválido: {current}'
        uids.extend(ids)
        inside = False
    elif inside:
        current.append(line)
assert not inside
assert len(uids) == len(set(uids)), 'UID duplicado en deadlines.ics'
print(f'radar ICS UID: OK ({len(uids)} eventos)')
