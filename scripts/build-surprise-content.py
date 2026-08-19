#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from datetime import datetime
from pathlib import Path

ALLOWED_TYPES={"lectura","cronica","articulo","proceso","recomendacion","herramienta","recurso","curiosidad"}
ALLOWED_AUDIENCES={"reader","writer","all"}
ALLOWED_STATUS={"ready","candidate","disabled"}
BLOCKED=("/privacidad", "/aviso-legal", "/gracias", "/press-kit/", "/libros/")

def validate(data):
    if data.get("schema_version") != 1: raise ValueError("schema_version debe ser 1")
    items=data.get("items")
    if not isinstance(items,list) or len(items)<5: raise ValueError("se requieren al menos 5 candidatos")
    seen=set(); ready=[]
    for i,item in enumerate(items,1):
        url=item.get("url","")
        if not isinstance(url,str) or not url.startswith("/") or not url.endswith("/") or "?" in url or "#" in url:
            raise ValueError(f"item {i}: URL interna limpia obligatoria")
        if url in seen: raise ValueError(f"item {i}: URL duplicada {url}")
        seen.add(url)
        if any(url.startswith(prefix) for prefix in BLOCKED): raise ValueError(f"item {i}: ruta bloqueada {url}")
        if item.get("type") not in ALLOWED_TYPES: raise ValueError(f"item {i}: type inválido")
        audiences=item.get("audiences")
        if not isinstance(audiences,list) or not audiences or any(a not in ALLOWED_AUDIENCES for a in audiences):
            raise ValueError(f"item {i}: audiences inválidas")
        if item.get("commercial") is not False: raise ValueError(f"item {i}: commercial debe ser false")
        if item.get("status") not in ALLOWED_STATUS: raise ValueError(f"item {i}: status inválido")
        if not item.get("title") or len(item["title"])>120: raise ValueError(f"item {i}: title inválido")
        try: datetime.strptime(item.get("reviewed_at",""),"%Y-%m-%d")
        except Exception: raise ValueError(f"item {i}: reviewed_at inválido")
        if item["status"]=="ready": ready.append(item)
    if len(ready)<5: raise ValueError("se requieren al menos 5 elementos ready")
    if len({x["type"] for x in ready})<3: raise ValueError("el pool ready debe mezclar al menos 3 tipos")
    return ready

def local_file(root:Path,url:str)->Path:
    rel=url.strip("/")
    if not rel: return root/"index.html"
    return root/rel/"index.html"

def check_repo(root:Path,ready):
    problems=[]
    for item in ready:
        p=local_file(root,item["url"])
        if not p.exists(): problems.append(f"ausente: {item['url']}"); continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',text,re.I):
            problems.append(f"noindex: {item['url']}")
        expected='https://davidportodiaz.com'+item['url']
        if expected not in text: problems.append(f"canonical no confirmado: {item['url']}")
    if problems: raise ValueError("; ".join(problems))

def render(ready):
    public=[{"url":x["url"],"title":x["title"],"type":x["type"],"audiences":x["audiences"]} for x in ready]
    return "window.DP_SURPRISE_CONTENT = Object.freeze("+json.dumps(public,ensure_ascii=False,separators=(",",":"))+ ");\n"

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("data",type=Path); ap.add_argument("output",type=Path); ap.add_argument("--root",type=Path); ap.add_argument("--check",action="store_true")
    a=ap.parse_args(); data=json.loads(a.data.read_text(encoding="utf-8")); ready=validate(data)
    if a.root: check_repo(a.root,ready)
    out=render(ready)
    if a.check:
        if not a.output.exists() or a.output.read_text(encoding="utf-8")!=out:
            print("OUTDATED",file=sys.stderr); return 2
        print(f"PASS: {len(ready)} destinos listos"); return 0
    a.output.write_text(out,encoding="utf-8"); print(f"GENERATED: {len(ready)} destinos"); return 0
if __name__=="__main__": raise SystemExit(main())
