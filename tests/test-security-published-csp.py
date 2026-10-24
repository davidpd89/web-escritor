#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {'recomendaciones', 'libros', 'cuaderno', 'fragmento', 'universo', 'asistente', 'convocatorias-escritores', 'editoriales', 'accesibilidad', 'herramientas', 'lecturas', 'mapa-del-sitio'}
ROOT_PAGES = {'index.html', 'eventos.html', 'ferias.html', 'premios.html', '404.html', 'offline.html', 'autor.html', 'prensa.html'}

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('http-equiv') or '').lower() == 'content-security-policy':
            self.policies.append(a.get('content') or '')

tracked = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode('utf-8').split('\0')
files = [p for p in tracked if p and (p.split('/')[0] in FAMILIES or p in ROOT_PAGES)]
assert files, 'No se encontraron páginas publicadas'
errors = []
for rel in files:
    audit = Audit()
    audit.feed((ROOT / rel).read_text(encoding='utf-8'))
    if len(audit.policies) != 1:
        errors.append(f'{rel}: {len(audit.policies)} CSP; se esperaba una')
        continue
    policy = audit.policies[0]
    rules = {part.strip().split()[0]: part.strip().split()[1:] for part in policy.split(';') if part.strip()}
    for directive in ('default-src', 'script-src', 'object-src', 'base-uri'):
        if directive not in rules:
            errors.append(f'{rel}: falta {directive}')
    if rules.get('object-src') != ["'none'"]:
        errors.append(f'{rel}: object-src no está cerrado')
    if '*' in rules.get('default-src', []) or "'unsafe-eval'" in rules.get('script-src', []):
        errors.append(f'{rel}: política excesivamente permisiva')
if errors:
    raise AssertionError('\n'.join(errors[:100]))
print(f'PASS CSP publicada: {len(files)} documentos')
