from pathlib import Path
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
PATH = 'donde-empieza-la-jaula/index.html'
SPEC = importlib.util.spec_from_file_location('jaula_public_builder', ROOT / 'scripts/build-public-dist.py')
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
entries = [entry for entry in registry['entries'] if entry.get('sourceFile') == PATH]
assert len(entries) == 1, f'{PATH}: registro editorial no unívoco'
status = module.registry_status(entries[0], registry)
assert status in module.GATED_REGISTRY_STATUS, f'{PATH}: estado no protegido: {status}'
assert not module.is_publishable(PATH, ROOT), f'{PATH}: la página staging se considera pública'
original = module.PUBLIC_DIR_PREFIXES
try:
    module.PUBLIC_DIR_PREFIXES = (*original, 'donde-empieza-la-jaula/')
    assert not module.is_publishable(PATH, ROOT), f'{PATH}: añadir el directorio a la allowlist ha expuesto el capítulo inédito'
    rules = module.render_assetsignore(ROOT)
    assert '/donde-empieza-la-jaula/' in rules, f'{PATH}: falta exclusión de staging en .assetsignore generado'
finally:
    module.PUBLIC_DIR_PREFIXES = original
print('OK: la autorización del namespace no anula el gate editorial de Jaula')