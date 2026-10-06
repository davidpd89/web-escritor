#!/usr/bin/env python3
"""Guard .lycheeignore against broad or stale link-check exceptions."""
from __future__ import annotations
import html, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
IGNORE=ROOT/".lycheeignore"

ALLOWED_BROAD={
r"https?://([^/]+\.)?instagram\.com/.*",
r"https?://([^/]+\.)?facebook\.com/.*",
r"https?://([^/]+\.)?(twitter|x)\.com/.*",
r"https?://([^/]+\.)?amazon\.[^/]+/.*",
r"https?://([^/]+\.)?goodreads\.com/.*",
r"https?://([^/]+\.)?casadellibro\.com/.*",
r"https?://([^/]+\.)?fnac\.es/.*",
r"https?://([^/]+\.)?elcorteingles\.es/.*",
r"https?://([^/]+\.)?todostuslibros\.com/.*",
r"https?://([^/]+\.)?linkedin\.com/.*",
r"https?://([^/]+\.)?librarything\.com/.*",
r"https?://([^/]+\.)?reddit\.com/.*",
r"https?://([^/]+\.)?thestorygraph\.com/.*",
r"https?://([^/]+\.)?siarchives\.si\.edu/.*",
r"https?://([^/]+\.)?tandfonline\.com/.*",
r"https?://([^/]+\.)?planetadelibros\.com/.*",
r"https?://([^/]+\.)?diversidadliteraria\.com/.*",
r"https?://([^/]+\.)?davidportodiaz\.com/.*",
}
URL_RE=re.compile(r"""(?:href|src|action|formaction|poster)\s*=\s*["']([^"']+)["']""",re.I)

def html_urls():
    urls=set()
    for path in ROOT.rglob("*.html"):
        if any(part in {".git","node_modules","tests","scripts","artifacts",".github","data"} or part.startswith(".preview-dist") for part in path.parts):
            continue
        try: text=path.read_text(encoding="utf-8")
        except OSError: continue
        for raw in URL_RE.findall(text):
            value=html.unescape(raw.strip())
            if value.startswith(("http://","https://")): urls.add(value)
    return urls

def main():
    patterns=[]
    errors=[]
    for n,raw in enumerate(IGNORE.read_text(encoding="utf-8").splitlines(),1):
        line=raw.strip()
        if not line or line.startswith("#"): continue
        patterns.append((n,line))
        if line in ALLOWED_BROAD: continue
        if not (line.startswith("^https://") and line.endswith("$")):
            errors.append(f".lycheeignore:{n}: non-whitelisted exception must be exact/anchored: {line}")
    urls=html_urls()
    for n,line in patterns:
        if line in ALLOWED_BROAD: continue
        try: rx=re.compile(line)
        except re.error as exc:
            errors.append(f".lycheeignore:{n}: invalid regex {exc}: {line}")
            continue
        matches=[u for u in urls if rx.fullmatch(u)]
        if not matches:
            errors.append(f".lycheeignore:{n}: stale exact exception matches no public HTML URL: {line}")
    if errors:
        print(f"FAIL Lychee exception hygiene: {len(errors)} issue(s)")
        for e in errors: print("-",e)
        return 1
    exact=sum(1 for _,p in patterns if p not in ALLOWED_BROAD)
    print(f"PASS Lychee exception hygiene: {len(ALLOWED_BROAD)} approved broad blockers, {exact} exact live exceptions")
    return 0

if __name__=="__main__": raise SystemExit(main())
