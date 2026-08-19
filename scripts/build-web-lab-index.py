#!/usr/bin/env python3
from __future__ import annotations
import argparse,html,json,re,sys
from datetime import date
from pathlib import Path

ALLOWED={'decision':'Decisión','audit':'Auditoría','experiment':'Experimento','observation':'Observación'}

def validate(d,today):
    if not isinstance(d,dict) or not isinstance(d.get('entries'),list): raise ValueError('entries debe ser lista')
    seen=set(); out=[]
    for x in d['entries']:
        if not x.get('publish'): continue
        slug=str(x.get('slug') or '')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{3,90}',slug): raise ValueError(f'slug inválido {slug!r}')
        if slug in seen: raise ValueError(f'slug duplicado: {slug}')
        seen.add(slug)
        typ=x.get('entry_type')
        if typ not in ALLOWED: raise ValueError(f'{slug}: tipo inválido')
        for f in ('title','summary','date','url'):
            if not str(x.get(f) or '').strip(): raise ValueError(f'{slug}: falta {f}')
        if len(x['summary'].strip())<80: raise ValueError(f'{slug}: summary demasiado breve')
        dd=date.fromisoformat(x['date'])
        if dd>today: raise ValueError(f'{slug}: fecha futura')
        if x['url'] != f'/cuaderno/{slug}/': raise ValueError(f'{slug}: URL debe ser /cuaderno/<slug>/')
        out.append(x)
    if len(out)<2: raise ValueError('el hub requiere al menos 2 piezas publicables')
    return sorted(out,key=lambda x:x['date'],reverse=True)

def render(items,updated):
    cards=''.join(f'''<article class="lab-card"><p class="lab-type">{ALLOWED[x['entry_type']]} · <time datetime="{x['date']}">{x['date']}</time></p><h2><a href="{html.escape(x['url'],quote=True)}">{html.escape(x['title'])}</a></h2><p>{html.escape(x['summary'])}</p></article>''' for x in items)
    schema=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','name':'Laboratorio de una web de escritor','url':'https://davidportodiaz.com/cuaderno/laboratorio-web/','inLanguage':'es','mainEntity':{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':'https://davidportodiaz.com'+x['url'],'name':x['title']} for i,x in enumerate(items)]}},ensure_ascii=False).replace('</','<\\/')
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow,max-image-preview:large"><title>Laboratorio de una web de escritor | David Porto Díaz</title><meta name="description" content="Decisiones, auditorías y experimentos reales al construir davidportodiaz.com, explicados con método, resultados y límites para que otros autores puedan reutilizar lo aprendido."><link rel="canonical" href="https://davidportodiaz.com/cuaderno/laboratorio-web/"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/assets/web-lab.css"><script type="application/ld+json">{schema}</script></head><body><main class="lab-page"><header class="lab-hero"><p class="eyebrow">Laboratorio de la web</p><h1>Construir una web de escritor también deja datos.</h1><p>Aquí documento decisiones y pruebas realizadas en esta propia web. Una observación de un solo sitio no se presenta como ley general.</p><p>Actualizado: <time datetime="{updated}">{updated}</time></p></header><section class="lab-grid" aria-label="Casos publicados">{cards}</section></main></body></html>'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('json_file',type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--check',action='store_true');ap.add_argument('--today',default=date.today().isoformat());a=ap.parse_args();today=date.fromisoformat(a.today);d=json.loads(a.json_file.read_text(encoding='utf-8'));items=validate(d,today);updated=d.get('updated_on') or a.today;date.fromisoformat(updated);out=render(items,updated)
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding='utf-8')!=out: print('FAIL: salida desactualizada',file=sys.stderr);return 1
        print(f'PASS: {len(items)} entradas');return 0
    a.output.write_text(out,encoding='utf-8');print(f'GENERATED: {len(items)} entradas');return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except ValueError as e: print(f'FAIL: {e}',file=sys.stderr);raise SystemExit(1)
