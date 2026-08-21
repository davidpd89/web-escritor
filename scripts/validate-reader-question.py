#!/usr/bin/env python3
from pathlib import Path
import re, sys

ALLOWED_STATUS={'captured','triaged','hold','ready','published','discarded'}
SOURCES={'email','instagram','tiktok','threads','facebook','evento','club_lectura','libreria','prensa','conversacion_directa','otro'}
DEST={'existing_page','short_answer_block','cuaderno_article','hold','discard'}
ATTR={'anonymous','permission_granted','public_handle'}

def empty(v):
    v=str(v or '').strip()
    return not v or v.lower() in {'n/a','na','none','null'} or '[[pendiente' in v.lower()

def meta(text):
    if not text.startswith('---\n'): raise ValueError('Falta front matter')
    end=text.find('\n---\n',4)
    if end<0: raise ValueError('Front matter sin cierre')
    raw=text[4:end]
    out={}
    for line in raw.splitlines():
        if ':' not in line: continue
        k,v=line.split(':',1); out[k.strip()]=v.strip().strip('"\'')
    return out, text[end+5:]

def validate(path):
    text=Path(path).read_text(encoding='utf-8')
    errors=[]
    try: m,body=meta(text)
    except Exception as e: return [str(e)]
    st=m.get('status','')
    if st not in ALLOWED_STATUS: errors.append('status inválido')
    dest=m.get('destination','')
    if dest not in DEST: errors.append('destination inválido')
    attr=m.get('attribution','')
    if attr not in ATTR: errors.append('attribution inválido')
    strict=st in {'triaged','hold','ready','published','discarded'}
    if strict:
        sk=m.get('source_kind','')
        if sk not in SOURCES: errors.append('source_kind real obligatorio')
        if empty(m.get('source_ref')): errors.append('source_ref obligatorio')
        if empty(m.get('captured_at')): errors.append('captured_at obligatorio')
    # "existing_page sin already_answered_url" ya es un error desde triaged,
    # no solo desde ready/published: el propio paso de triage consiste en
    # comprobar duplicidad y destino (doc 53 seccion 9), asi que decidir
    # destination=existing_page sin anotar TODAVIA la URL existente es
    # precisamente el fallo que el triage deberia haber evitado. El caso 5 de
    # QA del documento lo prueba explicitamente en estado triaged, no solo en
    # ready/published.
    if st in {'triaged','ready','published'}:
        if dest=='existing_page' and empty(m.get('already_answered_url')):
            errors.append('existing_page sin already_answered_url')
    if st in {'ready','published'}:
        if empty(m.get('question_id')): errors.append('question_id obligatorio')
        if empty(m.get('book_or_topic')): errors.append('book_or_topic obligatorio')
        if attr in {'permission_granted','public_handle'} and empty(m.get('permission_ref')):
            errors.append('atribución pública sin permission_ref')
        if dest=='cuaderno_article' and empty(m.get('first_hand_value')):
            errors.append('cuaderno_article sin first_hand_value')
        if '[[pendiente' in text.lower(): errors.append('ready/published con [[pendiente]]')
    if st=='published' and empty(m.get('published_url')):
        errors.append('published sin published_url')
    return errors

def main():
    if len(sys.argv)<2:
        print('Uso: validate-reader-question.py <archivo.md> [...]',file=sys.stderr); return 2
    failed=False
    for raw in sys.argv[1:]:
        errs=validate(raw)
        if errs:
            failed=True; print('FAIL',raw)
            for e in errs: print('  -',e)
        else: print('PASS',raw)
    return 1 if failed else 0

if __name__=='__main__': raise SystemExit(main())
