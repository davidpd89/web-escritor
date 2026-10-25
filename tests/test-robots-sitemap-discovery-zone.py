from __future__ import annotations
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('zone_publication_robots', ROOT / 'scripts/build-public-dist.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

lines = (ROOT / 'robots.txt').read_text(encoding='utf-8').splitlines()
sitemaps = [line.split(':', 1)[1].strip() for line in lines if line.strip().lower().startswith('sitemap:')]
assert sitemaps, 'robots.txt no anuncia ningún sitemap'
assert len(sitemaps) == len(set(sitemaps)), 'Directivas Sitemap duplicadas'
for url in sitemaps:
    parsed = urlsplit(url)
    assert parsed.scheme == 'https', url
    assert parsed.netloc == 'davidportodiaz.com', url
    assert not parsed.query and not parsed.fragment, url
    rel = parsed.path.lstrip('/')
    assert rel and (ROOT / rel).is_file(), f'Sitemap inexistente: {url}'
    assert publisher.is_publishable(rel, ROOT), f'Sitemap no publicable: {url}'
    tree = ET.parse(ROOT / rel)
    assert tree.getroot().tag in ('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset', '{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex')
print('PASS robots sitemap discovery')
