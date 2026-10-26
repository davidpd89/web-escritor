from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'accesibilidad/index.html'
REQUIRED = {'default-src', 'script-src', 'connect-src', 'object-src', 'base-uri', 'form-action'}

class CSPParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        values = dict(attrs)
        if (values.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(values.get('content') or '')

parser = CSPParser()
parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
assert len(parser.policies) == 1, f'{PAGE}: se esperaba una CSP meta; encontradas {len(parser.policies)}'
policy = {}
for part in parser.policies[0].split(';'):
    tokens = part.strip().split()
    if not tokens:
        continue
    name, *sources = tokens
    assert name not in policy, f'{PAGE}: directiva CSP duplicada {name}'
    policy[name] = sources
missing = REQUIRED - policy.keys()
assert not missing, f'{PAGE}: faltan directivas CSP {sorted(missing)}'
assert policy['object-src'] == ["'none'"], f'{PAGE}: object-src permite plugins: {policy["object-src"]}'
assert policy['base-uri'] == ["'self'"], f'{PAGE}: base-uri no restringe al origen propio'
assert "'self'" in policy['form-action'], f'{PAGE}: form-action no permite el origen propio'
for directive in ('default-src', 'script-src', 'connect-src', 'form-action'):
    sources = policy[directive]
    assert '*' not in sources, f'{PAGE}: comodin global en {directive}'
    assert "'unsafe-eval'" not in sources, f'{PAGE}: unsafe-eval en {directive}'
    assert 'http:' not in sources, f'{PAGE}: esquema HTTP abierto en {directive}'
assert "'unsafe-inline'" not in policy['script-src'], f'{PAGE}: scripts inline sin hashes o nonces'
print(f'PASS: {PAGE}, restricciones CSP activas verificadas')