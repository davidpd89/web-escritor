#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
errors = []
count = 0

for filename in ('sitemap.xml', 'editoriales-sitemap.xml'):
    root = ET.parse(ROOT / filename).getroot()
    for entry in root.findall('s:url', NS):
        loc = entry.findtext('s:loc', namespaces=NS)
        count += 1
        if not loc:
            errors.append(f'{filename}: loc vacío')
            continue
        try:
            parsed = urlsplit(loc)
            valid = (
                parsed.scheme == 'https'
                and parsed.netloc == 'davidportodiaz.com'
                and parsed.username is None
                and parsed.password is None
                and not parsed.query
                and not parsed.fragment
                and '\\' not in loc
                and not any(ord(char) < 32 for char in loc)
                and not any(char.isspace() for char in loc)
                and parsed.path.startswith('/')
                and '//' not in parsed.path
            )
        except ValueError:
            valid = False
        if not valid:
            errors.append(f'{filename}: URL no canónica: {loc}')

assert not errors, '\n'.join(errors[:50])
print(f'PASS sitemap URL syntax: {count} entradas')
