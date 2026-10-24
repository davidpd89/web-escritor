from __future__ import annotations
import copy
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('publisher_authority_qa', ROOT / 'scripts/build-editoriales.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
record = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers'][0]
today = date(2099, 1, 1)

bad_urls = [
    'https://editorial.example@attacker.invalid/recibir',
    'https://user:pass@editorial.example/recibir',
    'https://editorial.example:8080/recibir',
    'https://editorial.example/recibir\nX-Injection: yes',
    'https://editorial.example\\@attacker.invalid/recibir',
    'https://editorial.example:99999/recibir'
]

for field in ('submission_url', 'website_url'):
    for url in bad_urls:
        item = copy.deepcopy(record)
        item[field] = url
        try:
            mod.validate_record(item, set(), today)
        except (mod.ValidationError, ValueError):
            continue
        raise AssertionError(f'{field}: autoridad insegura aceptada: {url!r}')

print('OK: autoridades y credenciales rechazadas')
