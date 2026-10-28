from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'donde-empieza-la-jaula/index.html'

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

p = Metadata()
p.feed((ROOT / PAGE).read_text(encoding='utf-8'))
assert len(p.policies) == 1, f'{PAGE}: CSP encontradas={len(p.policies)}, esperado=1'
policy = {}
for item in p.policies[0].split(';'):
    tokens = item.strip().split()
    if tokens:
        assert tokens[0] not in policy, f'{PAGE}: directiva CSP duplicada {tokens[0]}'
        policy[tokens[0]] = tokens[1:]
for name in ('default-src', 'script-src', 'object-src', 'base-uri', 'form-action'):
    assert name in policy, f'{PAGE}: falta directiva CSP {name}'
assert policy['object-src'] == ["'none'"], f'{PAGE}: object-src insegura: {policy["object-src"]}'
for name in ('script-src', 'form-action', 'base-uri'):
    values = policy[name]
    assert '*' not in values, f'{PAGE}: comodín universal en {name}: {values}'
assert "'unsafe-eval'" not in policy['script-src'], f'{PAGE}: unsafe-eval autorizado'
assert "'unsafe-inline'" not in policy['script-src'], f'{PAGE}: scripts inline sin restricción'
assert policy['form-action'] == ["'self'"], f'{PAGE}: formulario autorizado fuera del origen: {policy["form-action"]}'
print('OK: CSP de Jaula restringe ejecución y destinos de formularios')