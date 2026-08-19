#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ALLOWED={'decision','audit','experiment','observation'}
FRONT=re.compile(r'^---\n(.*?)\n---\n',re.S)

def parse_front(text):
    m=FRONT.match(text)
    if not m: raise ValueError('falta front matter')
    d={}
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith('#'): continue
        if ':' not in line: raise ValueError(f'línea front matter inválida: {line}')
        k,v=line.split(':',1); v=v.strip()
        if ' #' in v: v=v.split(' #',1)[0].strip()
        if v in {'true','false'}: val=v=='true'
        elif v in {'null',''}: val=None
        else: val=v
        d[k.strip()]=val
    return d,m.end()

def section(text, title):
    m=re.search(rf'^# {re.escape(title)}\s*$\n(.*?)(?=^# |\Z)',text,re.M|re.S)
    return m.group(1).strip() if m else ''

def unresolved(s): return not s or '[[pendiente]]' in s

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('file',type=Path); ap.add_argument('--today',default=date.today().isoformat()); a=ap.parse_args()
    text=a.file.read_text(encoding='utf-8'); meta,start=parse_front(text); body=text[start:]
    if meta.get('status')=='draft' and not meta.get('publish'):
        print('PASS: borrador no publicable'); return 0
    typ=meta.get('entry_type')
    if typ not in ALLOWED: raise ValueError('entry_type inválido')
    if meta.get('publish') is not True: raise ValueError('review/published requiere publish:true')
    slug=str(meta.get('slug') or '');
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{3,90}',slug): raise ValueError('slug inválido')
    for field in ('title','question','started_on','public_url','measurement_source'):
        if unresolved(str(meta.get(field) or '')): raise ValueError(f'falta {field}')
    try: start_date=date.fromisoformat(str(meta['started_on']))
    except: raise ValueError('started_on inválida')
    today=date.fromisoformat(a.today)
    if start_date>today: raise ValueError('started_on futura')
    if meta.get('ended_on'):
        end=date.fromisoformat(str(meta['ended_on']))
        if end<start_date or end>today: raise ValueError('ended_on incoherente')
    p=urlparse(str(meta['public_url']))
    if p.scheme!='https' or p.netloc not in {'davidportodiaz.com','www.davidportodiaz.com'}: raise ValueError('public_url debe ser canónica propia HTTPS')
    required=['Problema real','Situación inicial / baseline','Qué cambié o comprobé','Cómo lo medí','Resultado observable','Lo que NO puedo concluir','Qué haría diferente','Reproducibilidad / recursos']
    for name in required:
        s=section(body,name)
        if unresolved(s) or len(s)<60: raise ValueError(f'sección insuficiente: {name}')
    if meta.get('contains_private_metrics') is True: raise ValueError('no publicar con contains_private_metrics:true')
    if typ=='experiment' and meta.get('has_control_group') is not True:
        raise ValueError('entry_type=experiment requiere has_control_group:true; usa observation/decision si no hay control')
    banned=('api key','apikey','password','contraseña','token secreto','authorization: bearer')
    low=text.lower()
    if any(x in low for x in banned): raise ValueError('posible secreto/credencial en el texto')
    print(f'PASS: {typ} publicable')
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except ValueError as e: print(f'FAIL: {e}',file=sys.stderr); raise SystemExit(1)
