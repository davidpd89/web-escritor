from pathlib import Path
from urllib.parse import urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'prensa.html', 'eventos.html']

for source in PAGES:
    html = (ROOT / source).read_text(encoding='utf-8')
    matches = re.findall(
        r'<script\s+type="speculationrules"[^>]*>(.*?)</script>',
        html, re.S
    )
    assert len(matches) == 1, f'{source}: numero incorrecto de bloques'
    rules = json.loads(matches[0])
    targets = []
    for kind in ('prefetch', 'prerender'):
        for group in rules.get(kind, []):
            targets += group.get('urls', [])

    assert targets, f'{source}: ningun destino especulativo'
    assert len(targets) == len(set(targets)), f'{source}: duplicados'

    for target in targets:
        parsed = urlsplit(target)
        assert not parsed.scheme and not parsed.netloc, (source, target)
        assert parsed.path.startswith('/') and not parsed.query and not parsed.fragment, (source, target)
        local = ROOT / parsed.path.lstrip('/')
        if parsed.path.endswith('/'):
            local /= 'index.html'
        assert local.is_file(), f'{source}: destino inexistente {target}'
        dest = local.read_text(encoding='utf-8')
        robots = re.search(r'<meta\s+name="robots"\s+content="([^"]+)"', dest)
        assert not robots or 'noindex' not in robots.group(1).lower(), target
        canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', dest)
        assert canonical, f'{target}: sin canonical'
        assert urlsplit(canonical.group(1)).path == parsed.path, (source, target)

print('PASS root-speculation-publication')
