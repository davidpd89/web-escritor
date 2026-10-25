from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def read(name):
    result = {}
    for node in ET.parse(ROOT / name).findall('s:url', NS):
        loc = node.findtext('s:loc', namespaces=NS)
        date = node.findtext('s:lastmod', namespaces=NS)
        assert loc not in result, f'{name}: URL duplicada {loc}'
        result[loc] = date
    return result


def test_parity():
    general = read('sitemap.xml')
    specialized = read('editoriales-sitemap.xml')
    assert specialized, 'Sitemap especializado vacío'
    errors = []
    for url, date in specialized.items():
        if url not in general:
            errors.append(f'URL ausente del sitemap general: {url}')
        elif date and general[url] and date != general[url]:
            errors.append(f'lastmod contradictorio: {url}: {date} != {general[url]}')
    assert not errors, '\n'.join(errors)


if __name__ == '__main__':
    test_parity()
    print('PASS editoriales sitemap cross parity')