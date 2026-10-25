import importlib.util
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'pagefind'
    output.mkdir()
    source = ROOT / 'pagefind'
    manifest = builder.MANIFEST_NAME
    for filename in ('pagefind.js', manifest):
        shutil.copyfile(source / filename, output / filename)
    assert builder.check(ROOT, output) == 0, 'El indice original debe ser valido para realizar la mutacion'
    js = output / 'pagefind.js'
    assert len(js.read_bytes()) > 100, 'Fixture Pagefind inesperadamente vacia'
    js.write_text('throw new Error("INDEX_CORRUPTED_BY_QA");', encoding='utf-8')
    assert builder.check(ROOT, output) != 0, 'FALSO POSITIVO: --check acepta un artefacto Pagefind inutilizable'
print('PASS: generated index corruption detected')
