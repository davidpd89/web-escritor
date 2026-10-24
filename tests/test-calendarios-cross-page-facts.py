from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('calendar_builder', ROOT / 'scripts/build-event-calendars.py')
cal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cal)

FIELDS = ('startDate', 'endDate', 'eventStatus', 'eventAttendanceMode', 'isAccessibleForFree')

def events(page):
    source = (ROOT / page).read_text(encoding='utf-8')
    return {e['@id'].split('#')[-1]: e for e in cal.extract_events(source)}

agenda = events('eventos.html')
archive = events('ferias.html')
shared = set(agenda) & set(archive)
assert shared, 'No se encontraron eventos comunes para comparar'

for key in sorted(shared):
    a, b = agenda[key], archive[key]
    for field in FIELDS:
        assert a.get(field) == b.get(field), f'{key}: diferencia en {field}: {a.get(field)!r} / {b.get(field)!r}'
    for field in ('addressLocality', 'addressRegion', 'addressCountry'):
        x = a['location']['address'].get(field)
        y = b['location']['address'].get(field)
        assert x == y, f'{key}: diferencia geográfica {field}: {x!r} / {y!r}'
    assert a['organizer']['name'] == b['organizer']['name'], f'{key}: organizadores diferentes'
    assert a['about']['isbn'] == b['about']['isbn'], f'{key}: ISBN diferente'
    assert a['about']['name'] == b['about']['name'], f'{key}: obra diferente'
    assert a['performer']['@id'] == b['performer']['@id'], f'{key}: autor diferente'
    assert a['offers']['price'] == b['offers']['price'], f'{key}: precio diferente'
    assert a['offers']['priceCurrency'] == b['offers']['priceCurrency'], f'{key}: moneda diferente'

print(f'OK: paridad factual de {len(shared)} eventos compartidos')