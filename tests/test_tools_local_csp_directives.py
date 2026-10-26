from pathlib import Path
from html.parser import HTMLParser
import json

ROOT = Path(__file__).resolve().parents[1]

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        if (a.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

def directives(policy):
    result = {}
    for segment in policy.split(';'):
        words = segment.strip().split()
        if words:
            assert words[0] not in result, f'Directiva CSP duplicada: {words[0]}'
            result[words[0]] = words[1:]
    return result

registry = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
checked = 0
for tool in registry['tools']:
    if tool.get('privacy') != 'local':
        continue
    route = tool['href']
    if not route.startswith('/herramientas/'):
        continue
    page = ROOT / route.lstrip('/') / 'index.html'
    assert page.is_file(), f'{route}: documento publicado inexistente'
    parser = Parser()
    parser.feed(page.read_text(encoding='utf-8'))
    assert len(parser.policies) == 1, f'{route}: {len(parser.policies)} políticas CSP; se esperaba una'
    policy = directives(parser.policies[0])
    assert policy.get('object-src') == ["'none'"], f'{route}: object-src inseguro o ausente: {policy.get("object-src")}'
    assert policy.get('base-uri') in (["'self'"], ["'none'"]), f'{route}: base-uri inseguro o ausente: {policy.get("base-uri")}'
    checked += 1
assert checked >= 4, f'Cobertura insuficiente: {checked} herramientas'
print(f'OK: CSP de {checked} herramientas locales')
