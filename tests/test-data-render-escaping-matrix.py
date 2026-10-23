from __future__ import annotations
import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

radar = load('build-radar-opportunities.py', 'qa_radar_escape')
writer = load('build-writer-tools.py', 'qa_writer_escape')
topics = load('build-topic-collections.py', 'qa_topics_escape')
editorials = load('build-editoriales.py', 'qa_editorials_escape')
attack = '\"><img src=x onerror=alert(92817)>'

checks = []
raw = json.loads((ROOT / 'data/radar-opportunities.json').read_text(encoding='utf-8'))
item = copy.deepcopy(raw['items'][0])
item['title'] = attack
item['organizer'] = attack
item['editorial_note'] = attack
checks.append(('radar', radar.card(item)))

raw = json.loads((ROOT / 'data/writer-tools.json').read_text(encoding='utf-8'))
item = copy.deepcopy(raw['tools'][0])
for field in ('name', 'best_for', 'not_for', 'editorial_note'):
    item[field] = attack
checks.append(('writer-tools', writer.render_tool(item)))

checks.append(('topics', topics.head(attack, attack, topics.INDEX_URL, {'@type': 'CollectionPage'})))
checks.append(('editoriales', editorials.page_shell(title=attack, description=attack, canonical='https://davidportodiaz.com/editoriales/', main_html='<main></main>', jsonld={})))

for label, html in checks:
    assert attack not in html, f'{label}: payload sin escapar'
    assert '<img src=x onerror=' not in html, f'{label}: HTML inyectado'
    assert '&lt;img' in html, f'{label}: el texto no se escapó'
    assert 'onerror=alert(92817)>' not in html, f'{label}: atributo ejecutable'

print(f'OK: {len(checks)} generadores comprobados')
