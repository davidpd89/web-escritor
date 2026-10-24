from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('editoriales_url_schemes', ROOT / 'scripts/build-editoriales.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
invalid = ['http://example.org', 'javascript:alert(1)', 'data:text/html,hello', '//example.org', '/contacto/', 'mailto:test@example.org', '', None]
for value in invalid:
    try:
        module.require_https(value, 'test.url')
    except module.ValidationError:
        pass
    else:
        raise AssertionError(f'URL insegura admitida: {value!r}')
for value in ['https://example.org', 'https://example.org/ruta?x=1']:
    module.require_https(value, 'test.url')
print('editoriales URL schemes: OK')
