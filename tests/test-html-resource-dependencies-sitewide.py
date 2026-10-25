#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'davidportodiaz.com', 'www.davidportodiaz.com'}
RELS = {'stylesheet', 'preload', 'modulepreload', 'manifest', 'icon', 'apple-touch-icon'}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'script' and d.get('src'):
            self.refs.append(d['src'])
        if tag == 'link' and RELS.intersection(set((d.get('rel') or '').lower().split())) and d.get('href'):
            self.refs.append(d['href'])

def target(source, value):
    u = urlsplit(value)
    if u.scheme and u.scheme not in ('https', 'http'):
        return None
    if u.hostname and u.hostname.lower() not in HOSTS:
        return None
    if not u.path:
        return None
    p = unquote(u.path)
    return ROOT / p.lstrip('/') if p.startswith('/') or u.hostname else source.parent / p

names = subprocess.check_output(['git', 'ls-files', '-z', '*.html'], cwd=ROOT).decode().split('\0')
errors = []
checked = 0
for name in names:
    if not name or name.startswith(('tests/', 'qa/', 'scripts/', 'data/', 'lab/')):
        continue
    source = ROOT / name
    parser = Parser()
    parser.feed(source.read_text(encoding='utf-8'))
    for ref in parser.refs:
        dest = target(source, ref)
        if dest is None:
            continue
        checked += 1
        if not dest.is_file():
            errors.append(f'{name}: {ref}')
assert checked > 30, f'Solo {checked} dependencias examinadas'
assert not errors, '\n'.join(errors[:100])
print(f'PASS HTML dependencies: {checked} referencias')
