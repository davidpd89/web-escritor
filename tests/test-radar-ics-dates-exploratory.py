from __future__ import annotations
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'convocatorias-escritores/deadlines.ics').read_text(encoding='utf-8-sig')
lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
blocks = []
current = None
for line in lines:
    if line == 'BEGIN:VEVENT':
        current = []
    elif line == 'END:VEVENT':
        assert current is not None
        blocks.append(current)
        current = None
    elif current is not None:
        current.append(line)

def parse_date(value):
    for fmt in ('%Y%m%d', '%Y%m%dT%H%M%S', '%Y%m%dT%H%M%SZ'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise AssertionError(f'Fecha ICS inválida: {value}')

for block in blocks:
    starts = [line.split(':', 1)[1] for line in block if line.split(':', 1)[0].split(';')[0] == 'DTSTART']
    ends = [line.split(':', 1)[1] for line in block if line.split(':', 1)[0].split(';')[0] == 'DTEND']
    assert len(starts) == 1, f'DTSTART ausente o duplicado: {block}'
    assert len(ends) <= 1, f'DTEND duplicado: {block}'
    start = parse_date(starts[0])
    if ends:
        assert parse_date(ends[0]) >= start, f'Intervalo temporal invertido: {block}'
print(f'radar ICS dates: OK ({len(blocks)} eventos)')
