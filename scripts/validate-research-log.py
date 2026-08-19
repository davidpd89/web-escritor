#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path

VALID = {'verified','inference','unconfirmed','discarded'}


def parse_meta(text):
    if not text.startswith('---\n'):
        raise ValueError('Falta front matter')
    raw, body = text[4:].split('\n---\n',1)
    meta={}
    for line in raw.splitlines():
        if ':' in line:
            k,v=line.split(':',1); meta[k.strip()]=v.strip().strip('"\'')
    return meta,body


def claims(body):
    pattern=re.compile(r'^###\s+(C\d+)\s+—\s+(.+?)\s*$([\s\S]*?)(?=^###\s+C\d+\s+—|^##\s+|\Z)',re.M)
    for m in pattern.finditer(body):
        fields={}
        for line in m.group(3).splitlines():
            if ':' in line:
                k,v=line.split(':',1); fields[k.strip()]=v.strip()
        yield m.group(1),m.group(2),fields


def emptyish(v):
    return not v or v.lower() in {'n/a','na','none','[[pendiente]]'} or '[[pendiente' in v.lower()


def validate(path):
    errors=[]
    text=path.read_text(encoding='utf-8')
    try: meta,body=parse_meta(text)
    except Exception as exc: return [str(exc)]
    status=meta.get('status','')
    if status not in {'draft','review','published','archived'}: errors.append('status inválido')
    body_no_comments = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    found=list(claims(body_no_comments))
    if status=='published' and not found: errors.append('Publicado sin afirmaciones registradas')
    for cid,title,f in found:
        st=f.get('status','')
        if st not in VALID: errors.append(f'{cid}: estado inválido {st!r}'); continue
        source=f.get('source','')
        basis=f.get('basis','')
        attempts=f.get('attempts','')
        checked=f.get('checked','')
        strict = status in {'review','published'}
        if strict and st=='verified' and emptyish(source): errors.append(f'{cid}: verified sin source')
        if strict and st=='inference' and emptyish(source) and emptyish(basis): errors.append(f'{cid}: inference sin fuentes base')
        if strict and st=='unconfirmed' and emptyish(attempts): errors.append(f'{cid}: unconfirmed sin attempts')
        if status=='published' and emptyish(checked): errors.append(f'{cid}: publicado sin checked')
    if status=='published':
        for key in ('research_id','topic','last_verified'):
            if emptyish(meta.get(key,'')): errors.append(f'Publicado sin {key}')
        if '[[pendiente' in text.lower(): errors.append('Publicado con [[pendiente]]')
    return errors


def main():
    if len(sys.argv)<2:
        print('Uso: validate-research-log.py <log.md> [...]',file=sys.stderr); return 2
    failed=False
    for raw in sys.argv[1:]:
        p=Path(raw); errs=validate(p)
        if errs:
            failed=True; print('FAIL',p)
            for e in errs: print('  -',e)
        else: print('PASS',p)
    return 1 if failed else 0

if __name__=='__main__': raise SystemExit(main())
