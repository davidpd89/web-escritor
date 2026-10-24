#!/usr/bin/env python3
import importlib.util
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_perm', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

pages = {
 'index.html': '<link rel="canonical" href="https://davidportodiaz.com/">',
 'asistente/index.html': '<link rel="canonical" href="https://davidportodiaz.com/asistente/">',
 'accesibilidad/index.html': '<link rel="canonical" href="https://davidportodiaz.com/accesibilidad/">',
 'hidden/index.html': '<meta name="robots" content="noindex"><link rel="canonical" href="https://davidportodiaz.com/hidden/">',
 'duplicate/index.html': '<link rel="canonical" href="https://davidportodiaz.com/asistente/">'
}

outputs = []
for reverse in (False, True):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        entries = list(pages.items())
        if reverse:
            entries.reverse()
        for i, (relative, fragment) in enumerate(entries):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('<html><head>' + fragment + '</head><body><main>QA</main></body></html>', encoding='utf-8')
            os.utime(path, (100000000 + i * 1000, 100000000 + i * 1000))
        outputs.append(mod.render_xml(mod.collect_urls(root)))
assert outputs[0] == outputs[1], 'El XML cambia con el orden físico o mtime'
xml = ET.fromstring(outputs[0])
locs = [node.text for node in xml.findall('.//{*}loc')]
assert len(locs) == len(set(locs)) == 3, locs
assert 'https://davidportodiaz.com/hidden/' not in locs
print('PASS: sitemap determinista ante orden, mtime y canonical duplicado')
