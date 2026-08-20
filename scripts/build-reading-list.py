#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_STATUS = {'reading','finished','paused'}
ALLOWED_LINK = {'official','author','publisher','affiliate','none'}

def fail(msg): raise ValueError(msg)

def valid_date(value, field, today):
    if value is None: return None
    try: d=date.fromisoformat(value)
    except Exception: fail(f'{field}: fecha inválida {value!r}')
    if d > today: fail(f'{field}: fecha futura {value}')
    return d

def validate(data, today):
    if not isinstance(data, dict) or not isinstance(data.get('items'), list): fail('items debe ser una lista')
    seen=set(); out=[]
    disclosure=(data.get('affiliate_disclosure') or '').strip()
    for raw in data['items']:
        if not isinstance(raw, dict): fail('cada item debe ser objeto')
        if not raw.get('publish'): continue
        ident=(raw.get('id') or '').strip()
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{2,80}', ident): fail(f'id inválido: {ident!r}')
        if ident in seen: fail(f'id duplicado: {ident}')
        seen.add(ident)
        title=(raw.get('title') or '').strip(); author=(raw.get('author') or '').strip(); note=(raw.get('note') or '').strip()
        if not title or not author: fail(f'{ident}: faltan title/author')
        if len(note) < 70: fail(f'{ident}: nota demasiado breve; debe aportar experiencia propia')
        if len(note) > 700: fail(f'{ident}: nota demasiado larga para este formato')
        status=raw.get('status')
        if status not in ALLOWED_STATUS: fail(f'{ident}: status inválido')
        started=valid_date(raw.get('started_on'), f'{ident}.started_on', today)
        finished=valid_date(raw.get('finished_on'), f'{ident}.finished_on', today)
        if status=='finished' and not finished: fail(f'{ident}: finished requiere finished_on')
        if finished and started and finished < started: fail(f'{ident}: finished_on anterior a started_on')
        kind=raw.get('link_kind','none'); url=raw.get('url')
        if kind not in ALLOWED_LINK: fail(f'{ident}: link_kind inválido')
        if kind=='none' and url: fail(f'{ident}: link_kind none no admite URL')
        if kind!='none':
            if not url: fail(f'{ident}: falta URL')
            p=urlparse(url)
            if p.scheme!='https' or not p.netloc: fail(f'{ident}: URL debe ser HTTPS')
        if kind=='affiliate' and len(disclosure) < 30: fail('Hay afiliación pero falta disclosure suficiente')
        verified=valid_date(raw.get('verified_on'), f'{ident}.verified_on', today)
        if kind!='none' and not verified: fail(f'{ident}: enlace sin verified_on')
        out.append({**raw, 'title':title,'author':author,'note':note})
    if not out: fail('No hay items publish=true')
    if sum(1 for x in out if x['status']=='reading') > 5: fail('Máximo 5 lecturas actuales')
    return out, disclosure

def link_html(item):
    if item['link_kind']=='none': return ''
    rel='noopener noreferrer'
    suffix=''
    if item['link_kind']=='affiliate':
        rel='sponsored noopener noreferrer'; suffix=' <span class="reading-affiliate">· afiliado</span>'
    label={'official':'Ficha oficial','author':'Web del autor','publisher':'Editorial','affiliate':'Ver libro'}[item['link_kind']]
    return f'<p class="reading-link"><a href="{html.escape(item["url"], quote=True)}" rel="{rel}" target="_blank">{label}</a>{suffix}</p>'

def card(item):
    when=''
    if item.get('finished_on'): when=f'<time datetime="{item["finished_on"]}">{item["finished_on"]}</time>'
    elif item.get('started_on'): when=f'Desde <time datetime="{item["started_on"]}">{item["started_on"]}</time>'
    return f'''<article class="reading-card">
  <p class="reading-meta">{when}</p>
  <h3>{html.escape(item['title'])}</h3>
  <p class="reading-author">{html.escape(item['author'])}</p>
  <p>{html.escape(item['note'])}</p>
  {link_html(item)}
</article>'''

def render(items, disclosure, updated):
    groups=[('reading','Leyendo ahora'),('finished','Lecturas recientes'),('paused','En pausa')]
    sections=[]
    for key,label in groups:
        subset=[x for x in items if x['status']==key]
        if not subset: continue
        if key=='finished': subset.sort(key=lambda x:x.get('finished_on') or '', reverse=True)
        sections.append(f'<section class="reading-group"><h2>{label}</h2><div class="reading-grid">'+''.join(card(x) for x in subset)+'</div></section>')
    has_aff=any(x['link_kind']=='affiliate' for x in items)
    disclosure_html=f'<p class="reading-disclosure">{html.escape(disclosure)}</p>' if has_aff else ''
    itemlist=','.join(json.dumps({'@type':'ListItem','position':i+1,'name':x['title']}, ensure_ascii=False) for i,x in enumerate(items))
    schema=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':'Qué estoy leyendo | David Porto Díaz','url':'https://davidportodiaz.com/lecturas/','inLanguage':'es','mainEntity':{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'name':x['title']} for i,x in enumerate(items)]}}, ensure_ascii=False).replace('</','<\/')
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow,max-image-preview:large"><title>Qué estoy leyendo | David Porto Díaz</title><meta name="description" content="Lecturas actuales y recientes de David Porto Díaz, con notas personales breves sobre lo que le está llamando la atención de cada libro."><link rel="canonical" href="https://davidportodiaz.com/lecturas/"><link rel="stylesheet" href="/styles.css?v=202609-launch-1"><link rel="stylesheet" href="/assets/reading-list.css"><script type="application/ld+json">{schema}</script></head>
<body><main id="main-content" class="reading-page"><header class="reading-hero"><p class="eyebrow">Cuaderno de lector</p><h1>Qué estoy leyendo.</h1><p>No es un ranking ni una lista de compras. Son lecturas actuales y recientes con una nota sobre lo que me está llamando la atención.</p><p class="reading-updated">Actualizado: <time datetime="{updated}">{updated}</time></p></header>{''.join(sections)}{disclosure_html}</main></body></html>'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('json_file',type=Path); ap.add_argument('--output',required=True,type=Path); ap.add_argument('--check',action='store_true'); ap.add_argument('--today',default=date.today().isoformat())
    a=ap.parse_args(); today=date.fromisoformat(a.today); data=json.loads(a.json_file.read_text(encoding='utf-8')); items,disclosure=validate(data,today); updated=data.get('updated_on') or a.today; valid_date(updated,'updated_on',today); out=render(items,disclosure,updated)
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding='utf-8')!=out: print('FAIL: salida desactualizada',file=sys.stderr); return 1
        print(f'PASS: {len(items)} lecturas publicables'); return 0
    a.output.write_text(out,encoding='utf-8'); print(f'GENERATED: {len(items)} lecturas'); return 0
if __name__=='__main__': raise SystemExit(main())
