from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'convocatorias-escritores/deadlines.ics'
raw = path.read_bytes()
assert raw, 'ICS vacío'
assert b'\r\n' in raw, 'ICS sin finales CRLF'
assert raw.replace(b'\r\n', b'').find(b'\n') == -1, 'Saltos LF aislados'
assert raw.endswith(b'\r\n'), 'Falta CRLF final'

for number, line in enumerate(raw.split(b'\r\n'), 1):
    assert len(line) <= 75, f'Línea {number}: {len(line)} octetos; máximo 75'
    if line.startswith((b' ', b'\t')):
        assert number > 1, 'Continuación sin línea anterior'
    if line:
        line.decode('utf-8')
print('ICS UTF-8 line folding: OK')