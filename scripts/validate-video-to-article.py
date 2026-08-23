#!/usr/bin/env python3
from pathlib import Path
import sys

STATUS={'captured','triaged','review','hold','ready','published','discarded'}
PLAT={'instagram','tiktok','youtube','facebook','threads','x','other'}
DEST={'existing_page','cuaderno_article','source_for_future','discard'}
BASIS={'search_demand','reader_question','first_hand','catalog_gap','editorial_value'}

def empty(v):
    v=str(v or '').strip()
    return not v or v.lower() in {'n/a','na','none','null'} or '[[pendiente' in v.lower()

def parse(text):
    if not text.startswith('---\n'): raise ValueError('Falta front matter')
    end=text.find('\n---\n',4)
    if end<0: raise ValueError('Front matter sin cierre')
    m={}
    for line in text[4:end].splitlines():
        if ':' not in line: continue
        k,v=line.split(':',1);m[k.strip()]=v.strip().strip('"\'')
    return m,text[end+5:]

def section(body,title):
    key='# '+title; pos=body.find(key)
    if pos<0:return ''
    start=pos+len(key);end=body.find('\n# ',start)
    return body[start:end if end>=0 else None].strip()

def validate(path):
    text=Path(path).read_text(encoding='utf-8');errs=[]
    try:m,body=parse(text)
    except Exception as e:return [str(e)]
    st=m.get('status','');dest=m.get('destination','')
    if st not in STATUS:errs.append('status inválido')
    if dest not in DEST:errs.append('destination inválido')
    strict=st in {'triaged','review','hold','ready','published','discarded'}
    if strict:
        if m.get('platform') not in PLAT:errs.append('platform inválida')
        for k in ('original_url','published_at','selection_basis'):
            if empty(m.get(k)):errs.append(f'{k} obligatorio')
        bases={x.strip() for x in m.get('selection_basis','').split(',') if x.strip()}
        bad=bases-BASIS
        if bad:errs.append('selection_basis inválida: '+','.join(sorted(bad)))
        if str(m.get('own_content','')).lower() not in {'true','yes','sí','si'}:
            errs.append('contenido no confirmado como propio')
    if st in {'ready','published'}:
        if empty(m.get('transcript_source')):errs.append('transcript_source obligatorio')
        if dest=='cuaderno_article':
            if empty(m.get('first_hand_value')):errs.append('cuaderno_article sin first_hand_value')
            if empty(section(body,'Estructura propuesta')):errs.append('cuaderno_article sin estructura')
        if dest=='existing_page' and empty(m.get('existing_page')):
            errs.append('existing_page sin URL destino')
        has_sc=not empty(m.get('search_console_query')) or not empty(m.get('search_console_impressions')) or not empty(m.get('search_console_clicks'))
        if has_sc and empty(m.get('search_console_extracted_at')):
            errs.append('métricas Search Console sin fecha de extracción')
        if '[[pendiente' in text.lower():errs.append('ready/published con [[pendiente]]')
    if st=='published' and empty(m.get('published_url')):errs.append('published sin published_url')
    return errs

def main():
    failed=False
    for raw in sys.argv[1:]:
        e=validate(raw)
        if e:
            failed=True;print('FAIL',raw)
            for x in e:print('  -',x)
        else:print('PASS',raw)
    return 1 if failed else 0
if __name__=='__main__':raise SystemExit(main())
