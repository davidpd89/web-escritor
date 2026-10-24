from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.labels, self.controls, self.sources, self.calendar, self.counts = set(), [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'label' and a.get('for'):
            self.labels.add(a['for'])
        if tag in ('input', 'select') and any(k.startswith('data-radar-') for k in a):
            if a.get('type') != 'checkbox':
                self.controls.append(a)
        if tag == 'a' and 'data-radar-source' in a:
            self.sources.append(a)
        if tag == 'a' and 'data-radar-calendar' in a:
            self.calendar.append(a)
        if 'data-radar-count' in a:
            self.counts.append(a)

p = Markup()
p.feed((ROOT / 'convocatorias-escritores/index.html').read_text(encoding='utf-8'))
assert p.controls and all(a.get('id') in p.labels for a in p.controls)
assert len(p.counts) == 1
assert p.counts[0].get('role') == 'status'
assert p.counts[0].get('aria-live') == 'polite'
assert p.sources
for a in p.sources:
    assert a.get('href', '').startswith('https://')
    assert a.get('target') == '_blank'
    assert {'noopener', 'noreferrer'} <= set(a.get('rel', '').split())
assert len(p.calendar) == 1
assert (ROOT / p.calendar[0]['href'].lstrip('/')).is_file()
print('radar controls: OK')
