#!/usr/bin/env python3
"""15 contratos JSON-LD transversales. Solo stdlib; sin red externa.

Ejecutar: python3 -m unittest discover -s tests -p test-jsonld-transversal.py -v
"""
from __future__ import annotations

import html
import json
import re
import unittest
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = 'https://davidportodiaz.com'
SCRIPT_RE = re.compile(r'<script\b([^>]*)>(.*?)</script\s*>', re.I | re.S)
TYPE_RE = re.compile(r'\btype\s*=\s*[\"\']application/ld\+json[\"\']', re.I)
TAG_RE = re.compile(r'<[^>]+>')


def attrs(tag):
    return {k.lower(): html.unescape(v) for k, v in re.findall(r'([\w:-]+)\s*=\s*[\"\']([^\"\']*)[\"\']', tag)}


def tags(source, tag):
    return re.findall(r'<' + tag + r'\b[^>]*>', source, re.I)


def norm(value):
    text = html.unescape(TAG_RE.sub(' ', str(value or '')))
    return ' '.join(text.split()).casefold()


def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', norm(value)) if not unicodedata.combining(c))


def source(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def registry_pages():
    data = json.loads(source('data/content-registry.json'))
    result = set()
    for entry in data['entries']:
        item = {**data.get('defaults', {}), **entry}
        rel = item.get('sourceFile', '')
        if item.get('status') == 'public' and rel.endswith('.html'):
            result.add(rel)
    return sorted(result)


def pages():
    extra = {
        'asistente/index.html', 'asistente/embed.html',
        'gracias-suscripcion/index.html', 'lecturas/index.html',
        '404.html', 'offline.html', 'privacidad.html'
    }
    return sorted(set(registry_pages()) | extra)


def raw_blocks(markup):
    return [body for tag, body in SCRIPT_RE.findall(markup) if TYPE_RE.search(tag)]


def documents(rel):
    result = []
    for raw in raw_blocks(source(rel)):
        def reject(value):
            raise ValueError('Non-finite JSON number: ' + value)
        result.append(json.loads(raw, parse_constant=reject))
    return result


def nodes(rel):
    for document in documents(rel):
        roots = document if isinstance(document, list) else [document]
        for root in roots:
            if not isinstance(root, dict):
                continue
            graph = root.get('@graph')
            for node in graph if isinstance(graph, list) else [root]:
                if isinstance(node, dict):
                    yield node


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def types(node):
    value = node.get('@type', [])
    return set(value if isinstance(value, list) else [value])


def meta(markup, key, attr='name'):
    for tag in tags(markup, 'meta'):
        d = attrs(tag)
        if d.get(attr, '').lower() == key.lower():
            return d.get('content')
    return None


def canonical(markup):
    for tag in tags(markup, 'link'):
        d = attrs(tag)
        if 'canonical' in d.get('rel', '').lower().split():
            return d.get('href')
    return None


def heading(markup):
    found = re.search(r'<h1\b[^>]*>(.*?)</h1\s*>', markup, re.I | re.S)
    return norm(found.group(1)) if found else ''


def expected_url(rel):
    if rel == 'index.html':
        return SITE + '/'
    if rel.endswith('/index.html'):
        return SITE + '/' + rel[:-10] + '/'
    return SITE + '/' + rel


def local_file(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != urlsplit(SITE).netloc:
        return None
    path = unquote(parsed.path)
    if '..' in Path(path).parts:
        raise AssertionError('Traversal in JSON-LD URL: ' + url)
    if path.endswith('/'):
        path += 'index.html'
    elif not Path(path).suffix:
        path += '/index.html'
    return ROOT / path.lstrip('/')


def breadcrumb_nodes(rel):
    return [obj for doc in documents(rel) for obj in walk(doc)
            if 'BreadcrumbList' in types(obj) and isinstance(obj.get('itemListElement'), list)]


def visible_breadcrumb(markup):
    found = re.search(r'<nav\b[^>]*class=[\"\'][^\"\']*breadcrumb[^\"\']*[\"\'][^>]*>(.*?)</nav\s*>', markup, re.I | re.S)
    if not found:
        return []
    out = []
    for value in re.findall(r'<li\b[^>]*>(.*?)</li\s*>', found.group(1), re.I | re.S):
        link = re.search(r'<a\b([^>]*)>(.*?)</a\s*>', value, re.I | re.S)
        if link:
            out.append((norm(link.group(2)), attrs(link.group(1)).get('href')))
        else:
            out.append((norm(value), None))
    return out


class StructuredDataTransversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.public = registry_pages()
        cls.all_pages = pages()
        cls.cache = {rel: source(rel) for rel in cls.all_pages}
        cls.parsed = {rel: list(nodes(rel)) for rel in cls.all_pages}

    def test_01_registry_census(self):
        """El control no debe pasar tras desaparecer páginas o JSON-LD."""
        self.assertGreaterEqual(len(self.public), 350)
        inspected = 0
        for rel in self.public:
            with self.subTest(page=rel):
                markup = self.cache[rel]
                self.assertTrue(canonical(markup), rel)
                robots = meta(markup, 'robots') or ''
                if 'noindex' not in robots.lower():
                    self.assertTrue(raw_blocks(markup), rel + ': página indexable sin JSON-LD')
                for document in documents(rel):
                    self.assertIsInstance(document, (dict, list), rel)
                inspected += 1
        self.assertGreaterEqual(inspected, 350)

    def test_02_page_entity_canonical_parity(self):
        """URL canónica, WebPage/CollectionPage y og:url no deben discrepar."""
        checked = 0
        page_types = {'WebPage', 'CollectionPage', 'AboutPage', 'ProfilePage', 'ContactPage', 'WebApplication', 'Article'}
        for rel in self.all_pages:
            markup = self.cache[rel]
            url = canonical(markup)
            if not url:
                continue
            og = meta(markup, 'og:url', 'property')
            if og:
                self.assertEqual(og, url, rel)
            for node in self.parsed[rel]:
                if not (types(node) & page_types):
                    continue
                if node.get('url'):
                    with self.subTest(page=rel, entity=node.get('@type')):
                        self.assertEqual(node['url'], url)
                        checked += 1
                if node.get('@id') and 'WebApplication' not in types(node):
                    address = node['@id'].split('#', 1)[0]
                    if address.startswith(SITE):
                        self.assertEqual(address, url, rel)
        self.assertGreater(checked, 200)

    def test_03_breadcrumb_visible_dom_parity(self):
        """Orden, textos y enlaces de BreadcrumbList reflejan la navegación visible."""
        checked = 0
        for rel in self.all_pages:
            visible = visible_breadcrumb(self.cache[rel])
            breadcrumbs = breadcrumb_nodes(rel)
            if not visible or not breadcrumbs:
                continue
            items = breadcrumbs[0]['itemListElement']
            with self.subTest(page=rel):
                self.assertEqual(len(items), len(visible))
                for index, (node, (text, href)) in enumerate(zip(items, visible), 1):
                    self.assertEqual(node.get('position'), index)
                    self.assertEqual(norm(node.get('name')), text)
                    target = node.get('item')
                    if isinstance(target, dict):
                        target = target.get('@id') or target.get('url')
                    expected = SITE + href if href and href.startswith('/') else href
                    if href is None:
                        expected = canonical(self.cache[rel])
                    self.assertEqual(target, expected)
                checked += 1
        self.assertGreater(checked, 30)

    def test_04_graph_reference_resolution(self):
        """Las referencias internas a identificadores tipados deben tener definición."""
        definitions = set()
        references = []
        for rel in self.all_pages:
            for doc in documents(rel):
                for obj in walk(doc):
                    ident = obj.get('@id')
                    if not isinstance(ident, str) or not ident.startswith(SITE) or '#' not in ident:
                        continue
                    if obj.get('@type'):
                        definitions.add(ident)
                    elif set(obj) == {'@id'}:
                        references.append((rel, ident))
        self.assertGreater(len(references), 20)
        for rel, ident in references:
            with self.subTest(page=rel, ref=ident):
                self.assertIn(ident, definitions)

    def test_05_offline_schema_targets(self):
        """Los destinos de url e item en entidades navegables existen localmente."""
        checked = 0
        navigable = {'WebPage', 'CollectionPage', 'Article', 'Book', 'Event', 'WebApplication', 'BreadcrumbList', 'ListItem'}
        for rel in self.all_pages:
            for doc in documents(rel):
                for obj in walk(doc):
                    if not (types(obj) & navigable):
                        continue
                    for field in ('url', 'item'):
                        value = obj.get(field)
                        if isinstance(value, dict):
                            value = value.get('url') or value.get('@id')
                        if not isinstance(value, str):
                            continue
                        path = local_file(value)
                        if path is None:
                            continue
                        if path.suffix.lower() not in ('.html',):
                            continue
                        with self.subTest(page=rel, destination=value):
                            self.assertTrue(path.is_file(), str(path))
                            checked += 1
        self.assertGreater(checked, 100)

    def test_06_context_locale_and_payload_budget(self):
        """Contexto Schema.org, idioma y presupuesto del JSON-LD por documento."""
        checked = 0
        for rel in self.all_pages:
            markup = self.cache[rel]
            language = re.search(r'<html\b[^>]*\blang=[\"\']([^\"\']+)', markup, re.I)
            lang = language.group(1).split('-')[0].lower() if language else None
            blocks = raw_blocks(markup)
            total = sum(len(s.encode('utf-8')) for s in blocks)
            with self.subTest(page=rel):
                self.assertLessEqual(total, 131072, 'JSON-LD superior a 128 KiB')
                for doc in documents(rel):
                    roots = doc if isinstance(doc, list) else [doc]
                    for root in roots:
                        self.assertEqual(root.get('@context'), 'https://schema.org')
                for node in self.parsed[rel]:
                    value = node.get('inLanguage')
                    if value and lang:
                        self.assertEqual(str(value).split('-')[0].lower(), lang)
                        checked += 1
        self.assertGreater(checked, 100)

    def test_07_unique_typed_identifiers(self):
        """Un @id no puede definir entidades distintas dentro del mismo HTML."""
        checked = 0
        for rel in self.all_pages:
            seen = {}
            for doc in documents(rel):
                for obj in walk(doc):
                    ident = obj.get('@id')
                    if not ident or not obj.get('@type'):
                        continue
                    with self.subTest(page=rel, ident=ident):
                        self.assertNotIn(ident, seen, 'Definición duplicada en la página')
                        seen[ident] = obj
                        checked += 1
        self.assertGreater(checked, 200)

    def test_08_book_name_isbn_and_heading(self):
        """Book describe el libro de la ficha, no una edición o autor diferente."""
        count = 0
        for rel in self.all_pages:
            if not rel.startswith('recomendaciones/libros/'):
                continue
            markup = self.cache[rel]
            for book in self.parsed[rel]:
                if 'Book' not in types(book):
                    continue
                with self.subTest(page=rel):
                    self.assertEqual(norm(book.get('name')), heading(markup))
                    self.assertEqual(book.get('url'), canonical(markup))
                    isbn = book.get('isbn')
                    rating_isbns = re.findall(r'\bdata-isbn=[\"\']([^\"\']+)', markup)
                    if isbn and rating_isbns:
                        self.assertTrue(all(x == str(isbn) for x in rating_isbns))
                    count += 1
        self.assertGreater(count, 20)

    def test_09_recommendation_catalogue_dom_bijection(self):
        """Cada entrada estructurada del catálogo corresponde a una tarjeta real."""
        markup = self.cache['recomendaciones/index.html']
        lists = [obj for obj in self.parsed['recomendaciones/index.html'] if 'ItemList' in types(obj)]
        self.assertEqual(len(lists), 1)
        listing = lists[0]
        items = listing['itemListElement']
        cards = re.findall(r'<li\b[^>]*\bdata-catalogue-book\b[^>]*>.*?<a\b[^>]*class=[\"\'][^\"\']*catalogue-card__cover[^\"\']*[\"\'][^>]*href=[\"\']([^\"\']+)', markup, re.I | re.S)
        urls = []
        for item in items:
            value = item['item']
            urls.append(value['url'] if isinstance(value, dict) else value)
        self.assertEqual(len(cards), len(items))
        self.assertEqual(listing['numberOfItems'], len(items))
        self.assertEqual(Counter(SITE + href for href in cards), Counter(urls))
        self.assertEqual([x['position'] for x in items], list(range(1, len(items) + 1)))

    def test_10_universal_itemlist_positions(self):
        """Las listas de libros, categorías y rutas conservan posiciones coherentes."""
        checked = 0
        for rel in self.all_pages:
            for doc in documents(rel):
                for obj in walk(doc):
                    if not (types(obj) & {'ItemList', 'BreadcrumbList'}):
                        continue
                    items = obj.get('itemListElement')
                    if not isinstance(items, list):
                        continue
                    with self.subTest(page=rel, entity=obj.get('@type')):
                        self.assertEqual([x.get('position') for x in items], list(range(1, len(items) + 1)))
                        if 'numberOfItems' in obj:
                            self.assertEqual(obj['numberOfItems'], len(items))
                        checked += 1
        self.assertGreater(checked, 100)

    def test_11_article_visible_dates(self):
        """Las fechas publicadas y modificadas en Article no contradicen el HTML."""
        checked = 0
        for rel in self.all_pages:
            if not rel.startswith('cuaderno/'):
                continue
            markup = self.cache[rel]
            rendered = set(re.findall(r'<time\b[^>]*datetime=[\"\']([^\"\']+)', markup, re.I))
            for node in self.parsed[rel]:
                if 'Article' not in types(node):
                    continue
                with self.subTest(page=rel):
                    pub = node.get('datePublished')
                    mod = node.get('dateModified')
                    self.assertTrue(pub and mod)
                    self.assertLessEqual(date.fromisoformat(pub[:10]), date.fromisoformat(mod[:10]))
                    self.assertIn(pub[:10], {x[:10] for x in rendered})
                    self.assertIn(mod[:10], {x[:10] for x in rendered})
                    checked += 1
        self.assertGreater(checked, 3)

    def test_12_editorial_verification_freshness(self):
        """La fecha estructurada no puede ser anterior a la comprobación visible."""
        checked = 0
        for rel in self.all_pages:
            if not rel.startswith('editoriales/') or rel == 'editoriales/index.html':
                continue
            markup = self.cache[rel]
            page = next((x for x in self.parsed[rel] if 'WebPage' in types(x)), None)
            if not page or not page.get('dateModified'):
                continue
            visible = re.findall(r'<time\b[^>]*datetime=[\"\'](\d{4}-\d{2}-\d{2})', markup)
            if not visible:
                continue
            with self.subTest(page=rel):
                modified = date.fromisoformat(page['dateModified'][:10])
                self.assertGreaterEqual(modified, max(date.fromisoformat(x) for x in visible))
                checked += 1
        self.assertGreater(checked, 50)

    def test_13_awards_person_provenance(self):
        """Los premios personales deben coincidir entre Inicio y Premios."""
        topics = ('aullidos', 'de amor', 'juan andres teno')
        sets = []
        for rel in ('index.html', 'premios.html'):
            persons = [x for x in self.parsed[rel] if 'Person' in types(x) and x.get('@id') == SITE + '/#author']
            self.assertEqual(len(persons), 1, rel)
            awards = persons[0].get('award') or []
            if isinstance(awards, str):
                awards = [awards]
            subjects = {topic for award in awards for topic in topics if topic in fold(award)}
            self.assertEqual(subjects, set(topics), rel)
            self.assertEqual(len(awards), len(topics), rel)
            visible = SCRIPT_RE.sub(lambda m: '' if TYPE_RE.search(m.group(1)) else m.group(0), self.cache[rel])
            for topic in topics:
                self.assertIn(topic, fold(visible), rel)
            sets.append(subjects)
        self.assertEqual(sets[0], sets[1])

    def test_14_noindex_and_error_page_isolation(self):
        """Los estados técnicos no anuncian productos, eventos ni resultados ricos."""
        special = ('404.html', 'offline.html', 'asistente/embed.html')
        for rel in special:
            with self.subTest(page=rel):
                robots = meta(self.cache[rel], 'robots') or ''
                self.assertIn('noindex', robots.lower())
                self.assertEqual(raw_blocks(self.cache[rel]), [])
        restricted = ('asistente/index.html', 'privacidad.html', 'gracias-suscripcion/index.html', 'lecturas/index.html')
        forbidden = {'Product', 'Offer', 'AggregateRating', 'Event', 'SearchAction'}
        for rel in restricted:
            with self.subTest(page=rel):
                robots = meta(self.cache[rel], 'robots') or ''
                self.assertIn('noindex', robots.lower())
                found = set().union(*(types(obj) for doc in documents(rel) for obj in walk(doc))) if documents(rel) else set()
                self.assertFalse(found & forbidden, (rel, found & forbidden))

    def test_15_book_commercial_claims_visible(self):
        """Un Book no debe inventar precio ni puntuación no visibles en su ficha."""
        checked = 0
        for rel in self.all_pages:
            if not rel.startswith('recomendaciones/libros/'):
                continue
            markup = SCRIPT_RE.sub(lambda m: '' if TYPE_RE.search(m.group(1)) else m.group(0), self.cache[rel])
            for book in self.parsed[rel]:
                if 'Book' not in types(book):
                    continue
                rating = book.get('aggregateRating')
                if isinstance(rating, dict):
                    value = rating.get('ratingValue')
                    votes = rating.get('ratingCount') or rating.get('reviewCount')
                    self.assertIsNotNone(value, rel)
                    self.assertIsNotNone(votes, rel)
                    self.assertIn(str(value), html.unescape(markup), rel)
                    self.assertIn(str(votes), html.unescape(markup), rel)
                offers = book.get('offers')
                if offers:
                    entries = offers if isinstance(offers, list) else [offers]
                    for offer in entries:
                        self.assertIsInstance(offer, dict, rel)
                        self.assertTrue(offer.get('priceCurrency'), rel)
                        self.assertIsNotNone(offer.get('price'), rel)
                        self.assertIn(str(offer['price']), html.unescape(markup), rel)
                checked += 1
        self.assertGreater(checked, 20)


if __name__ == '__main__':
    unittest.main()