#!/usr/bin/env python3
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dist_prune_qa', ROOT / 'scripts/build-public-dist.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / 'dist'
    mod.build(out, ROOT)
    ghost = out / 'assets/qa-stale-asset.js'
    ghost.parent.mkdir(parents=True, exist_ok=True)
    ghost.write_text('const stale = true;', encoding='utf-8')
    assert ghost.exists()
    mod.build(out, ROOT)
    assert not ghost.exists(), 'Build incremental conserva recurso obsoleto'
    manifest = mod.write_manifest(out)
    records = json.loads(manifest.read_text(encoding='utf-8'))['files']
    paths = [item['path'] for item in records]
    expected = sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    assert paths == expected, 'Manifiesto desordenado, incompleto o con elementos inexistentes'
    assert len(paths) == len(set(paths))
    forbidden = ('cloudflare-worker-', 'wrangler', 'lighthouserc', 'package.json')
    assert not any(Path(name).name.startswith(forbidden) for name in paths), 'Archivo de infraestructura publicado'
    assert mod.check_contents(out, ROOT) == 0
print('PASS: limpieza, manifiesto y frontera de publicación')
