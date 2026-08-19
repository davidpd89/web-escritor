#!/usr/bin/env python3
"""Simple RSS generator for /cuaderno entries.

Scans HTML files under 'cuaderno' for JSON-LD or meta title/date and emits feed.xml.
"""
import os, sys, re, json
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring

ROOT = os.path.dirname(os.path.dirname(__file__))
CUADERNO = os.path.join(ROOT, 'cuaderno')
OUT = os.path.join(ROOT, 'cuaderno', 'feed.xml')

def find_html_files():
    for dirpath, dirs, files in os.walk(CUADERNO):
        for f in files:
            if f.lower().endswith('.html'):
                yield os.path.join(dirpath, f)

def extract_metadata(path):
    s = open(path, encoding='utf8', errors='ignore').read()
    # Try JSON-LD
    m = re.search(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>', s, flags=re.I)
    title=None; url=None; date=None; desc=None
    if m:
        try:
            j=json.loads(m.group(1))
            # try Article or WebPage
            node = None
            if isinstance(j, dict):
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
    return {'path': path, 'title': title, 'url': url, 'date': date, 'description': desc}

def iso_to_rfc2822(d):
    try:
        dt = datetime.fromisoformat(d.replace('Z','+00:00'))
        return dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
    except Exception:
        return None

def build_feed(items):
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
    xml = tostring(root, encoding='utf-8')
    open(OUT,'wb').write(xml)
    print('Feed written to', OUT)

def main():
    if not os.path.isdir(CUADERNO):
        print('No cuaderno directory found, skipping'); sys.exit(0)
    files = list(find_html_files())
    items = []
    for f in files:
        meta = extract_metadata(f)
        if meta.get('url') or meta.get('title'):
            items.append(meta)
    # sort by date desc if possible
    items.sort(key=lambda x: x.get('date') or '', reverse=True)
    build_feed(items[:50])

if __name__ == '__main__':
    main()
