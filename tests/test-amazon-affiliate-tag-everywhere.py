"""Todo enlace publicado a Amazon lleva el tag de afiliado davidporto-21 (incluido el perfil de autor).

Comprueba el parámetro exacto `tag` de la URL: `dib_tag=se` u otros parámetros parecidos no cuentan.
Excepciones: Send to Kindle (servicio, no tienda) y los enlaces cortos amzn.to, que ya llevan el tag en su
destino. El JSON-LD (`sameAs`) conserva la URL canónica: solo se revisan los `<a href>`.
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TAG = 'davidporto-21'
SKIP_DIRS = {'.git', '.local', 'node_modules', 'pagefind', 'tests', 'qa', 'artifacts', '.ci', 'tools', '_dist'}
ANCHOR = re.compile(r'<a\b[^>]*?\bhref="(https?://(?:www\.)?amazon\.(?:es|com)/[^"]*)"[^>]*>', re.I)


def has_tag(url):
    return parse_qs(urlsplit(html.unescape(url)).query).get('tag') == [TAG]


def exempt(url):
    return '/sendtokindle' in url


def violations(text):
    out = []
    for m in ANCHOR.finditer(text):
        url = m.group(1)
        if exempt(url):
            continue
        if not has_tag(url):
            out.append(url)
        elif 'sponsored' not in m.group(0):
            out.append(url + ' (falta rel="sponsored")')
    return out


def self_test():
    assert has_tag('https://www.amazon.es/dp/X?tag=davidporto-21')
    assert has_tag('https://www.amazon.es/s?k=1&amp;tag=davidporto-21#r')
    assert not has_tag('https://www.amazon.es/s?k=1&dib_tag=se')
    assert not has_tag('https://www.amazon.es/stores/author/B0GZFP1JV3')
    assert violations('<a href="https://www.amazon.es/dp/X?tag=davidporto-21" rel="sponsored">') == []
    assert violations('<a href="https://www.amazon.es/dp/X?tag=davidporto-21" rel="noopener">')
    assert violations('<a class="x" href="https://www.amazon.es/stores/author/B0X">')
    assert violations('<a href="https://www.amazon.com/sendtokindle">') == []


def main():
    self_test()
    bad = {}
    pages = 0
    for path in ROOT.rglob('*.html'):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        pages += 1
        found = violations(path.read_text(encoding='utf-8', errors='ignore'))
        if found:
            bad[path.relative_to(ROOT).as_posix()] = found
    if bad:
        for page, urls in sorted(bad.items())[:20]:
            print(f'FAIL {page}: {urls[:3]}')
        sys.exit(f'{sum(map(len, bad.values()))} enlace(s) a Amazon sin tag {TAG} o sin sponsored en {len(bad)} página(s)')
    print(f'PASS: todos los enlaces a Amazon de {pages} páginas llevan tag={TAG} y rel=sponsored')


if __name__ == '__main__':
    main()
