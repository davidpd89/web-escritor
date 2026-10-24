from pathlib import Path
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[1]
m = runpy.run_path(str(ROOT / 'scripts/build-surprise-content.py'))

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    items = []
    for index in range(5):
        url = f'/contenido-{index}/'
        items.append({'url': url, 'title': f'Contenido {index}', 'type': ['lectura', 'articulo', 'herramienta'][index % 3], 'audiences': ['reader'], 'commercial': False, 'status': 'ready', 'reviewed_at': '2026-10-20'})
        page = root / url.strip('/') / 'index.html'
        page.parent.mkdir(parents=True)
        decoy = 'https://davidportodiaz.com' + url
        page.write_text(f'<html><head><link rel="canonical" href="https://davidportodiaz.com/otra/"></head><body><p>Referencia textual: {decoy}</p></body></html>', encoding='utf-8')
    ready = m['validate']({'schema_version': 1, 'items': items})
    try:
        m['check_repo'](root, ready)
    except ValueError:
        pass
    else:
        raise AssertionError('check_repo ha aceptado una canonical equivocada por encontrar la URL en el cuerpo')
print('PASS: canonical semántica en destinos sorpresa')
