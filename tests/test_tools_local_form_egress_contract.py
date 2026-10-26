import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.buttons = []
        self.csp = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.forms.append(a)
        elif tag in ('button', 'input'):
            self.buttons.append(a)
        elif tag == 'meta' and (a.get('http-equiv') or '').lower() == 'content-security-policy':
            self.csp.append(a.get('content', ''))

registry = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
checked = 0
for tool in registry['tools']:
    route = tool['href']
    if tool.get('privacy') != 'local' or not route.startswith('/herramientas/'):
        continue
    page = ROOT / route.lstrip('/') / 'index.html'
    assert page.exists(), f'{route}: página inexistente'
    audit = Audit()
    audit.feed(page.read_text(encoding='utf-8'))
    for form in audit.forms:
        action = form.get('action', '').strip()
        target = urlsplit(action)
        assert not target.scheme and not target.netloc and not action.startswith('//'), f'{route}: formulario con envío externo: {action}'
        assert form.get('method', 'get').lower() != 'post' or not action, f'{route}: POST declarado en formulario local: {action}'
    for control in audit.buttons:
        action = control.get('formaction', '').strip()
        target = urlsplit(action)
        assert not target.scheme and not target.netloc and not action.startswith('//'), f'{route}: formAction externo: {action}'
    assert len(audit.csp) == 1, f'{route}: política CSP ausente o duplicada'
    checked += 1
assert checked >= 4, f'Solo se auditaron {checked} páginas'
print(f'OK: {checked} herramientas sin destinos externos de formulario')
