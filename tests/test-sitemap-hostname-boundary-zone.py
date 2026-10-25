from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_sitemap_host', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    page = root / 'index.html'
    page.write_text('<html></html>', encoding='utf-8')
    invalid = [
        'https://davidportodiaz.com.ejemplo.org/robo/',
        'https://davidportodiaz.com.attacker.test/',
        'https://davidportodiaz.com@attacker.test/',
        'https://sub.davidportodiaz.com/',
        'https://davidportodiaz.com:444/',
    ]
    for canonical in invalid:
        result = module.normalize_canonical(canonical, root, page)
        assert result is None, f'Hostname no autorizado aceptado: {canonical} -> {result}'
    assert module.normalize_canonical('https://davidportodiaz.com/', root, page) == 'https://davidportodiaz.com/'
print('PASS sitemap hostname boundary')
