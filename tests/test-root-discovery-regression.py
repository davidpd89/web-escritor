from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / 'robots.txt').read_text(encoding='utf-8')
groups = []
current_agents = []
current_rules = []
for raw in text.splitlines() + ['']:
    line = raw.split('#', 1)[0].strip()
    if not line:
        if current_agents:
            groups.append((current_agents, current_rules))
            current_agents, current_rules = [], []
        continue
    if ':' not in line: continue
    key, value = [part.strip() for part in line.split(':', 1)]
    key = key.lower()
    if key == 'user-agent':
        if current_rules:
            groups.append((current_agents, current_rules))
            current_agents, current_rules = [], []
        current_agents.append(value.lower())
    elif key in ('allow', 'disallow'):
        current_rules.append((key, value))

sitemaps = [line.split(':', 1)[1].strip() for line in text.splitlines() if line.lower().startswith('sitemap:')]
expected = 'https://davidportodiaz.com/sitemap.xml'
assert sitemaps == [expected], f'robots.txt: sitemap declarado {sitemaps!r}, esperado {expected}'
general = [rules for agents, rules in groups if '*' in agents]
assert len(general) == 1, f'robots.txt: grupos generales encontrados: {len(general)}'
rules = general[0]
assert ('allow', '/') in rules, f'robots.txt: falta Allow: / en grupo general: {rules!r}'
assert not any(k == 'disallow' and v == '/' for k, v in rules), 'robots.txt: bloqueo general de la raíz'
xml = ET.parse(ROOT / 'sitemap.xml').getroot()
locs = [e.text for e in xml.iter() if e.tag.rsplit('}', 1)[-1] == 'loc']
assert 'https://davidportodiaz.com/' in locs, 'sitemap.xml: falta la portada canónica'
print('OK: descubrimiento de raíz')