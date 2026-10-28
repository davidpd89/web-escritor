"""Bounded, cached access to reviewed public publisher catalogues; no Amazon/LLM.

The first live connector uses the edition metadata exposed by Penguin Libros
in its own product element. It never substitutes creation dates for publication
dates and never imports prices, commercial descriptions or customer reviews.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.robotparser import RobotFileParser

from decimal import Decimal, InvalidOperation

from reading_intake_core import clean_title, edition_date, isbn13, normalize_text
from reading_taxonomy import keyword_list

AGENT = 'DavidPortoReadingCatalogue/1.0 (+https://davidportodiaz.com)'
PRODUCT_PATH = re.compile(r'^/es/[^/?]+/\d+-libro-[^/?]+-(97[89]\d{10})/?$')


class SourceError(ValueError):
    pass


class PlainParagraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs, self.parts, self.ignored = [], [], 0

    def flush(self):
        text = ' '.join(' '.join(self.parts).split())
        if text:
            self.paragraphs.append(text)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1
        if tag in ('p', 'div', 'br', 'li'):
            self.flush()

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        if tag in ('p', 'div', 'li'):
            self.flush()

    def handle_data(self, text):
        if not self.ignored:
            self.parts.append(text)


def editorial_excerpt(value, limit=24):
    """A short attributed excerpt, never the publisher's complete synopsis."""
    parser = PlainParagraphs()
    parser.feed(str(value or ''))
    parser.flush()
    candidates = [p for p in parser.paragraphs if len(p.split()) >= 10
                  and not normalize_text(p).startswith(('resenas', 'la critica', 'criticas', 'sobre el autor'))
                  and not p.startswith(('«', '“', '"'))]
    if not candidates:
        return ''
    def score(text):
        folded = normalize_text(text)
        letters = [ch for ch in text if ch.isalpha()]
        uppercase = sum(ch.isupper() for ch in letters) / max(1, len(letters))
        value = min(len(text.split()), 80) / 20
        if uppercase > .6:
            value -= 10
        if any(word in folded for word in ('bestseller', 'premio', 'exito internacional', 'vuelve el autor', 'llega a las librerias', 'nuevo libro', 'fenomeno editorial')):
            value -= 4
        if text.count('?') or text.count('¿'):
            value -= 3
        return value
    text = max(enumerate(candidates), key=lambda pair: (score(pair[1]), -pair[0]))[1]
    words = text.split()
    return ' '.join(words[:limit]).rstrip(' ,;:') + ('…' if len(words) > limit else '')


def allowed_url(raw, hosts):
    p = urlsplit(raw)
    if p.scheme != 'https' or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443) or p.fragment:
        raise SourceError('URL fuera de las fuentes editoriales autorizadas')
    return raw


class _Redirects(HTTPRedirectHandler):
    def __init__(self, hosts, before_request):
        self.hosts = hosts
        self.before_request = before_request

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        allowed_url(newurl, self.hosts)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            self.before_request()
        return redirected


class CachedHTTP:
    """Every physical request counts; one attempt, then next-run backoff.

    Fixed reviewed hosts also constrain redirects. Cache holds public responses
    in local/Actions cache only, never in the published dataset or artifacts.
    """
    def __init__(self, cache: Path, hosts, *, budget=80, delay=1.5, now=None):
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)
        self.hosts = tuple(hosts)
        self.budget = budget
        self.delay = delay
        self.now = now or time.time
        self.requests = self.hits = 0
        self.last_request = 0.0
        self.robots = {}
        self.opener = build_opener(_Redirects(self.hosts, self._before_request))

    def _before_request(self):
        if self.requests >= self.budget:
            raise SourceError('Presupuesto diario de solicitudes agotado')
        pause = self.delay - (time.monotonic() - self.last_request)
        if pause > 0:
            time.sleep(pause)
        self.requests += 1
        self.last_request = time.monotonic()

    def get(self, url, *, ttl=86400, limit=5_000_000, robots=True):
        allowed_url(url, self.hosts)
        if robots:
            origin = 'https://' + urlsplit(url).netloc
            if origin not in self.robots:
                try:
                    content = self.get(origin + '/robots.txt', ttl=86400, limit=150_000, robots=False)
                    parser = RobotFileParser()
                    parser.parse(content.decode('utf-8').splitlines())
                except HTTPError as exc:
                    if exc.code != 404:
                        raise SourceError('No se ha podido verificar robots.txt') from exc
                    parser = RobotFileParser()
                    parser.parse([])
                self.robots[origin] = parser
            if not self.robots[origin].can_fetch(AGENT.split('/')[0], url):
                raise SourceError('La fuente no permite esta ruta en robots.txt')
        key = hashlib.sha256(url.encode()).hexdigest()
        body, stamp = self.cache / (key + '.body'), self.cache / (key + '.json')
        if body.is_file() and stamp.is_file():
            meta = json.loads(stamp.read_text(encoding='utf-8'))
            age = self.now() - meta['retrieved_at']
            if 0 <= age < ttl and body.stat().st_size <= limit:
                self.hits += 1
                return body.read_bytes()
        self._before_request()
        req = Request(url, headers={'User-Agent': AGENT, 'Accept': 'text/html, image/*;q=0.9, */*;q=0.5'})
        with self.opener.open(req, timeout=25) as response:
            allowed_url(response.url, self.hosts)
            content = response.read(limit + 1)
            if len(content) > limit:
                raise SourceError('Respuesta editorial demasiado grande')
        tmp = body.with_suffix('.tmp')
        tmp.write_bytes(content)
        tmp.replace(body)
        stamp.write_text(json.dumps({'url': url, 'retrieved_at': self.now()}), encoding='utf-8')
        return content


class ProductHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.products = []
        self.links = []
        self.canonical = None
        self._anchor = None
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'meta' and d.get('content'):
            self.meta[d.get('name') or d.get('property')] = d['content']
        if tag == 'link' and d.get('rel') == 'canonical':
            self.canonical = d.get('href')
        if d.get('data-product'):
            try:
                item = json.loads(d['data-product'])
                if isinstance(item, dict):
                    self.products.append(item)
            except ValueError:
                pass
        if tag == 'a' and d.get('href'):
            self._anchor = {'url': d['href'], 'text': ''}
            self.links.append(self._anchor)

    def handle_data(self, text):
        if self._anchor is not None:
            self._anchor['text'] += text

    def handle_endtag(self, tag):
        if tag == 'a':
            self._anchor = None


def product_links(document, source):
    parser = ProductHTML()
    parser.feed(document)
    links = []
    for a in parser.links:
        url = urljoin(source, html.unescape(a['url']))
        p = urlsplit(url)
        if p.hostname == urlsplit(source).hostname and not p.query and PRODUCT_PATH.fullmatch(p.path) and isbn13(PRODUCT_PATH.fullmatch(p.path).group(1)):
            if url not in links:
                links.append(url)
    return links


def publisher_author_bio(document, source, name):
    parser = ProductHTML()
    parser.feed(document)
    if parser.canonical and parser.canonical.rstrip('/') != source.rstrip('/'):
        raise SourceError('La biografía no conserva su URL canónica')
    title = normalize_text(parser.meta.get('og:title', ''))
    expected = normalize_text(name)
    if not title.startswith(expected):
        raise SourceError('La ficha de autor no coincide con el nombre de la edición')
    raw = parser.meta.get('description') or parser.meta.get('og:description') or ''
    if '\ufffd' in raw or len(raw.split()) < 12:
        raise SourceError('Biografía editorial ausente o dañada')
    words = ' '.join(raw.split()).split()
    return ' '.join(words[:24]).rstrip(' ,;:') + ('…' if len(words) > 24 else '')


def _pvp_centimos(product):
    """PVP fijado por la editorial (precio sin el descuento de tienda), en céntimos.

    Los libros tienen precio fijo en España: `price_without_reduction` es ese PVP y no el
    precio de ningún minorista. Sin importe claro y plausible no se publica nada.
    """
    for key, with_discount in (('price_without_reduction', True), ('price_amount', False)):
        raw = product.get(key)
        if raw in (None, '') or (with_discount and str(product.get('has_discount')) != 'True'):
            continue
        try:
            cents = int((Decimal(str(raw)) * 100).quantize(Decimal('1')))
        except (InvalidOperation, ValueError):
            continue
        if 100 <= cents <= 20000:
            return cents
    return None


def penguin_edition(document, source):
    """Strict selected edition, not recommendations included lower on the page."""
    parser = ProductHTML()
    parser.feed(document)
    path = PRODUCT_PATH.fullmatch(urlsplit(source).path)
    expected = isbn13(path.group(1)) if path else None
    if not expected or (parser.canonical and parser.canonical.rstrip('/') != source.rstrip('/')):
        raise SourceError('La ficha no conserva la edición canónica esperada')
    items = [p for p in parser.products if str(p.get('reference')) == expected and p.get('features')]
    if len(items) != 1:
        raise SourceError('Metadatos de edición ausentes o ambiguos')
    p = items[0]
    features = {normalize_text(f.get('name', '')): str(f.get('value', '')).strip() for f in p['features'] if isinstance(f, dict)}
    title = clean_title(html.unescape(str(p.get('name', ''))))
    authors = list(dict.fromkeys(html.unescape(a).strip()
        for feature in p['features'] if isinstance(feature, dict) and normalize_text(feature.get('name', '')) == 'autor'
        for a in re.split(r'\s*[;|]\s*', str(feature.get('value', ''))) if a.strip()))
    publisher = features.get('editorial', '')
    language = features.get('idioma', '').casefold()
    if not title or not authors or not publisher or language not in ('es', 'espanol', 'castellano') or features.get('region') != 'ES':
        raise SourceError('Faltan autoría, sello o edición española comprobable')
    if features.get('cod tipo material') not in ('ZLIB', 'ZEDIG', 'ZAUDIO'):
        raise SourceError('Tipo de producto no bibliográfico o no admitido')
    published, precision = edition_date(features.get('fecha de publicacion', ''))
    if not published:
        raise SourceError('Fecha editorial ausente o inválida')
    binding = features.get('tipo de encuadernacion', '')
    physical = normalize_text(binding)
    format_id = 'tapa-dura' if physical.startswith('tapa dura') else 'tapa-blanda' if any(x in physical for x in ('rustica', 'tapa blanda', 'bolsillo')) else 'ebook' if features.get('cod tipo material') == 'ZEDIG' else 'audiolibro' if features.get('cod tipo material') == 'ZAUDIO' else None
    if not format_id:
        raise SourceError('Encuadernación desconocida')
    cover = (p.get('cover') or {}).get('large') or {}
    image = cover.get('url')
    if not image or urlsplit(image).hostname != 'www.penguinlibros.com':
        raise SourceError('Portada editorial ausente')
    count = features.get('paginas', '')
    pvp = _pvp_centimos(p)
    author_sources = {name: next((urljoin(source, a['url']) for a in parser.links
        if normalize_text(a['text']) == normalize_text(name)
        and urlsplit(urljoin(source, a['url'])).hostname == 'www.penguinlibros.com'
        and re.fullmatch(r'/es/\d+-[a-z0-9-]+', urlsplit(urljoin(source, a['url'])).path)), source) for name in authors}
    return {'isbn13': expected, 'titulo': title, 'autores': authors, 'editorial': publisher,
            'fecha_publicacion_edicion': published, 'precision_fecha': precision,
            'idioma': 'es', 'formato_edicion': format_id, 'encuadernacion': binding,
            'numero_paginas': int(count) if count.isdigit() else None,
            'materias': [html.unescape(str(p.get('category_name', '')))],
            'edad_recomendada': features.get('target de edad', ''),
            'portada_fuente_url': image, 'fuente_bibliografica_url': source,
            'fuentes_autores': author_sources, 'coleccion': features.get('coleccion', ''),
            'sinopsis_breve': editorial_excerpt(p.get('description')) or editorial_excerpt(p.get('description_short')),
            'palabras_clave': keyword_list(html.unescape(str(p.get('meta_keywords', '')))),
            'pvp_centimos': pvp}
