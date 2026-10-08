#!/usr/bin/env python3
"""Sitewide public-document and form-accessibility contract."""
from __future__ import annotations
import re, sys, xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
EXTRA_PUBLIC_HTML=("404.html","offline.html","privacidad.html","aviso-legal.html")

def route_to_file(url:str)->Path:
    path=urlparse(url).path
    if path in {"","/"}: return ROOT/"index.html"
    rel=path.lstrip("/")
    if path.endswith("/"): rel+="index.html"
    return ROOT/rel

@dataclass
class Control:
    tag:str; line:int; attrs:dict[str,str]; wrapped_label:bool; text:str=""

class Parser(HTMLParser):
    def __init__(self,rel:str)->None:
        super().__init__(convert_charrefs=True)
        self.rel=rel; self.errors=[]; self.doctype_count=0; self.html_count=0
        self.head_count=0; self.body_count=0; self.main_count=0
        self.lang_values=[]; self.charsets=[]; self.viewports=[]
        self.label_for=set(); self.element_ids=set(); self.stack=[]; self.controls=[]
    @staticmethod
    def attrs_dict(attrs): return {str(k).lower():"" if v is None else str(v) for k,v in attrs}
    def handle_decl(self,decl):
        if decl.strip().lower()=="doctype html": self.doctype_count+=1
    def handle_starttag(self,tag,attrs): self._start(tag,attrs,False)
    def handle_startendtag(self,tag,attrs): self._start(tag,attrs,True)
    def _start(self,tag,attrs,self_closing):
        t=tag.lower(); a=self.attrs_dict(attrs); line=self.getpos()[0]
        identifier=a.get("id","").strip()
        if identifier: self.element_ids.add(identifier)
        if t=="html": self.html_count+=1; self.lang_values.append(a.get("lang","").strip())
        elif t=="head": self.head_count+=1
        elif t=="body": self.body_count+=1
        elif t=="main": self.main_count+=1
        elif t=="meta":
            if "charset" in a: self.charsets.append(a["charset"].strip().lower())
            if a.get("name","").strip().lower()=="viewport": self.viewports.append(a.get("content","").strip().lower())
        if t=="label" and a.get("for"): self.label_for.add(a["for"].strip())
        wrapped=any(x["tag"]=="label" for x in self.stack)
        if t in {"input","select","textarea","button"}:
            input_type=a.get("type","text").lower() if t=="input" else ""
            if not (t=="input" and input_type=="hidden"):
                self.controls.append(Control(t,line,a,wrapped))
                if not self_closing and t!="input":
                    a=dict(a); a["__control_index"]=str(len(self.controls)-1)
        if not self_closing and t not in {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}:
            self.stack.append({"tag":t,"attrs":a,"text":[]})
    def handle_data(self,data):
        for item in self.stack: item["text"].append(data)
    def handle_endtag(self,tag):
        t=tag.lower()
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]["tag"]==t:
                closing=self.stack[i]; del self.stack[i:]
                idx=closing["attrs"].get("__control_index")
                if idx is not None: self.controls[int(idx)].text=" ".join("".join(closing["text"]).split())
                break
    def finish(self):
        if self.doctype_count!=1: self.errors.append(f"{self.rel}: expected one <!doctype html>, got {self.doctype_count}")
        if self.html_count!=1: self.errors.append(f"{self.rel}: expected one <html>, got {self.html_count}")
        if not self.lang_values or not self.lang_values[0].lower().startswith("es"): self.errors.append(f"{self.rel}: non-Spanish/missing lang {self.lang_values!r}")
        if self.head_count!=1: self.errors.append(f"{self.rel}: expected one <head>, got {self.head_count}")
        if self.body_count!=1: self.errors.append(f"{self.rel}: expected one <body>, got {self.body_count}")
        if self.main_count!=1: self.errors.append(f"{self.rel}: expected one <main>, got {self.main_count}")
        if len(self.charsets)!=1 or self.charsets[0] not in {"utf-8","utf8"}: self.errors.append(f"{self.rel}: expected one UTF-8 charset, got {self.charsets!r}")
        if len(self.viewports)!=1: self.errors.append(f"{self.rel}: expected one viewport meta, got {len(self.viewports)}")
        elif not re.search(r"(?:^|,)\s*width\s*=\s*device-width\s*(?:,|$)",self.viewports[0]): self.errors.append(f"{self.rel}: viewport lacks width=device-width")
        for c in self.controls:
            a=c.attrs; cid=a.get("id","").strip()
            refs=a.get("aria-labelledby","").split()
            missing=sorted({ref for ref in refs if ref not in self.element_ids})
            if missing:
                self.errors.append(f"{self.rel}:{c.line}: <{c.tag}> aria-labelledby references missing IDs: {', '.join(missing)}")
            labelled=bool(c.wrapped_label or (cid and cid in self.label_for) or a.get("aria-label","").strip() or (refs and not missing))
            if c.tag=="button": labelled=bool(labelled or c.text or a.get("title","").strip())
            elif c.tag=="input" and a.get("type","text").lower() in {"submit","reset","button"}: labelled=bool(labelled or a.get("value","").strip() or a.get("title","").strip())
            else: labelled=bool(labelled or a.get("title","").strip())
            if not labelled:
                ph=a.get("placeholder","").strip()
                suffix=f" (placeholder={ph!r} is not an accessible name)" if ph else ""
                self.errors.append(f"{self.rel}:{c.line}: <{c.tag}> has no accessible name{suffix}")
        return self.errors

def public_html_files():
    root=ET.parse(ROOT/"sitemap.xml").getroot(); ns={"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls=[n.text.strip() for n in root.findall(".//sm:loc",ns) if n.text and n.text.strip()]
    files=[]; seen=set()
    for url in urls:
        p=route_to_file(url)
        if p.suffix.lower()==".html" and p.is_file() and p not in seen: seen.add(p); files.append(p)
    for rel in EXTRA_PUBLIC_HTML:
        p=ROOT/rel
        if p.is_file() and p not in seen: seen.add(p); files.append(p)
    return sorted(files)

def main():
    errors=[]; files=public_html_files()
    for path in files:
        rel=path.relative_to(ROOT).as_posix(); p=Parser(rel)
        try: p.feed(path.read_text(encoding="utf-8")); p.close()
        except Exception as exc: errors.append(f"{rel}: parse failure: {exc}"); continue
        errors.extend(p.finish())
    if errors:
        print(f"FAIL public document/form contract: {len(errors)} issue(s) across {len(files)} files")
        for e in errors: print("-",e)
        return 1
    print(f"PASS public document/form contract: {len(files)} public HTML files")
    return 0

if __name__=="__main__": raise SystemExit(main())
