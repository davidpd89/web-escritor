#!/usr/bin/env python3
import argparse, html, json, re
from pathlib import Path

SLUG_RE=re.compile(r'^[a-z0-9-]+$')
ALLOWED_REL={'book-setting','filming-location','inspiration','writer-route','library','bookshop','book-town','fact-check','mixed','library-list'}


def load(path:Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    cats={c['slug']:c['name'] for c in data.get('categories',[])}
    if not cats: raise ValueError('Sin categorías')
    seen=set()
    for item in data.get('items',[]):
        slug=item.get('slug','')
        if not SLUG_RE.fullmatch(slug): raise ValueError(f'slug inválido: {slug!r}')
        if slug in seen: raise ValueError(f'slug duplicado: {slug}')
        seen.add(slug)
        if item.get('category') not in cats: raise ValueError(f'categoría inválida en {slug}')
        if item.get('relationship') not in ALLOWED_REL: raise ValueError(f'relationship inválida en {slug}')
        urls=item.get('source_urls') or []
        if not urls or any(not u.startswith('https://') for u in urls): raise ValueError(f'{slug}: requiere fuente HTTPS')
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
    return f'''<article class="atlas-card" data-atlas-card data-category="{item['category']}" data-search="{search}"><img src="{src}" alt="{alt}" width="720" height="450" loading="lazy" decoding="async"><div class="atlas-card__body"><p class="atlas-card__meta"><span>{cat}</span><span>{country}</span></p><h2><a href="/atlas-literario/{item['slug']}/">{title}</a></h2><p>{summ}</p><a href="/atlas-literario/{item['slug']}/">Explorar →</a></div></article>'''


def build(data,cats,out:Path):
    published=[x for x in data['items'] if x.get('status')=='published']
    out.mkdir(parents=True,exist_ok=True)
    options=''.join(f'<option value="{html.escape(slug)}">{html.escape(name)}</option>' for slug,name in cats.items())
    cards=''.join(card(x,cats) for x in published) or '<p>Aún no hay artículos publicados en este dataset de ejemplo.</p>'
    doc=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas literario | David Porto Díaz</title><meta name="description" content="Lugares de libros, bibliotecas extraordinarias, rutas literarias y huellas de escritores, investigados con fuentes y sin mezclar hechos con mitos."><link rel="canonical" href="https://davidportodiaz.com/atlas-literario/"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/assets/atlas-literario.css"></head><body><main class="atlas-page" data-atlas-index><header class="atlas-hero"><p class="eyebrow">Atlas literario</p><h1>El mundo de los libros también existe fuera de las páginas.</h1><p class="lead">Lugares reales, bibliotecas, librerías y rutas investigadas con una regla: diferenciar texto, rodaje, inspiración, tradición y mito.</p></header><aside class="atlas-trust"><strong>Cómo verificamos:</strong> priorizamos fuentes oficiales y documentación primaria. Una asociación turística no se presenta como hecho literario si no está documentada.</aside><section class="atlas-filters" aria-label="Filtrar Atlas"><label>Buscar<input type="search" data-atlas-search placeholder="Libro, autor, ciudad o lugar"></label><label>Tipo<select data-atlas-category><option value="">Todo</option>{options}</select></label><p class="atlas-count" data-atlas-count></p></section><section class="atlas-grid">{cards}</section></main><script src="/assets/atlas-literario.js" defer></script></body></html>'''
    (out/'index.html').write_text(doc,encoding='utf-8')
    (out/'atlas-literario-public.json').write_text(json.dumps({'updated':data['updated'],'items':published},ensure_ascii=False,indent=2),encoding='utf-8')
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
