"""Reject GSC's actual ProfilePage date-only regression, preserving WebPage dates."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'autor.html').read_text(encoding='utf-8')
block = re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)
graph = json.loads(block[1])['@graph']
profile = next(n for n in graph if n.get('@type') == 'ProfilePage')
page = next(n for n in graph if n.get('@type') == 'WebPage')
assert page['dateCreated'] == '2026-05-02'
assert page['dateModified'] == '2026-10-15'
assert page['hasPart']['@id'] == profile['@id']
assert profile['mainEntity']['@id'] == page['mainEntity']['@id']
assert 'dateCreated' not in profile and 'dateModified' not in profile

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'scripts').mkdir()
    (root / 'data').mkdir()
    checker = root / 'scripts/check-public-time-semantics.py'
    checker.write_text((ROOT / 'scripts/check-public-time-semantics.py').read_text(encoding='utf-8'), encoding='utf-8')
    (root / 'data/content-registry.json').write_text(json.dumps({
        'entries': [{'sourceFile': 'autor.html', 'status': 'public'}]
    }), encoding='utf-8')
    for types in ('ProfilePage', ['ProfilePage', 'WebPage']):
        for field in ('dateCreated', 'dateModified'):
            for value, expected in [('2026-05-02', 1), ('2026-05-02T12:00:00+02:00', 0), (None, 0)]:
                node = {'@type': types}
                if value is not None:
                    node[field] = value
                (root / 'autor.html').write_text('<script type="application/ld+json">' + json.dumps(node) + '</script>', encoding='utf-8')
                result = subprocess.run([sys.executable, str(checker)], capture_output=True, text=True)
                assert result.returncode == expected, (types, field, value, result.stdout, result.stderr)
                if expected:
                    assert 'ProfilePage requires DateTime precision' in result.stdout
print('PASS ProfilePage DateTime regression: date-only rejected; precise or absent dates accepted')
