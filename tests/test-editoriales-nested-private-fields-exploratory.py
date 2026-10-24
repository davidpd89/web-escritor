from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editoriales_private_keys', ROOT / 'scripts/build-editoriales.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
cases = [
    {'notas_privadas': 'secreto'},
    {'sources': [{'metadata': {'prioridad': 1}}]},
    {'history': [{'estado_envio': 'pendiente'}]},
    {'nested': [{'deep': [{'fecha_de_envio': '2026-01-01'}]}]},
    {'extra': {'encaje_noa': 'alto'}},
]
for case in cases:
    try:
        module.scan_forbidden_keys(case)
    except module.ValidationError:
        continue
    raise AssertionError(f'Campo privado no detectado: {case}')
module.scan_forbidden_keys({'sources': [{'label': 'Fuente pública', 'url': 'https://example.org'}]})
print('editoriales recursive private keys: OK')
