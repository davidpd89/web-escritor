#!/usr/bin/env python3
import argparse, html, ipaddress, json, re
from pathlib import Path
from urllib.parse import urlsplit

SLUG_RE=re.compile(r'^[a-z0-9-]+$')
ALLOWED_REL={'book-setting','filming-location','inspiration','writer-route','library','bookshop','book-town','fact-check','mixed','library-list'}


def valid_https_source(url):
    if not isinstance(url, str) or not url.startswith('https://'):
        return False
    if any(ord(ch) <= 32 or ord(ch) == 127 or ch in '<>\\' for ch in url):
        return False
    try:
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.netloc:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        host = parsed.hostname
        if not host:
            return False
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            return False
        if parsed.netloc.endswith(':'):
            return False
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if ':' in host:
                return False
            labels = host.split('.')
            if not all(0 < len(label) <= 63 and re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?', label) for label in labels):
                return False
            if len(host) > 253:
                return False
        return True
    except (ValueError, TypeError):
        return False


def load(path:Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    cats={}
    for category in data.get('categories',[]):
        slug=category['slug']
        if slug in cats:
            raise ValueError(f'slug de categoría duplicado: {slug!r}')
        cats[slug]=category['name']
    if not cats: raise ValueError('Sin categorías')
    for category_slug in cats:
        if not isinstance(category_slug, str) or not SLUG_RE.fullmatch(category_slug):
            raise ValueError(f'slug de categoría inválido: {category_slug!r}')
    seen=set()
    for item in data.get('items',[]):
        slug=item.get('slug','')
        if not SLUG_RE.fullmatch(slug): raise ValueError(f'slug inválido: {slug!r}')
        if slug in seen: raise ValueError(f'slug duplicado: {slug}')
        seen.add(slug)
        if item.get('category') not in cats: raise ValueError(f'categoría inválida en {slug}')
        if item.get('relationship') not in ALLOWED_REL: raise ValueError(f'relationship inválida en {slug}')
        urls=item.get('source_urls') or []
        if not isinstance(urls, list) or not urls or any(not valid_https_source(u) for u in urls):
            raise ValueError(f'{slug}: requiere fuentes HTTPS válidas')
        if item.get('status')=='published':
            image=item.get('image') or {}
            for key in ('src','alt','credit','license','source_url'):
                if not image.get(key): raise ValueError(f'{slug}: imagen publicada sin {key}')
            if not item.get('verified_date'): raise ValueError(f'{slug}: falta verified_date')
    return data,cats


def card(item,cats):
    img=item.get('image') or {}
    src=html.escape(img.get('src') or '/assets/atlas-literario-placeholder.webp')
    alt=html.escape(img.get('alt') or '')
    title=html.escape(item['title']); summ=html.escape(item['summary'])
    cat=html.escape(cats[item['category']]); country=html.escape(item.get('country',''))
    search=html.escape(' '.join([item['title'],item.get('summary',''),item.get('country',''),' '.join(item.get('query_intent',[]))]))
    return f'''<article class="atlas-card" data-atlas-card data-category="{html.escape(item['category'], quote=True)}" data-search="{search}"><img src="{src}" alt="{alt}" width="720" height="450" loading="lazy" decoding="async"><div class="atlas-card__body"><p class="atlas-card__meta"><span>{cat}</span><span>{country}</span></p><h2><a href="/atlas-literario/{item['slug']}/">{title}</a></h2><p>{summ}</p><a href="/atlas-literario/{item['slug']}/">Explorar →</a></div></article>'''


def build(data,cats,out:Path):
    published=[x for x in data['items'] if x.get('status')=='published']
    out.mkdir(parents=True,exist_ok=True)
    options=''.join(f'<option value="{html.escape(slug)}">{html.escape(name)}</option>' for slug,name in cats.items())
    cards=''.join(card(x,cats) for x in published) or '<p>Aún no hay artículos publicados en este dataset de ejemplo.</p>'
    doc=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas literario | David Porto Díaz</title><meta name="description" content="Lugares de libros, bibliotecas extraordinarias, rutas literarias y huellas de escritores, investigados con fuentes y sin mezclar hechos con mitos."><link rel="canonical" href="https://davidportodiaz.com/atlas-literario/"><link rel="stylesheet" href="/styles.css?v=202609-launch-1"><link rel="stylesheet" href="/assets/atlas-literario.css"></head><body><main class="atlas-page" data-atlas-index><header class="atlas-hero"><p class="eyebrow">Atlas literario</p><h1>El mundo de los libros también existe fuera de las páginas.</h1><p class="lead">Lugares reales, bibliotecas, librerías y rutas investigadas con una regla: diferenciar texto, rodaje, inspiración, tradición y mito.</p></header><aside class="atlas-trust"><strong>Cómo verificamos:</strong> priorizamos fuentes oficiales y documentación primaria. Una asociación turística no se presenta como hecho literario si no está documentada.</aside><section class="atlas-filters" aria-label="Filtrar Atlas"><label>Buscar<input type="search" data-atlas-search placeholder="Libro, autor, ciudad o lugar"></label><label>Tipo<select data-atlas-category><option value="">Todo</option>{options}</select></label><p class="atlas-count" data-atlas-count role="status" aria-live="polite"></p></section><section class="atlas-grid">{cards}</section></main><script src="/assets/atlas-literario.js" defer></script></body></html>'''
    (out/'index.html').write_text(doc,encoding='utf-8')
    (out/'atlas-literario-public.json').write_text(json.dumps({'updated':data['updated'],'items':published},ensure_ascii=False,indent=2),encoding='utf-8')
    for item in published:
        slug = item['slug']
        if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
            raise ValueError(f'slug inválido: {slug!r}')
        detail_dir = out / slug
        detail_dir.mkdir(parents=True, exist_ok=True)
        title = html.escape(item['title'])
        summary = html.escape(item['summary'])
        category = html.escape(cats[item['category']])
        country = html.escape(item.get('country') or '')
        image = item.get('image') or {}
        image_src = html.escape(image.get('src') or '', quote=True)
        image_alt = html.escape(image.get('alt') or '', quote=True)
        sources = []
        for url in item.get('source_urls') or []:
            if not isinstance(url, str) or not url.startswith('https://'):
                raise ValueError(f'{slug}: fuente HTTPS inválida')
            safe_url = html.escape(url, quote=True)
            sources.append(f'<li><a href="{safe_url}" rel="noopener noreferrer">{safe_url}</a></li>')
        sources_html = ''.join(sources)
        detail = (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
                  f'<meta name="viewport" content="width=device-width,initial-scale=1">'
                  f'<title>{title} | Atlas literario</title>'
                  f'<link rel="canonical" href="https://davidportodiaz.com/atlas-literario/{slug}/">'
                  f'<link rel="stylesheet" href="/styles.css?v=202609-launch-1">'
                  f'<link rel="stylesheet" href="/assets/atlas-literario.css">'
                  f'</head><body><main class="atlas-page">'
                  f'<nav aria-label="Navegación"><a href="/atlas-literario/">Atlas literario</a></nav>'
                  f'<article><header><p>{category} · {country}</p><h1>{title}</h1></header>'
                  f'<img src="{image_src}" alt="{image_alt}" width="720" height="450">'
                  f'<p>{summary}</p><section aria-label="Fuentes documentales">'
                  f'<h2>Fuentes</h2><ul>{sources_html}</ul></section></article>'
                  f'</main></body></html>')
        (detail_dir / 'index.html').write_text(detail, encoding='utf-8')
    return len(published)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('data',type=Path)
    ap.add_argument('--out',type=Path,default=Path('dist/atlas-literario'))
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    data,cats=load(args.data)
    if args.check:
        print(f'OK: {len(data["items"])} ideas, {sum(i.get("status")=="published" for i in data["items"])} publicadas')
        return
    n=build(data,cats,args.out)
    print(f'Generado: {args.out} ({n} artículos publicados)')

if __name__=='__main__': main()
