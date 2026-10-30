import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
manifest = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))
indexed = set(manifest['pages'])
defaults = registry.get('defaults', {})
by_source = {}
# Las entradas de ancla (/pagina/#seccion) no son la página (#943): si la página
# tiene entrada propia, solo cuentan las entradas de página.
has_page_entry = {e['sourceFile'] for e in registry['entries'] if e.get('sourceFile') and '#' not in str(e.get('url') or '')}

for entry in registry['entries']:
    source = entry.get('sourceFile')
    if not source:
        continue
    if source in has_page_entry and '#' in str(entry.get('url') or ''):
        continue
    effective = {**defaults, **entry}
    previous = by_source.get(source)
    if previous:
        effective['status'] = 'private' if previous.get('status', 'public') != 'public' or effective.get('status', 'public') != 'public' else 'public'
        effective['searchIndex'] = previous.get('searchIndex', True) is not False and effective.get('searchIndex', True) is not False
    by_source[source] = effective

excluded = {source for source, entry in by_source.items() if entry.get('status', 'public') != 'public' or entry.get('searchIndex', True) is False}
assert excluded, 'Registro editorial: no se encontraron exclusiones que verificar'
leaked = sorted(excluded & indexed)
assert not leaked, f'Pagefind publica páginas excluidas por content-registry.json: {leaked}'
print(f'PASS: {len(excluded)} exclusiones editoriales respetadas por Pagefind')
