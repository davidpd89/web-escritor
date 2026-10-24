#!/usr/bin/env python3
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_platform_qa', ROOT / 'scripts/build-pagefind-index.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    page = root / 'asistente/index.html'
    page.parent.mkdir(parents=True)
    registry_path = root / 'data/content-registry.json'
    registry_path.parent.mkdir(parents=True)
    registry = {'entries': [{'sourceFile': 'asistente/index.html', 'label': 'Asistente de lectura', 'status': 'public'}]}
    registry_path.write_text(json.dumps(registry), encoding='utf-8')
    rel = 'asistente/index.html'
    raw = b'<html>\n<head>\n<title>Lectura</title>\n</head>\n<body>Texto</body>\n</html>\n'
    page.write_bytes(raw)
    baseline = mod.source_hashes(root, [rel])[rel]
    page.write_bytes(raw.replace(b'\n', b'\r\n'))
    assert mod.source_hashes(root, [rel])[rel] == baseline, 'CRLF provoca deriva'
    page.write_bytes(raw.replace(b'Texto', b'Texto distinto'))
    assert mod.source_hashes(root, [rel])[rel] != baseline, 'Cambio HTML no detectado'
    page.write_bytes(raw)
    registry['entries'][0]['label'] = 'Nuevo nombre accesible'
    registry_path.write_text(json.dumps(registry), encoding='utf-8')
    assert mod.source_hashes(root, [rel])[rel] != baseline, 'Cambio de etiqueta no detectado'
print('PASS: normalización de plataforma y detección de cambios reales')
