#!/usr/bin/env python3
"""Simple RSS generator for /cuaderno entries.

Scans HTML files under 'cuaderno' for JSON-LD or meta title/date and emits
feed.xml. The output links to /assets/rss.xsl so the feed renders as a
readable page when opened directly in a browser, while staying valid RSS 2.0
for feed readers (the xml-stylesheet PI is presentation-only).

Usage:
    python scripts/build-feed.py
    python scripts/build-feed.py --check
"""
import argparse
import os
import sys
import re
import json
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(__file__))
CUADERNO = os.path.join(ROOT, 'cuaderno')
OUT = os.path.join(ROOT, 'cuaderno', 'feed.xml')
XSL_PATH = os.path.join(ROOT, 'assets', 'rss.xsl')
XSL_HREF = '/assets/rss.xsl'
STALE_CHANNEL_MARKERS = ('fantasía juvenil', 'portales', 'worldbuilding', 'samuel entre mundos')

def find_html_files():
    for dirpath, dirs, files in os.walk(CUADERNO):
        for f in files:
            if f.lower().endswith('.html'):
                yield os.path.join(dirpath, f)

def is_noindex(html_text):
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', html_text, flags=re.I)
    if not m:
        return False
    return 'noindex' in m.group(1).lower()

# /cuaderno/ ya no es solo articulos: los hubs tematicos del doc 55
# (/cuaderno/temas/, /cuaderno/temas/{slug}/) tambien viven bajo este
# directorio y son indexables, pero no son entradas nuevas -- son una capa de
# navegacion sobre articulos que YA estan en el feed individualmente.
# Meterlos tambien como item de RSS duplicaria contenido para el suscriptor
# sin dar nada nuevo que leer. Un CollectionPage no es un Article.
ARTICLE_TYPES = {'Article', 'BlogPosting', 'NewsArticle', 'TechArticle'}
NON_ARTICLE_TYPES = {'CollectionPage'}


def is_non_article_page(json_ld_root) -> bool:
    """True si el @graph de la pagina declara explicitamente un tipo que NO
    es una entrada de blog (p.ej. CollectionPage), sin declarar ningun tipo
    de articulo junto a el."""
    if not isinstance(json_ld_root, dict):
        return False
    graph = json_ld_root.get('@graph')
    if not isinstance(graph, list):
        return False
    types = set()
    for node in graph:
        if isinstance(node, dict):
            t = node.get('@type')
            if isinstance(t, str):
                types.add(t)
            elif isinstance(t, list):
                types.update(x for x in t if isinstance(x, str))
    return bool(types & NON_ARTICLE_TYPES) and not (types & ARTICLE_TYPES)


def extract_metadata(path):
    s = open(path, encoding='utf8', errors='ignore').read()
    if is_noindex(s):
        return {'path': path, 'title': None, 'url': None, 'date': None, 'description': None, 'skip': True}
    # Try JSON-LD
    m = re.search(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', s, flags=re.I)
    title=None; url=None; date=None; desc=None
    if m:
        try:
            j=json.loads(m.group(1))
            if is_non_article_page(j):
                return {'path': path, 'title': None, 'url': None, 'date': None, 'description': None, 'skip': True}
            # Every article on the site emits its JSON-LD as a top-level
            # @graph (Article + BreadcrumbList, etc), never a flat Article
            # object -- so node = j always picked the @graph WRAPPER, whose
            # .get('name')/.get('datePublished') are always None even though
            # the real values sit one level down. That silently dropped
            # every item's pubDate (confirmed empty in production feed.xml)
            # and degraded the intended date sort to the alphabetical
            # fallback below.
            node = None
            if isinstance(j, dict) and isinstance(j.get('@graph'), list):
                for candidate in j['@graph']:
                    if not isinstance(candidate, dict):
                        continue
                    t = candidate.get('@type')
                    types = {t} if isinstance(t, str) else set(t or [])
                    if types & ARTICLE_TYPES:
                        node = candidate
                        break
            elif isinstance(j, dict):
                node = j
            elif isinstance(j, list) and j:
                node = j[0]
            if node:
                title = node.get('name') or node.get('headline')
                url = node.get('url')
                date = node.get('datePublished') or node.get('dateModified')
                desc = node.get('description')
        except Exception:
            pass
    # Fallback to meta title
    if not title:
        m = re.search(r'<title>([^<]+)</title>', s, flags=re.I)
        if m: title = m.group(1).strip()
    # canonical link
    if not url:
        m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', s, flags=re.I)
        if m: url = m.group(1)
    # date meta
    if not date:
        m = re.search(r'<meta[^>]+name=["\']datePublished["\'][^>]*content=["\']([^"\']+)["\']', s, flags=re.I)
        if m: date = m.group(1)
    # description meta
    if not desc:
        m = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', s, flags=re.I)
        if m: desc = m.group(1)
    return {'path': path, 'title': title, 'url': url, 'date': date, 'description': desc, 'skip': False}

def iso_to_rfc2822(d):
    try:
        dt = datetime.fromisoformat(d.replace('Z','+00:00'))
        return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
    except Exception:
        return None

def build_feed_bytes(items):
    root = Element('rss', version='2.0')
    ch = SubElement(root, 'channel')
    SubElement(ch, 'title').text = 'Cuaderno — David Porto Díaz'
    SubElement(ch, 'link').text = 'https://davidportodiaz.com/cuaderno/'
    SubElement(ch, 'description').text = 'Entradas recientes del cuaderno'
    for it in items:
        if not it.get('url') or not it.get('title'): continue
        item = SubElement(ch, 'item')
        SubElement(item,'title').text = it['title']
        SubElement(item,'link').text = it['url']
        SubElement(item,'guid').text = it['url']
        if it.get('description'):
            SubElement(item,'description').text = it['description']
        if it.get('date'):
            rfc = iso_to_rfc2822(it['date'])
            if rfc:
                SubElement(item,'pubDate').text = rfc
    body = tostring(root, encoding='unicode')
    # Build the XML declaration and xml-stylesheet PI ourselves: ElementTree's
    # tostring() does not emit a declaration for plain element serialization,
    # and the PI must precede the root element per the W3C Associating Style
    # Sheets spec.
    declaration = "<?xml version='1.0' encoding='UTF-8'?>"
    pi = f'<?xml-stylesheet type="text/xsl" href="{XSL_HREF}"?>'
    return f'{declaration}\n{pi}\n{body}'.encode('utf-8')

def collect_items():
    files = list(find_html_files())
    items = []
    skipped = 0
    for f in files:
        meta = extract_metadata(f)
        if meta.get('skip'):
            skipped += 1
            continue
        if meta.get('url') or meta.get('title'):
            items.append(meta)
    # El orden debe ser determinista en cualquier sistema de archivos: los
    # articulos actuales no publican fecha, asi que ordenar solo por fecha
    # dejaba el orden que devuelve os.walk -- alfabetico en Windows, arbitrario
    # en ext4. El feed se generaba distinto en local y en CI, y --check fallaba
    # en CI sin que hubiera cambiado ningun contenido. Se desempata por URL.
    items.sort(key=lambda x: x.get('url') or x.get('link') or '')
    items.sort(key=lambda x: x.get('date') or '', reverse=True)
    return items[:50], skipped

def validate_xsl_asset(errors):
    if not os.path.isfile(XSL_PATH):
        errors.append(f'falta {XSL_PATH}')
        return
    try:
        ET.parse(XSL_PATH)
    except ET.ParseError as exc:
        errors.append(f'{XSL_PATH} no es XML valido: {exc}')

def validate_feed_content(xml_bytes, errors):
    text = xml_bytes.decode('utf-8')
    expected_pi = f'<?xml-stylesheet type="text/xsl" href="{XSL_HREF}"?>'
    if expected_pi not in text:
        errors.append('falta la instruccion xml-stylesheet en el feed generado')
    lowered = text.lower()
    channel_end = lowered.find('</description>')
    channel_desc = lowered[:channel_end] if channel_end != -1 else lowered
    for marker in STALE_CHANNEL_MARKERS:
        if marker in channel_desc:
            errors.append(f'la descripcion de canal contiene la formulacion antigua centrada en Samuel/fantasia juvenil ("{marker}")')
            break
    try:
        ET.fromstring(text)
    except ET.ParseError as exc:
        errors.append(f'feed.xml generado no es XML valido: {exc}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='comprueba que feed.xml y assets/rss.xsl ya estan al dia, sin escribir')
    args = parser.parse_args()

    if not os.path.isdir(CUADERNO):
        print('No cuaderno directory found, skipping')
        return 0

    items, skipped = collect_items()
    generated = build_feed_bytes(items)

    errors = []
    validate_xsl_asset(errors)
    validate_feed_content(generated, errors)

    if args.check:
        if os.path.isfile(OUT):
            with open(OUT, 'rb') as f:
                current = f.read()
        else:
            current = b''
            errors.append(f'falta {OUT}')
        if current != generated:
            errors.append('feed.xml esta desactualizado respecto al contenido actual de cuaderno/')
        if errors:
            for e in errors:
                print(f'ERROR: {e}', file=sys.stderr)
            return 1
        print(f'OK: feed.xml al dia ({len(items)} entradas, {skipped} excluidas por noindex/no-articulo)')
        return 0

    if errors:
        for e in errors:
            print(f'ERROR: {e}', file=sys.stderr)
        return 1

    with open(OUT, 'wb') as f:
        f.write(generated)
    print(f'Feed written to {OUT} ({len(items)} entradas, {skipped} excluidas por noindex/no-articulo)')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
