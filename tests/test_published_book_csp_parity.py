import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Policies(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'content-security-policy':
            self.values.append(attrs.get('content', ''))

def directives(policy):
    result = {}
    for item in policy.split(';'):
        parts = item.strip().split()
        if parts:
            result[parts[0].lower()] = set(parts[1:])
    return result

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
checked = 0
for book in catalogue['libros']:
    if book['estado'] != 'publicado':
        continue
    path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
    assert path.is_file(), f'{path}: ficha publicada ausente'
    parser = Policies()
    parser.feed(path.read_text(encoding='utf-8'))
    assert parser.values, f'{path}: no existe CSP declarada en el documento'
    policies = [directives(value) for value in parser.values]
    assert any(p.get('object-src') == {"'none'"} for p in policies), f'{path}: object-src no está bloqueado'
    assert any(p.get('base-uri') in ({"'self'"}, {"'none'"}) for p in policies), f'{path}: base-uri no está restringido'
    assert any('script-src' in p and "'unsafe-inline'" not in p['script-src'] and "'unsafe-eval'" not in p['script-src'] and '*' not in p['script-src'] for p in policies), f'{path}: script-src permite ejecución insegura o no está declarado'
    checked += 1
assert checked > 0, 'No se analizaron fichas publicadas'
print(f'PASS: CSP de {checked} fichas publicadas')
