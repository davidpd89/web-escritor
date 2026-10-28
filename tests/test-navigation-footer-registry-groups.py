from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
nav=json.loads((ROOT/'data/navigation.json').read_text(encoding='utf-8'))
raw=json.loads((ROOT/'data/content-registry.json').read_text(encoding='utf-8'))
extras=json.loads((ROOT/'data/site-shell-extras.json').read_text(encoding='utf-8'))
registry={entry['id']:{**raw.get('defaults',{}),**entry} for entry in raw['entries']}
assert len(nav['footer'])==4
for file in ['index.html','empieza-aqui/index.html','mapa-del-sitio/index.html']:
    html=(ROOT/file).read_text(encoding='utf-8')
    footer=re.search(r'<footer class="site-footer">(.*?)</footer>',html,re.S)
    assert footer,f'{file}: falta footer'
    actual_groups=re.findall(r'<nav aria-label="([^"]+)">',footer.group(1))
    assert actual_groups==list(nav['footer']),f'{file}: grupos {actual_groups} != {list(nav["footer"])}'
    for group,ids in nav['footer'].items():
        pattern=r'<nav aria-label="'+re.escape(group)+r'">(.*?)</nav>'
        match=re.search(pattern,footer.group(1),re.S)
        assert match,f'{file}: falta grupo {group}'
        actual=re.findall(r'<a\b[^>]*href="([^"]+)"',match.group(1))
        expected=[registry[item]['url'] for item in ids]
        for extra in extras.get('footerNavExtras', {}).values():
            if file not in extra.get('pages', []) or extra['group'] != group:
                continue
            extra_url=registry[extra['id']]['url']
            if extra_url not in expected:
                expected.append(extra_url)
        assert actual==expected,f'{file}/{group}: {actual} != {expected}'
        assert len(actual)==len(set(actual)),f'{file}/{group}: enlaces duplicados'
print('PASS footer registry groups across three families')
