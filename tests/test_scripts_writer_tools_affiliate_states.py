from pathlib import Path
import copy
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-writer-tools.py'))
source = json.loads((ROOT / 'data/writer-tools.json').read_text(encoding='utf-8'))
original = copy.deepcopy(source['tools'][0])
plain = m['render_tool'](original)
assert 'rel="sponsored' not in plain, 'enlace ordinario marcado como afiliado'

affiliate = copy.deepcopy(original)
affiliate['affiliate'] = True
affiliate['affiliate_disclosure'] = 'Este enlace puede generar una comisión sin coste adicional para quien lo utilice.'
affiliate['website'] = 'https://example.org/producto?ref=escritor'
mutated = copy.deepcopy(source)
mutated['tools'][0] = affiliate
assert m['validate'](mutated)
rendered = m['render_tool'](affiliate)
assert affiliate['affiliate_disclosure'] in rendered, 'falta declaración visible'
link = re.search(r'<a[^>]+href="https://example.org/producto\?ref=escritor"[^>]*>', rendered)
assert link, 'desaparece el enlace comercial'
assert re.search(r'rel="[^"]*\bsponsored\b', link.group()), 'falta rel=sponsored'
print('PASS: disclosure y rel afiliado')
