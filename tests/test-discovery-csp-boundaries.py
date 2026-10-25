from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['recomendaciones', 'cuaderno', 'herramientas', 'editoriales', 'libros']

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

for name in PAGES:
    path = ROOT / name / 'index.html'
    parser = Meta()
    parser.feed(path.read_text(encoding='utf-8'))
    assert parser.policies, f'/{name}/: falta CSP'
    directives = {}
    for policy in parser.policies:
        for part in policy.split(';'):
            tokens = part.strip().split()
            if tokens:
                directives.setdefault(tokens[0], []).append(tokens[1:])
    assert any("'none'" in values for values in directives.get('object-src', [])), f'/{name}/: object-src no bloquea objetos'
    assert 'base-uri' in directives, f'/{name}/: falta base-uri'
    assert 'script-src' in directives, f'/{name}/: falta script-src'
    for values in directives['script-src']:
        assert '*' not in values, f'/{name}/: script-src permite origen universal'
        assert "'unsafe-eval'" not in values, f'/{name}/: script-src permite unsafe-eval'
    print(f'PASS /{name}/ CSP')
