from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

builder = load('image_builder', 'build-image-format-ladder.py')
checker = load('image_checker', 'check-image-format-ladder.py')
manifest = json.loads((ROOT / 'data/image-format-ladder.json').read_text(encoding='utf-8'))

builder_errors = builder.manifest_contract_errors(manifest)
checker_errors = checker.manifest_errors(manifest)
assert not builder_errors, f'data/image-format-ladder.json: builder rechaza manifiesto: {builder_errors}'
assert not checker_errors, f'data/image-format-ladder.json: checker rechaza manifiesto: {checker_errors}'

for index, entry in enumerate(manifest['eligible_sources']):
    errors = builder.entry_structure_errors(entry, index)
    assert not errors, f'data/image-format-ladder.json: entrada {index}: {errors}'
    source = Path(entry['source'])
    derivative = Path(entry['derivative'])
    assert source.suffix == '.webp', f'entrada {index}: fuente incorrecta: {source}'
    assert derivative == source.with_suffix('.avif'), f'entrada {index}: derivada incorrecta: {derivative}'
    for field in ('source_sha256', 'derivative_sha256'):
        assert builder.valid_sha256(entry.get(field)), f'entrada {index}: hash invalido en {field}'

print('PASS image checker manifest parity')