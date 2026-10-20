"""Contratos del catálogo: fixtures aisladas, nunca libros públicos inventados."""
import copy
import base64
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(root):
    data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    data['libros'] = [{
        'id': 'contrato-uno', 'slug': 'contrato-uno', 'titulo': 'Título de prueba técnica',
        'autores': ['Autora técnica'], 'estado': 'publicado',
        'descripcion_breve': 'Descripción original de prueba para verificar la plantilla sin publicar un libro inventado.',
        'descripcion_original_confirmada': True, 'edicion': 'Edición técnica de prueba',
        'portada_local': '/assets/reading-covers/contrato-uno.png',
        'portada_fuente_url': 'https://fuente.invalid/cubierta',
        'portada_edicion_verificada': True, 'autorizacion_o_base_uso': 'Fixture aislada de QA',
        'portada_fecha_revision': '2026-10-20', 'portada_ancho': 120, 'portada_alto': 180,
        'fuente_bibliografica_url': 'https://fuente.invalid/edicion',
        'fecha_verificacion': '2026-10-20', 'fecha_actualizacion': '2026-10-20',
        'fecha_publicacion': '2026-10-15', 'fuente_publicacion_url': 'https://fuente.invalid/publicacion',
        'edad_recomendada': 'Desde 14 años', 'fuente_edad_url': 'https://fuente.invalid/edad',
        'isbn13': '9780140328721', 'resenas': [{'titulo': 'Referencia técnica externa', 'url': 'https://fuente.invalid/resena', 'fecha_verificacion': '2026-10-20'}]
    }]
    data['libro_categorias'] = [{'libro_id': 'contrato-uno', 'categoria_id': c} for c in ('fantasia', 'romantasy', 'halloween', 'juvenil')]
    folder = root / 'assets/reading-covers'
    folder.mkdir(parents=True)
    Image.new('RGB', (120, 180), 'navy').save(folder / 'contrato-uno.png')
    return data


def rejected(data, root, mutate, label):
    bad = copy.deepcopy(data)
    mutate(bad)
    try:
        m.validate(bad, root)
    except m.ValidationError:
        return
    raise AssertionError('Se aceptó: ' + label)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    data = fixture(root)
    assert len(m.validate(data, root)) == 1
    original = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    assert m.validate(original, ROOT) == []
    template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
    assert m.render_hub(original, [], template) == (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
    b = data['libros'][0]
    for field, value in [
        ('portada_edicion_verificada', False), ('descripcion_original_confirmada', False),
        ('portada_local', '/assets/reading-covers/../../secret.png'),
        ('portada_local', '/assets/reading-covers/ausente.png'),
        ('portada_ancho', 100), ('fecha_verificacion', '2026-02-30'),
        ('fecha_actualizacion', 'ayer'), ('isbn13', '9780140328722'),
        ('lectura_personal_confirmada', True), ('fuente_bibliografica_url', 'javascript:alert(1)'),
        ('fuente_publicacion_url', ''), ('fuente_edad_url', ''),
        ('url_amazon_afiliada', 'https://www.amazon.es/dp/B000000001'),
        ('url_amazon_afiliada', 'https://www.amazon.es.evil.invalid/dp/B000000001?tag=prueba-21'),
        ('url_amazon_afiliada', 'https://www.amazon.es@evil.invalid/dp/B000000001?tag=prueba-21'),
        ('estado', 'public'), ('slug', '../escape'), ('nota_privada', 'no publicar'),
    ]:
        rejected(data, root, lambda d, f=field, v=value: d['libros'][0].__setitem__(f, v), field)
    rejected(data, root, lambda d: d['libros'].append(copy.deepcopy(b)), 'duplicado id/slug')
    rejected(data, root, lambda d: d['libro_categorias'].append({'libro_id': 'contrato-uno', 'categoria_id': 'no-existe'}), 'categoría inexistente')
    rejected(data, root, lambda d: d['libro_categorias'].append(copy.deepcopy(d['libro_categorias'][0])), 'relación duplicada')
    rejected(data, root, lambda d: d.__setitem__('libro_categorias', []), 'sin categoría')
    multi = copy.deepcopy(data)
    second = copy.deepcopy(b)
    second.update(id='contrato-dos', slug='contrato-dos', titulo='Segundo título técnico', isbn13='9780140449136', descripcion_breve='Otra descripción original y suficientemente larga para el segundo libro de prueba técnica.')
    multi['libros'].append(second)
    rejected(multi, root, lambda d: None, 'portada duplicada')
    multi['libros'][1]['portada_local'] = '/assets/reading-covers/otra.png'
    (root / 'assets/reading-covers/otra.png').write_bytes((root / b['portada_local'].lstrip('/')).read_bytes())
    rejected(multi, root, lambda d: None, 'bytes de cubierta duplicados')
    for state in ('listo', 'borrador'):
        draft = copy.deepcopy(data)
        draft['libros'][0]['estado'] = state
        assert m.validate(draft, root) == []
    b['url_amazon_afiliada'] = 'https://www.amazon.es/dp/B000000001?tag=contrato-21'
    assert len(m.validate(data, root)) == 1
    book = m.render_book(data, b, template)
    hub = m.render_hub(data, [b], template)
    expected = m.SITE + m.url(b)
    assert '<link rel="canonical" href="' + expected + '"' in book
    assert 'rel="sponsored nofollow noopener noreferrer"' in book
    assert 'enlace de afiliado' in book and 'compras adscritas' in book
    assert '"@type": "Book"' in book and '"@type": "BreadcrumbList"' in book
    assert 'aggregateRating' not in book and '"@type": "Review"' not in book
    assert 'og:image" content="' + m.SITE + b['portada_local'] in book
    assert 'data-catalogue-speak' in book and 'Reseña externa:' in book
    assert 'Fixture aislada de QA' not in book
    assert hub.count('data-catalogue-book ') == 1
    assert hub.count('href="' + m.url(b) + '"') == 3
    assert 'fantasia romantasy halloween juvenil' in hub
    assert len(m.registry_entries([b])) == 1
    human_map = m.render_map('<main><a href="/cuaderno/">Cuaderno</a></main>', [b])
    assert m.url(b) in human_map and m.render_map(human_map, [b]) == human_map
    sitemap_spec = importlib.util.spec_from_file_location('reading_sitemap', ROOT / 'scripts/build-sitemap.py')
    sitemap = importlib.util.module_from_spec(sitemap_spec)
    sitemap_spec.loader.exec_module(sitemap)
    pagefile = root / (m.url(b).lstrip('/') + 'index.html')
    pagefile.parent.mkdir(parents=True)
    pagefile.write_text(book, encoding='utf-8')
    assert expected in sitemap.collect_urls(root)
    del b['url_amazon_afiliada']
    without = m.render_book(data, b, template)
    # The global header has its own existing affiliate CTA. Check the book article.
    article = without[without.index('<article class="catalogue-book-layout"'):without.index('</article>')]
    assert 'Ver en Amazon' not in article and 'affiliate-disclosure' not in article
    b['titulo'] = '<script>alert("x")</script>'
    escaped = m.render_book(data, b, template)
    assert '<script>alert' not in escaped and '\\u003cscript' in escaped
    if '--browser-fixture' in sys.argv:
        # Only serialize synthetic HTML for interception in a browser test.
        b['titulo'] = 'Título de prueba técnica'
        second = copy.deepcopy(b)
        second.update(id='contrato-dos', slug='contrato-dos', titulo='Lectura clásica técnica', autores=['Otro autor'], fecha_publicacion='1990-01-01')
        old_data = copy.deepcopy(data)
        old_data['libros'].append(second)
        old_data['libro_categorias'].append({'libro_id': 'contrato-dos', 'categoria_id': 'clasicos'})
        payload = {'hub': m.render_hub(old_data, [b, second], template), 'book': m.render_book(data, b, template), 'cover': base64.b64encode((root / b['portada_local'].lstrip('/')).read_bytes()).decode()}
        Path(sys.argv[sys.argv.index('--browser-fixture') + 1]).write_text(json.dumps(payload), encoding='utf-8')
print('PASS catálogo: validación, estados, duplicados, metadatos, afiliación y HTML estático.')
