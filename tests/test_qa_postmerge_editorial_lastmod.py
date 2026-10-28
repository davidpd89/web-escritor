import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_dates', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

urls = module.collect_urls(ROOT)
published = module.parse_existing(ROOT / 'sitemap.xml')

for rel in ('recomendaciones/index.html', 'cuaderno/index.html', 'editoriales/index.html'):
    path = ROOT / rel
    html = path.read_text(encoding='utf-8')
    canonical, noindex, modified = module.extract_meta(html)
    assert not noindex, f'{rel}: página principal inesperadamente noindex'
    loc = module.normalize_canonical(canonical, ROOT, path)
    assert loc in urls, f'{rel}: URL ausente de collect_urls: {loc}'
    expected = module.normalize_lastmod(modified)
    assert urls[loc] == expected, f'{rel}: lastmod generado {urls[loc]!r}, fecha editorial {expected!r}'
    assert published.get(loc) == urls[loc], f'{rel}: sitemap.xml={published.get(loc)!r}, generador={urls[loc]!r}'

assert published['https://davidportodiaz.com/recomendaciones/'] is not None, 'recomendaciones/index.html: se ha perdido dateModified publicado'
print('OK: fechas editoriales y sitemap coherentes')