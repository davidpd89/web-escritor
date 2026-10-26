from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
ROUTES = [
    'recursos/ficha-historia-objeto-heredado/index.html',
    'recursos/herramientas-para-escritores/index.html',
]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
        self.active = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))
        if tag in ('script', 'iframe', 'object', 'embed'):
            self.active.append((tag, a))

for route in ROUTES:
    parser = Parser()
    parser.feed((ROOT / route).read_text(encoding='utf-8'))
    assert len(parser.policies) == 1, f'{route}: CSP encontradas={len(parser.policies)}'
    directives = {}
    for part in parser.policies[0].split(';'):
        tokens = part.strip().split()
        if tokens:
            assert tokens[0] not in directives, f'{route}: directiva CSP duplicada {tokens[0]}'
            directives[tokens[0]] = tokens[1:]
    for name in ('connect-src', 'form-action', 'frame-src', 'object-src'):
        assert directives.get(name) == ["'none'"], f'{route}: {name}={directives.get(name)}'
    for name in ('default-src', 'script-src', 'style-src', 'img-src', 'font-src'):
        assert directives.get(name) == ["'self'"], f'{route}: {name}={directives.get(name)}'
    assert directives.get('base-uri') == ["'self'"], f'{route}: base-uri incorrecto'
    for tag, attrs in parser.active:
        assert tag == 'script', f'{route}: elemento activo inesperado {tag}'
        if attrs.get('type') == 'application/ld+json':
            assert 'src' not in attrs, f'{route}: JSON-LD con src'
        else:
            assert attrs.get('src', '').startswith('/assets/'), f'{route}: script externo o inline {attrs}'
print('OK: CSP y contenido activo de recursos')