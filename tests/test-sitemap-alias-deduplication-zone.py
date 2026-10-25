from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_sitemap_alias', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    canonical = 'https://davidportodiaz.com/obra/'
    for name, date in [('obra/index.html', '2026-10-20'), ('alias.html', '2026-10-24')]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('<html><head><link rel="canonical" href="' + canonical + '"><script type="application/ld+json">{"@type":"WebPage","dateModified":"' + date + '"}</script></head></html>', encoding='utf-8')
    urls = module.collect_urls(root)
    assert list(urls) == [canonical], f'Alias no consolidados: {urls}'
    assert urls[canonical] == '2026-10-24', f'Fecha incorrecta tras consolidar: {urls}'
    xml = module.render_xml(urls)
    assert xml.count('<loc>') == 1
print('PASS sitemap alias deduplication')
