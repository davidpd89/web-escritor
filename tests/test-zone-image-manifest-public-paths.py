from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ASSETS = (ROOT / 'assets').resolve()
manifest = json.loads((ROOT / 'data/image-format-ladder.json').read_text(encoding='utf-8'))
failures = []
checked = 0
for index, entry in enumerate(manifest['eligible_sources']):
    for field in ('source', 'derivative'):
        value = entry[field]
        target = (ROOT / value).resolve()
        if not target.is_relative_to(ASSETS):
            failures.append(f'eligible_sources[{index}].{field}: {value} queda fuera de assets')
        elif not target.is_file():
            failures.append(f'eligible_sources[{index}].{field}: {value} no existe como archivo')
        else:
            checked += 1
assert checked > 0, 'data/image-format-ladder.json: no se verificaron archivos'
assert not failures, '\n'.join(failures)
print(f'PASS image manifest public paths: {checked} archivos')