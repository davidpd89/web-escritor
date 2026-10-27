#!/usr/bin/env python3
import base64
import hashlib
import re
import subprocess
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.buffer = []
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag != 'script':
            return
        a = dict(attrs)
        kind = (a.get('type') or '').lower()
        self.active = not a.get('src') and kind not in {'application/ld+json', 'application/json', 'text/plain'}
        self.buffer = []
    def handle_data(self, data):
        if self.active:
            self.buffer.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(''.join(self.buffer))
            self.active = False

STYLE_RE = re.compile(r'<style(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</style>', re.I)
styles_checked = 0

files = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for rel in files:
    if not rel or rel.startswith(('tests/', 'qa/', 'lab/', 'scripts/')):
        continue
    html = (ROOT / rel).read_text(encoding='utf-8')
    parser = Scripts()
    parser.feed(html)
    csp = re.search(r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html, re.I)
    if csp:
        style_src = re.search(r'(?:^|;)\s*style-src\s([^;]*)', csp.group(1))
        # Sin 'unsafe-inline', cada <style> inline necesita su hash exacto.
        if style_src and "'unsafe-inline'" not in style_src.group(1):
            for style in STYLE_RE.findall(html):
                if not style.strip():
                    continue
                styles_checked += 1
                digest = base64.b64encode(hashlib.sha256(style.encode('utf-8')).digest()).decode('ascii')
                if "'sha256-" + digest + "'" not in style_src.group(1):
                    errors.append(f'{rel}: SHA-256 de <style> ausente o desactualizado (ejecuta scripts/build-site-shell.py)')
    if not parser.blocks:
        continue
    if not csp:
        errors.append(f'{rel}: scripts inline sin CSP')
        continue
    policy = csp.group(1)
    for script in parser.blocks:
        if not script.strip():
            continue
        checked += 1
        digest = base64.b64encode(hashlib.sha256(script.encode('utf-8')).digest()).decode('ascii')
        if "'sha256-" + digest + "'" not in policy:
            errors.append(f'{rel}: SHA-256 ausente o desactualizado (ejecuta scripts/build-site-shell.py)')
assert checked, 'No se encontraron scripts inline ejecutables'
assert not errors, '\n'.join(errors[:100])
print(f'PASS hashes CSP: {checked} scripts inline, {styles_checked} estilos inline')
