#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'publicar-web/index.html').read_text(encoding='utf-8')
REFERENCES = set(re.findall(r'scripts/[\w.-]+\.py', HTML))
EXPECTED = {
    'scripts/build-sitemap.py',
    'scripts/validate_jsonld.py',
    'scripts/check-internal-graph.py',
}
assert REFERENCES == EXPECTED, f'Instrucciones modificadas sin actualizar el contrato: {REFERENCES}'

def execute(script, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *map(str, args)],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )

for script in sorted(REFERENCES):
    assert (ROOT / script).is_file(), script

for script in ('scripts/build-sitemap.py', 'scripts/check-internal-graph.py'):
    result = execute(script, '--help')
    assert result.returncode == 0, f'{script}: {result.stderr}'

with tempfile.TemporaryDirectory() as directory:
    valid = Path(directory) / 'valid.html'
    invalid = Path(directory) / 'invalid.html'
    valid.write_text('<script type="application/ld+json">{"@type":"WebPage"}</script>', encoding='utf-8')
    invalid.write_text('<script type="application/ld+json">{"@type":</script>', encoding='utf-8')
    assert execute('scripts/validate_jsonld.py', valid).returncode == 0
    assert execute('scripts/validate_jsonld.py', invalid).returncode != 0

print('PASS publicar-web: interfaces CLI e instrucciones verificadas')
