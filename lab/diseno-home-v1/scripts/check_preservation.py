#!/usr/bin/env python3
"""Preservation gate for future staging/production candidates. Standard library only.

Usage:
  python scripts/check_preservation.py --home path/to/index.html \
      --manecillas path/to/las-manecillas-del-recuerdo/index.html \
      --jaula path/to/donde-empieza-la-jaula/index.html

Home/Manecillas compare against public baselines. Jaula has no public baseline yet: its gate
verifies the authorized factual copy, exact Chapter 1 payload and staging-only restrictions.
"""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

class HeadAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.meta = []
        self.links = []
        self.scripts_jsonld = []
        self._jsonld = None
        self.ids = []
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if "id" in d: self.ids.append(d["id"])
        if tag=="title": self._in_title=True
        elif tag=="meta": self.meta.append(d)
        elif tag=="link": self.links.append(d)
        elif tag=="script" and d.get("type")=="application/ld+json": self._jsonld=[]
    def handle_endtag(self, tag):
        if tag=="title": self._in_title=False
        elif tag=="script" and self._jsonld is not None:
            self.scripts_jsonld.append("".join(self._jsonld)); self._jsonld=None
    def handle_data(self, data):
        if self._in_title: self.title += data
        if self._jsonld is not None: self._jsonld.append(data)

class JaulaAudit(HTMLParser):
    """Collect the exact visible text payload from Jaula without depending on CSS."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1_text=[]; self._in_h1=False
        self.excerpt_depth=0; self._in_p=False; self._p=[]; self.paragraphs=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=="h1": self._in_h1=True
        if tag=="div" and self.excerpt_depth==0 and "excerpt-field" in (d.get("class") or "").split():
            self.excerpt_depth=1
            return
        if self.excerpt_depth:
            if tag=="div": self.excerpt_depth += 1
            if tag=="p": self._in_p=True; self._p=[]
    def handle_endtag(self, tag):
        if tag=="h1": self._in_h1=False
        if self.excerpt_depth:
            if tag=="p" and self._in_p:
                self.paragraphs.append(" ".join("".join(self._p).split()))
                self._in_p=False
            if tag=="div": self.excerpt_depth -= 1
    def handle_data(self, data):
        if self._in_h1: self.h1_text.append(data)
        if self.excerpt_depth and self._in_p: self._p.append(data)

def parse(path: Path) -> tuple[HeadAudit,str]:
    text=path.read_text(encoding="utf-8")
    p=HeadAudit(); p.feed(text)
    return p,text

def meta_value(p: HeadAudit, key: str, value: str) -> str|None:
    for m in p.meta:
        if m.get(key)==value: return m.get("content")
    return None

def canonical(p: HeadAudit) -> str|None:
    for l in p.links:
        if l.get("rel")=="canonical": return l.get("href")
    return None

def jsonld_text(p: HeadAudit) -> str:
    return "\n".join(p.scripts_jsonld)

def check_jaula(path: Path, contract: dict):
    p,text=parse(path); js=jsonld_text(p)
    errors=[]; warnings=[]
    a=JaulaAudit(); a.feed(text)
    facts=contract.get("publicFacts",{}); copy=contract.get("publicCopy",{}); ch=contract.get("chapter1",{})
    h1=" ".join("".join(a.h1_text).split())
    if h1 != facts.get("title"): errors.append(f"H1 mismatch: {h1!r}")
    for value,label in ((facts.get("author"),"author"),(facts.get("editorialStatus"),"editorial status"),(facts.get("type"),"type"),(copy.get("lead"),"authorized lead")):
        if value and value not in text: errors.append(f"missing {label}: {value}")
    for key in ("primaryCta","secondaryCta"):
        c=copy.get(key,{})
        if c.get("label") and c["label"] not in text: errors.append(f"missing {key} label")
        href=c.get("href")
        if href and f'href="{href}"' not in text and f"href='{href}'" not in text: errors.append(f"missing {key} href: {href}")

    paras=a.paragraphs
    if len(paras) != ch.get("paragraphCount"): errors.append(f"chapter paragraph count mismatch: {len(paras)}")
    words=sum(len(x.split()) for x in paras)
    if words != ch.get("wordCount"): errors.append(f"chapter word count mismatch: {words}")
    if paras:
        if paras[0] != ch.get("firstParagraph"): errors.append("chapter first paragraph drift")
        if paras[-1] != ch.get("lastParagraph"): errors.append("chapter last paragraph drift")
    source_payload="\n\n".join(paras)
    digest=hashlib.sha256(source_payload.encode("utf-8")).hexdigest()
    if digest != ch.get("sha256"): errors.append(f"chapter SHA-256 mismatch: {digest}")
    marker=ch.get("sha256")
    if marker and f'data-source-chapter-sha256="{marker}"' not in text: warnings.append("chapter checksum marker missing; payload itself still verified")

    # Staging stays undiscoverable until the explicit promotion gate changes the contract.
    policy=contract.get("stagingPolicy",{})
    if contract.get("productionAllowed") is False:
        robots=(meta_value(p,"name","robots") or "").lower()
        required=(policy.get("robotsMustContain") or "noindex").lower()
        if required not in robots: errors.append(f"staging robots must contain {required!r}: {robots!r}")

    # No publication/commercial metadata may leak in before it is verified and contract-updated.
    forbidden_markup={
        "publicationDate": [r'publicationDate', r'datePublished'],
        "publisher": [r'"publisher"\s*:', r'>\s*Editorial\s*<'],
        "isbn": [r'"isbn"\s*:', r'>\s*ISBN\s*<'],
        "price": [r'"price"\s*:', r'>\s*(?:PVP|Precio)\s*<'],
        "retailers": [r'>\s*Comprar\s*<', r'Amazon', r'Casa del Libro', r'FNAC'],
        "officialCover": [r'jaula[^"\']*(?:cover|portada)|(?:cover|portada)[^"\']*jaula'],
    }
    for key in contract.get("forbiddenUntilVerified",[]):
        for pattern in forbidden_markup.get(key,[]):
            if re.search(pattern,text,re.I): errors.append(f"forbidden until verified: {key} ({pattern})"); break
    # Book schema is not forbidden, but publication-only properties are.
    for prop in ("isbn","publisher","datePublished","offers"):
        if re.search(rf'"{prop}"\s*:',js,re.I): errors.append(f"forbidden JSON-LD property before publication gate: {prop}")
    if "/donde-empieza-la-jaula/" in (canonical(p) or ""):
        warnings.append("canonical points to planned public route while productionAllowed=false; verify staging host policy")
    return errors,warnings

def check_file(label, path, contract, allow_copy_delta=False):
    if label=="jaula":
        return check_jaula(path,contract)
    p,text=parse(path)
    js=jsonld_text(p)
    errors=[]; warnings=[]
    if canonical(p) != contract.get("canonical", contract.get("preserve",{}).get("canonical")):
        errors.append(f"canonical mismatch: {canonical(p)!r}")
    baseline=contract.get("baseline",{})
    if baseline:
        if p.title.strip()!=baseline.get("title"):
            (warnings if allow_copy_delta else errors).append(f"title delta: {p.title.strip()!r}")
        desc=meta_value(p,"name","description")
        if desc!=baseline.get("description"):
            (warnings if allow_copy_delta else errors).append("meta description delta")
        robots=meta_value(p,"name","robots")
        if robots!=baseline.get("robots"): errors.append(f"robots mismatch: {robots!r}")
        if meta_value(p,"property","og:title")!=baseline.get("og_title"): warnings.append("OG title differs from baseline; verify intentional")
        if meta_value(p,"property","og:image")!=baseline.get("og_image"): warnings.append("OG image differs from baseline; verify asset/size/alt")
    for eid in contract.get("canonical_entity_ids",[]):
        if eid not in js: errors.append(f"missing canonical entity @id: {eid}")
    preserve=contract.get("preserve",{})
    if preserve:
        for eid_key in ("book_entity_id","author_entity_id"):
            eid=preserve.get(eid_key)
            if eid and eid not in js: errors.append(f"missing {eid_key}: {eid}")
        hooks=preserve.get("functional_hooks_first_migration",[])
        for hook in hooks:
            if hook.startswith("source:"): continue
            if hook not in text: errors.append(f"missing functional hook: {hook}")
        facts=preserve.get("book_facts",{})
        for key in ("isbn","datePublished","numberOfPages"):
            v=facts.get(key)
            if v is not None and str(v) not in js: errors.append(f"missing Book fact in JSON-LD: {key}={v}")
    if label=="manecillas":
        deep_links=preserve.get("deep_links",{})
        for anchor in deep_links:
            if not re.search(rf'id=["\']{re.escape(anchor)}["\']', text): errors.append(f"missing preserved deep link id: #{anchor}")
        dedication=preserve.get("dedication_contract",{}).get("text")
        if dedication:
            count=text.count(dedication)
            if count!=1: errors.append(f"dedication must appear exactly once, found {count}")
        gate=contract.get("commercial_gate",{})
        if gate.get("status")=="pending-verified-retailer-urls":
            cta=gate.get("pending_state_cta",{})
            href=cta.get("href"); label_text=cta.get("label")
            if href and f'href="{href}"' not in text and f"href='{href}'" not in text: errors.append(f"pending commercial CTA href missing: {href}")
            if label_text and label_text not in text: errors.append(f"pending commercial CTA label missing: {label_text}")
    if label=="home":
        if '"@type": "FAQPage"' in js or '"@type":"FAQPage"' in js: warnings.append("FAQPage present: manually confirm equivalent FAQ remains visible")
        if '"@type": "Review"' in js or '"@type":"Review"' in js: warnings.append("Review schema present: manually confirm reviews remain visible on this page")
        if '"@type": "Event"' in js or '"@type":"Event"' in js: warnings.append("Event schema present: manually confirm event remains substantively represented")
    return errors,warnings

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--home", type=Path)
    ap.add_argument("--manecillas", type=Path)
    ap.add_argument("--jaula", type=Path)
    ap.add_argument("--allow-copy-delta", action="store_true")
    args=ap.parse_args()
    if not args.home and not args.manecillas and not args.jaula:
        ap.error("provide --home, --manecillas and/or --jaula")
    targets=[]
    if args.home:
        targets.append(("home",args.home,json.loads((ROOT/"data/home-preservation.json").read_text(encoding="utf-8"))))
    if args.manecillas:
        targets.append(("manecillas",args.manecillas,json.loads((ROOT/"data/manecillas-preservation.json").read_text(encoding="utf-8"))))
    if args.jaula:
        targets.append(("jaula",args.jaula,json.loads((ROOT/"data/jaula-preservation.json").read_text(encoding="utf-8"))))
    failed=False
    for label,path,contract in targets:
        if not path.exists():
            print(f"FAIL {label}: file not found {path}"); failed=True; continue
        errors,warnings=check_file(label,path,contract,args.allow_copy_delta)
        print(f"{label.upper()} PRESERVATION: {'FAIL' if errors else 'PASS'}")
        for e in errors: print(f"  ERROR: {e}")
        for w in warnings: print(f"  REVIEW: {w}")
        failed |= bool(errors)
    return 1 if failed else 0

if __name__=="__main__": raise SystemExit(main())
