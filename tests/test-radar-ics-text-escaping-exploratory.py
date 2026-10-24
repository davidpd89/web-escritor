from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT / 'convocatorias-escritores/deadlines.ics').read_text(encoding='utf-8-sig')
lines = raw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
logical = []
for line in lines:
    if line.startswith((' ', '\t')) and logical:
        logical[-1] += line[1:]
    else:
        logical.append(line)
for line in logical:
    if line.startswith(('SUMMARY:', 'DESCRIPTION:')):
        value = line.split(':', 1)[1]
        assert value.strip(), f'Campo textual vacío: {line}'
        assert '\r' not in value and '\n' not in value
        for index, character in enumerate(value):
            if character in ',;':
                backslashes = 0
                cursor = index - 1
                while cursor >= 0 and value[cursor] == '\\':
                    backslashes += 1
                    cursor -= 1
                assert backslashes % 2 == 1, f'Separador ICS sin escapar: {line}'
print('radar ICS text escaping: OK')
