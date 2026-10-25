import json
import re
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

def parse_date(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()

def published_dates(html):
    dates = []
    for block in re.findall(r'<script[^>]+type=[\x22\x27]application/ld\+json[\x22\x27][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        nodes = data.get('@graph', [data]) if isinstance(data, dict) else data if isinstance(data, list) else []
        for node in nodes:
            if isinstance(node, dict) and node.get('@type') in ('Article', 'BlogPosting', 'WebPage') and node.get('datePublished'):
                dates.append(parse_date(node['datePublished']))
    return dates

class SitemapChronology(unittest.TestCase):
    def test_lastmod_not_before_publication(self):
        tree = ET.parse(ROOT / 'sitemap.xml')
        checked = 0
        for entry in tree.findall('s:url', NS):
            loc = entry.findtext('s:loc', namespaces=NS)
            lastmod = entry.findtext('s:lastmod', namespaces=NS)
            if not loc or not lastmod or not loc.startswith(DOMAIN + '/'):
                continue
            path = unquote(urlsplit(loc).path)
            file = ROOT / path.lstrip('/')
            file = file / 'index.html' if path.endswith('/') else file
            if not file.is_file() or file.suffix != '.html':
                continue
            dates = published_dates(file.read_text(encoding='utf-8'))
            if dates:
                checked += 1
                with self.subTest(path=path):
                    self.assertGreaterEqual(parse_date(lastmod), max(dates))
        self.assertGreater(checked, 0, 'No se contrastaron fechas editoriales')

if __name__ == '__main__':
    unittest.main()