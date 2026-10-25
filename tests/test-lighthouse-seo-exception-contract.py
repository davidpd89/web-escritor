import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
config = json.loads((ROOT / 'lighthouserc.json').read_text(encoding='utf-8'))
matrices = config['ci']['assert']['assertMatrix']
exceptions = [m for m in matrices if m['assertions'].get('categories:seo') == 'off']
assert exceptions, 'Expected explicit SEO exceptions'
required = {'document-title', 'meta-description', 'http-status-code', 'canonical', 'link-text', 'crawlable-anchors'}
for matrix in exceptions:
    assertions = matrix['assertions']
    missing = required - assertions.keys()
    assert not missing, f'{matrix["matchingUrlPattern"]}: missing {sorted(missing)}'
    for key in required:
        assert assertions[key] != 'off', f'{key} disabled'
print('PASS: SEO exception contracts')