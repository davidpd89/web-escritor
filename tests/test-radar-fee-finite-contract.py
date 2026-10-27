import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('radar_fee', ROOT / 'scripts/build-radar-opportunities.py')
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)

base = {
    'id': 'fee-fixture', 'title': 'Premio de prueba',
    'type': 'premio', 'organizer': 'Organizador',
    'deadline': '2027-12-31', 'genres': ['novela'],
    'source_url': 'https://example.org/bases',
    'verified_at': '2026-10-23', 'published': True,
    'fee_eur': None
}

for value in (None, 0, 0.01, 100, 2500.5):
    row = copy.deepcopy(base)
    row['fee_eur'] = value
    radar.validate(row)

for value in (-1, -0.01, True, False, float('nan'), float('inf'), -float('inf'), '0', [], {}):
    row = copy.deepcopy(base)
    row['fee_eur'] = value
    try:
        radar.validate(row)
    except (ValueError, TypeError):
        continue
    raise AssertionError(f'fee_eur invalido aceptado: {value!r}')

print('PASS radar fee finite contract')
