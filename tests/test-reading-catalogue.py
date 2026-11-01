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
    assert len(m.validate(original, ROOT)) == sum(b['estado'] == 'publicado' for b in original['libros'])
    template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
    assert m.render_hub(original, m.validate(original, ROOT), template) == (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
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
    assert 'Criterio editorial y afiliación' in book
    assert 'compras adscritas' not in book and 'Esta comprobación no implica' not in book
    assert '"@type": "Book"' in book and '"@type": "BreadcrumbList"' in book
    assert 'aggregateRating' not in book and '"@type": "Review"' not in book
    assert 'og:image" content="' + m.SITE + b['portada_local'] in book
    assert 'data-catalogue-speak' not in book and '<audio' not in book and 'Referencia técnica externa' in book
    assert 'Fixture aislada de QA' not in book
    assert hub.count('data-catalogue-book ') == 1
    assert hub.count('href="' + m.url(b) + '"') == 3
    assert all(c in hub for c in ('fantasia', 'romantasy', 'halloween', 'juvenil'))
    assert len(m.registry_entries([b])) == 1
    human_map = m.render_map('<main><a href="/cuaderno/">Cuaderno</a></main>', [b])
    assert m.url(b) in human_map and m.render_map(human_map, [b]) == human_map
    real_authors = m.author_records(ROOT)
    real_map = m.render_map('<main></main>', m.validate(original, ROOT), real_authors)
    assert '/recomendaciones/autores/neil-gaiman/' in real_map
    assert m.render_map(real_map, m.validate(original, ROOT), real_authors) == real_map
    sitemap_spec = importlib.util.spec_from_file_location('reading_sitemap', ROOT / 'scripts/build-sitemap.py')
    sitemap = importlib.util.module_from_spec(sitemap_spec)
    sitemap_spec.loader.exec_module(sitemap)
    pagefile = root / (m.url(b).lstrip('/') + 'index.html')
    pagefile.parent.mkdir(parents=True)
    pagefile.write_text(book, encoding='utf-8')
    assert expected in sitemap.collect_urls(root)
    for hidden in ('.ci/browser/Default', '.qa-edge-profile', '.claude/worktrees/debug'):
        debug = root / hidden / 'debug.html'
        debug.parent.mkdir(parents=True, exist_ok=True)
        debug.write_text('<html><head><link rel="canonical" href="https://davidportodiaz.com/debug-leak/"></head></html>', encoding='utf-8')
        assert sitemap.should_skip_file(debug, root)
    assert set(sitemap.collect_urls(root)) == {expected}, 'Local profiles must never enter the public sitemap'
    del b['url_amazon_afiliada']
    without = m.render_book(data, b, template)
    # The global header has its own existing affiliate CTA. Check the book article.
    article = without[without.index('<article class="catalogue-book-layout"'):without.index('</article>')]
    assert 'Ver en Amazon' not in article and 'affiliate-disclosure' not in article
    b['titulo'] = '<script>alert("x")</script>'
    escaped = m.render_book(data, b, template)
    assert '<script>alert' not in escaped and '\\u003cscript' in escaped
    assert m.book_group([{'id': 'cocina'}]) == 'cocina' and m.book_group([{'id': 'adultos'}, {'id': 'fantasia'}]) == 'novela'
    assert m.book_group([{'id': 'cocina'}, {'id': 'desarrollo-personal'}]) == 'cocina' and m.book_group([{'id': 'adultos'}]) == 'otros'
    future = copy.deepcopy(b)
    future.update(fecha_publicacion='2999-01-01', fecha_actualizacion='2026-10-21')
    page = m.render_book(data, future, template)
    assert '"datePublished": "2999-01-01"' not in page, 'una publicacion futura no puede declararse como ya publicada'
    past = copy.deepcopy(b)
    past.update(fecha_publicacion='2026-10-01', fecha_actualizacion='2026-10-21')
    assert '"datePublished": "2026-10-01"' in m.render_book(data, past, template)
    # Calendario de lanzamientos: determinista (no usa el reloj) y solo con fechas completas posteriores a los datos.
    soon, shown = copy.deepcopy(b), copy.deepcopy(b)
    soon.update(id='contrato-futuro', slug='contrato-futuro', titulo='Lanzamiento, con coma; y punto y coma', fecha_publicacion='2999-01-01', fecha_actualizacion='2026-10-20')
    ics = m.render_release_ics([shown, soon])
    assert ics.count('BEGIN:VEVENT') == 1 and 'DTSTART;VALUE=DATE:29990101' in ics and 'DTEND;VALUE=DATE:29990102' in ics
    BS, CRLF = chr(92), chr(13) + chr(10)
    assert 'Lanzamiento' + BS + ', con coma' + BS + '; y punto' in ics.replace(CRLF + ' ', ''), 'el texto del evento debe escaparse'
    assert ics == m.render_release_ics([shown, soon]) and all(len(line.encode()) <= 75 for line in ics.split(CRLF))
    assert 'Añadir al calendario' in m.render_book({**data, 'libros': [shown, soon]}, soon, template)
    assert 'Añadir al calendario' not in m.render_book({**data, 'libros': [shown, soon]}, shown, template)
    weak = copy.deepcopy(shown)
    weak.update(sinopsis_tipo='extracto_editorial', autoria_propia=False, lectura_personal_confirmada=False)
    assert 'sin texto propio' in m.quality_gate(weak), 'un extracto editorial sin señal propia no pasa el umbral'
    assert 'noindex,follow' in m.render_book({**data, 'libros': [weak]}, weak, template, True)
    assert 'noindex' not in m.render_book({**data, 'libros': [weak]}, weak, template), 'en modo informe la ficha sigue indexable'
    assert 'sin texto propio' not in m.quality_gate({**weak, 'sinopsis_tipo': 'resumen_propio'})
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
