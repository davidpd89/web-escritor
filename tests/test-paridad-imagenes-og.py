#!/usr/bin/env python3
import json
import struct
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            d = dict(attrs)
            if d.get('property', '').startswith('og:'):
                self.values[d['property']] = d.get('content', '')

def dimensions(path):
    raw = path.read_bytes()
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):
        return struct.unpack('>II', raw[16:24])
    if raw[:2] != b'\xff\xd8':
        return None
    i = 2
    while i + 9 < len(raw):
        if raw[i] != 255:
            i += 1
            continue
        marker = raw[i + 1]
        i += 2
        if marker in {216, 217, 1}:
            continue
        if i + 2 > len(raw):
            break
        length = int.from_bytes(raw[i:i + 2], 'big')
        if length < 2:
            break
        if marker in {192, 193, 194, 195, 198, 199} and i + 7 <= len(raw):
            height, width = struct.unpack('>HH', raw[i + 3:i + 7])
            return width, height
        i += length
    return None

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
checked = 0
errors = []
cache = {}
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    rel = entry.get('sourceFile', '')
    if entry['status'] != 'public' or not rel.endswith('.html') or not (ROOT / rel).is_file():
        continue
    meta = Meta()
    meta.feed((ROOT / rel).read_text(encoding='utf-8'))
    image = meta.values.get('og:image', '')
    parsed = urlsplit(image)
    if parsed.netloc != 'davidportodiaz.com' or not {'og:image:width', 'og:image:height'} <= meta.values.keys():
        continue
    local = ROOT / parsed.path.lstrip('/')
    if local.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
        continue
    checked += 1
    if not local.is_file():
        errors.append(f'{rel}: imagen OG inexistente {image}')
        continue
    if local not in cache:
        cache[local] = dimensions(local)
    actual = cache[local]
    expected = (int(meta.values['og:image:width']), int(meta.values['og:image:height']))
    if actual != expected:
        errors.append(f'{rel}: tamaño declarado {expected}, real {actual}')
assert checked > 0, 'Ninguna imagen OG local con dimensiones comprobables'
assert not errors, '\n'.join(errors[:100])
print(f'OK imágenes OG: {checked} páginas, {len(cache)} imágenes únicas')
