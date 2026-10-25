from pathlib import Path
from datetime import date
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'


def check(name):
    root = ET.parse(ROOT / name).getroot()
    assert root.tag == f'{{{NS}}}urlset'
    seen = set()
    for entry in root:
        assert entry.tag == f'{{{NS}}}url', entry.tag
        locs = entry.findall(f'{{{NS}}}loc')
        dates = entry.findall(f'{{{NS}}}lastmod')
        assert len(locs) == 1 and locs[0].text, name
        assert len(dates) <= 1
        url = locs[0].text
        parts = urlsplit(url)
        assert parts.scheme == 'https' and parts.netloc == 'davidportodiaz.com', url
        assert not parts.username and not parts.password
        assert not parts.query and not parts.fragment
        assert url not in seen, f'Duplicado: {url}'
        seen.add(url)
        if dates:
            value = dates[0].text
            assert value, url
            date.fromisoformat(value)
        assert all(child.tag in {f'{{{NS}}}loc', f'{{{NS}}}lastmod', f'{{{NS}}}changefreq', f'{{{NS}}}priority'} for child in entry), url
    assert seen, f'{name} vacío'


if __name__ == '__main__':
    for name in ('sitemap.xml', 'editoriales-sitemap.xml'):
        check(name)
    print('PASS sitemap structural integrity')