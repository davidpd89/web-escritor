from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/'data/content-registry.json').read_text(encoding='utf-8'))
entries={x['id']:x for x in registry['entries']}
assert 'microstory-al-otro-lado' in entries
entry=entries['microstory-al-otro-lado']
assert entry['url']=='/al-otro-lado/'
assert entry['sourceFile']=='al-otro-lado/index.html'
assert entry['parentId']=='awards'
assert entry['territory']=='autor'
assert entry['discoverability']=='contextual'
assert {'reader','press'}<=set(entry['audience'])
for id in [entry['parentId'],entry['hubId'],*entry['relatedIds']]:
    assert id in entries,f'Broken registry reference: {id}'
assert (ROOT/entry['sourceFile']).is_file()
page=(ROOT/entry['sourceFile']).read_text(encoding='utf-8')
awards=(ROOT/'premios.html').read_text(encoding='utf-8')
assert 'href="/al-otro-lado/"' in awards
assert 'href="/premios.html"' in page
assert 'data-family="identity"' in page
assert 'data-page="microstory"' in page
sections=re.findall(r'<section[^>]*id="([^"]+)"[^>]*aria-labelledby="([^"]+)"',page)
assert len(sections)==4
assert {x[0] for x in sections}=={'texto','antologia','evidencia','seguir'}
for section,label in sections:
    assert re.search(r'<h2[^>]*id="'+re.escape(label)+r'"',page),section
print('PASS microstory registry and named sections')
