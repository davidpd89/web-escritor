import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PublicationDateSitemap(unittest.TestCase):
    def test_metadata_and_sitemap_equal_real_revision(self):
        builder = (ROOT / 'scripts/build-editoriales.py').read_text(encoding='utf-8')
        revised = re.search('METHODOLOGY_REVISED = "([0-9-]+)"', builder)
        self.assertIsNotNone(revised)
        data = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        published = [p for p in data['publishers'] if p.get('publish')]
        expected = max([revised.group(1)] + [p['page_updated_at'] for p in published])
        html = (ROOT / 'metodologia-editorial/index.html').read_text(encoding='utf-8')
        payload = re.search('<script type="application/ld\\+json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(payload)
        graph = json.loads(payload.group(1))['@graph']
        webpage = next(x for x in graph if x['@type'] == 'WebPage')
        self.assertEqual(webpage['dateModified'], expected)
        tree = ET.parse(ROOT / 'editoriales-sitemap.xml')
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        dates = {}
        for entry in tree.findall('s:url', ns):
            url = entry.findtext('s:loc', namespaces=ns)
            dates[url] = entry.findtext('s:lastmod', namespaces=ns)
        self.assertEqual(dates['https://davidportodiaz.com/metodologia-editorial/'], expected)

if __name__ == '__main__':
    unittest.main()