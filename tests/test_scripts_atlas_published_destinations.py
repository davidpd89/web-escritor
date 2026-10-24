from pathlib import Path
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-atlas-literario.py'))
item = {
    'status': 'published',
    'slug': 'biblioteca-prueba',
    'title': 'Biblioteca de prueba',
    'category': 'bibliotecas',
    'summary': 'Descripción de una biblioteca publicada.',
    'country': 'España',
    'relationship': 'library',
    'source_urls': ['https://example.org/fuente'],
    'verified_date': '2026-10-20',
    'image': {'src': '/assets/atlas-literario-placeholder.webp', 'alt': 'Interior', 'credit': 'Archivo', 'license': 'CC BY-SA', 'source_url': 'https://example.org/imagen'}
}
with tempfile.TemporaryDirectory() as temporary:
    out = Path(temporary) / 'atlas-literario'
    data = {'version': 1, 'updated': '2026-10-20', 'items': [item]}
    m['build'](data, {'bibliotecas': 'Bibliotecas'}, out)
    document = (out / 'index.html').read_text(encoding='utf-8')
    assert '/atlas-literario/biblioteca-prueba/' in document
    target = out / item['slug'] / 'index.html'
    assert target.is_file(), f'el generador enlaza una ficha sin destino: {target}'
print('PASS destinos Atlas publicados')
