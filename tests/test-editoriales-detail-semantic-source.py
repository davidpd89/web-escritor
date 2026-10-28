import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
records = [r for r in source['publishers'] if r.get('publish') is True]
assert records

def nodes(document):
    result = []
    for block in re.findall(r'<script\b[^>]*type=[\x22\x27]application/ld\+json[\x22\x27][^>]*>(.*?)</script>', document, re.S | re.I):
        obj = json.loads(block)
        result.extend(obj.get('@graph', [obj]))
    return result

for record in records:
    rel = Path('editoriales') / record['slug'] / 'index.html'
    page = (ROOT / rel).read_text(encoding='utf-8')
    headings = re.findall(r'<h1\b[^>]*>(.*?)</h1>', page, re.S | re.I)
    visible = [html.unescape(re.sub(r'<[^>]+>', '', h)).strip() for h in headings]
    assert visible == [record['name']], (rel, visible, record['name'])
    canonical = 'https://davidportodiaz.com/editoriales/' + record['slug'] + '/'
    assert len(re.findall(r'<link\b[^>]*rel="canonical"', page)) == 1, rel
    assert f'href="{canonical}"' in page, rel
    assert f'datetime="{record["verified_at"]}"' in page, rel
    found = [n for n in nodes(page) if n.get('@type') == 'WebPage']
    assert len(found) == 1, rel
    node = found[0]
    assert node.get('url') == canonical, rel
    assert node.get('dateModified') == record['page_updated_at'], rel
    assert node.get('about', {}).get('name') == record['name'], rel
print(f'OK: {len(records)} fichas editoriales verificadas')
