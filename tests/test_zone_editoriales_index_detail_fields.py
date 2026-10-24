import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = [r for r in json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))['publishers'] if r.get('publish') is True]

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'data-editorial-card' in a:
            self.found.append(a)

parsed = Cards()
index = (ROOT / 'editoriales/index.html').read_text(encoding='utf-8')
parsed.feed(index)
actual = {x['data-name']: x for x in parsed.found}
assert len(parsed.found) == len(actual) == len(records)
for row in records:
    label = row['name']
    card = actual[label]
    for attr, field in [('data-status', 'status'), ('data-country', 'country'),
                        ('data-verified-at', 'verified_at'), ('data-group', 'group')]:
        assert card[attr] == row[field], (label, attr)
    assert card['data-direct'] == str(row['direct_submission']).lower()
    detail = (ROOT / 'editoriales' / row['slug'] / 'index.html').read_text(encoding='utf-8')
    assert f'href="/editoriales/{row["slug"]}/"' in index
    assert f'datetime="{row["verified_at"]}"' in detail
print('editoriales index detail: OK')
