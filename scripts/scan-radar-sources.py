#!/usr/bin/env python3
"""Descubre enlaces/cambios candidatos en una lista blanca de fuentes oficiales.

NO publica oportunidades. Genera una cola JSON para revisión humana.
Python estándar; sin scraping de redes sociales ni bypass de bloqueos.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

UA = "DavidPortoRadar/1.0 (+https://davidportodiaz.com/metodologia-editorial/)"

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]; self._href=None; self._text=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            self._href=dict(attrs).get("href"); self._text=[]
    def handle_data(self, data):
        if self._href is not None: self._text.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=="a" and self._href is not None:
            text=re.sub(r"\s+"," ","".join(self._text)).strip()
            if text and self._href: self.links.append((text,self._href))
            self._href=None; self._text=[]

def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def dump(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def fingerprint(text,url): return hashlib.sha256(f"{text}|{url}".encode()).hexdigest()[:20]

def fetch(url, timeout=20):
    if url.startswith("file://"):
        return Path(url[7:]).read_text(encoding="utf-8")
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
    with urlopen(req,timeout=timeout) as r:
        ctype=r.headers.get_content_charset() or "utf-8"
        return r.read(2_000_000).decode(ctype,errors="replace")

def discover(source, html):
    p=LinkParser(); p.feed(html)
    kws=[k.casefold() for k in source.get("keywords",[]) if k.strip()]
    out=[]
    for text,href in p.links:
        hay=text.casefold()
        if kws and not any(k in hay for k in kws): continue
        url=urljoin(source["url"],href)
        if urlparse(url).scheme not in {"http","https","file"}: continue
        out.append({"title":text[:240],"url":url,"fingerprint":fingerprint(text,url)})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sources",required=True)
    ap.add_argument("--known",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--fail-on-new",action="store_true")
    args=ap.parse_args()
    config=load(args.sources)
    known_path=Path(args.known)
    known=set(load(known_path).get("fingerprints",[])) if known_path.exists() else set()
    now=datetime.now(timezone.utc).isoformat()
    candidates=[]; errors=[]; seen=set(known)
    for src in config.get("sources",[]):
        if not src.get("enabled",True): continue
        if not src.get("official",False):
            errors.append({"source":src.get("id"),"error":"source_not_official"}); continue
        try:
            html=fetch(src["url"])
            for item in discover(src,html):
                seen.add(item["fingerprint"])
                if item["fingerprint"] in known: continue
                candidates.append({"source_id":src["id"],"source_name":src["name"],"discovered_at":now,**item})
        except Exception as exc:
            errors.append({"source":src.get("id"),"error":str(exc)[:300]})
    dump(args.out,{"generated_at":now,"candidates":candidates,"errors":errors})
    dump(args.known,{"fingerprints":sorted(seen)})
    print(f"candidates={len(candidates)} errors={len(errors)}")
    if args.fail_on_new and candidates: return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
