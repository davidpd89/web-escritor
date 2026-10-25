import hashlib
import base64
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.policies = []
        self.scripts = []
        self.active = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))
        if tag == 'script' and not a.get('src') and a.get('type', '').lower() not in ('application/ld+json', 'application/json', 'speculationrules'):
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.scripts.append(''.join(self.parts))
            self.active = False

for name in ('offline.html',):
    doc = Document()
    doc.feed((ROOT / name).read_text(encoding='utf-8'))
    assert len(doc.policies) == 1, f'{name}: se esperaba una CSP y se encontraron {len(doc.policies)}'
    directives = {}
    for part in doc.policies[0].split(';'):
        tokens = part.split()
        if tokens:
            directives[tokens[0].lower()] = tokens[1:]
    for key in ('default-src', 'script-src', 'object-src', 'base-uri'):
        assert key in directives, f'{name}: falta directiva {key}'
    assert "'none'" in directives['object-src'], f'{name}: object-src debe impedir plugins'
    assert "'unsafe-inline'" not in directives['script-src'], f'{name}: unsafe-inline permite scripts arbitrarios'
    for script in doc.scripts:
        if not script.strip():
            continue
        digest = base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii')
        assert "'sha256-" + digest + "'" in directives['script-src'], f'{name}: script inline ejecutable sin hash CSP válido'
print('PASS: CSP de recuperación offline')
