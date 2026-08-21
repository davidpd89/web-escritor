#!/usr/bin/env python3
"""Intrinsic QA for professional writer resources; no network requests."""
from __future__ import annotations
import importlib.util,json,re
from datetime import date,timedelta
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
STATUS={"open","closed","indirect","award_only","unknown"}
BAD_URL=re.compile(r"[\s\\\x00-\x1f\x7f<>\"{}|^`]")
STATIC_DAYS=re.compile(r"<time[^>]+>\d{2}/\d{2}/\d{4}</time>\s*·\s*\d+\s+días\b",re.I)
def fail(m):raise AssertionError(m)
def iso(v,label):
    if not isinstance(v,str):fail(f"{label}: expected ISO date string")
    try:return date.fromisoformat(v)
    except ValueError as e:raise AssertionError(f"{label}: invalid ISO date {v!r}") from e
def https(v,label):
    if not isinstance(v,str) or not v or BAD_URL.search(v):fail(f"{label}: invalid URL characters")
    try:p=urlsplit(v);port=p.port
    except ValueError as e:raise AssertionError(f"{label}: malformed URL") from e
    if p.scheme!="https" or not p.hostname or p.username or p.password or port not in (None,443):fail(f"{label}: must be clean HTTPS URL")
def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))
def check_editorials():
    src=load(Path("data/editoriales.json"));pub=load(Path("editoriales/editoriales-data.json"))
    items=src.get("publishers");public=pub.get("publishers")
    if not isinstance(items,list) or not isinstance(public,list):fail("editoriales: publishers[] missing")
    seen=set()
    for item in items:
        slug=item.get("slug")
        if not slug or slug in seen:fail(f"editoriales duplicate/missing slug {slug!r}")
        seen.add(slug)
        if item.get("status") not in STATUS:fail(f"{slug}: invalid status")
        iso(item.get("verified_at"),f"{slug}.verified_at")
        for key in ("submission_url","website_url"):
            if item.get(key):https(item[key],f"{slug}.{key}")
        for n,source in enumerate(item.get("sources",[])):
            https(source.get("url"),f"{slug}.sources[{n}]")
        if item.get("status")!="open" and item.get("submission_email"):fail(f"{slug}: submission email exposed while not open")
    expected={i["slug"] for i in items if i.get("publish",True)}
    if {i.get("slug") for i in public}!=expected:fail("editoriales source/public mismatch")
    details={p.parent.name for p in (ROOT/"editoriales").glob("*/index.html")}
    if details!=expected:fail(f"editoriales detail coverage mismatch data={sorted(expected)} details={sorted(details)}")
def radar_builder():
    p=ROOT/"scripts/build-radar-opportunities.py";spec=importlib.util.spec_from_file_location("radar_builder",p);m=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(m);return m
def unfold(raw):
    if b"\r\n" not in raw or re.search(br"(?<!\r)\n|\r(?!\n)",raw):fail("ICS: line endings must be CRLF only")
    out=[]
    for line in raw.decode("utf-8").split("\r\n"):
        if line.startswith((" ","\t")):
            if not out:fail("ICS: orphan fold")
            out[-1]+=line[1:]
        else:out.append(line)
    return out
def parse_ics():
    lines=unfold((ROOT/"convocatorias-escritores/deadlines.ics").read_bytes())
    if lines[:1]!=["BEGIN:VCALENDAR"] or "END:VCALENDAR" not in lines:fail("ICS envelope invalid")
    for req in ("VERSION:2.0","CALSCALE:GREGORIAN","METHOD:PUBLISH"):
        if req not in lines:fail(f"ICS missing {req}")
    events=[];cur=None
    for line in lines:
        if line=="BEGIN:VEVENT":cur={}
        elif line=="END:VEVENT":events.append(cur);cur=None
        elif cur is not None and ":" in line:
            k,v=line.split(":",1);cur[k]=v
    if cur is not None:fail("ICS unterminated VEVENT")
    return events
def unesc(v):return v.replace("\\n","\n").replace("\\,",",").replace("\\;",";").replace("\\\\","\\")
def check_radar():
    b=radar_builder();src=load(Path("data/radar-opportunities.json"));items=src.get("items")
    if not isinstance(items,list):fail("radar source items[] missing")
    ids=set()
    for item in items:
        b.validate(item)
        if item["id"] in ids:fail(f"radar duplicate id {item['id']}")
        ids.add(item["id"])
    pub=load(Path("convocatorias-escritores/opportunities.json"));today=iso(pub.get("generated_for"),"generated_for");expected=b.active_items(items,today)
    if pub.get("items")!=expected:fail("radar public JSON drifted from source/builder")
    html=(ROOT/"convocatorias-escritores/index.html").read_text(encoding="utf-8")
    if html!=b.build_html(items,today):fail("radar HTML drifted from builder")
    if STATIC_DAYS.search(html):fail("radar HTML contains static countdown")
    if "connect-src 'none'" not in html:fail("radar CSP connect-src changed")
    ics=b.build_ics(items,today).encode("utf-8")
    if (ROOT/"convocatorias-escritores/deadlines.ics").read_bytes()!=ics:fail("ICS drifted from builder")
    events=parse_ics()
    if len(events)!=len(expected):fail("ICS event count mismatch")
    by_uid={e.get("UID"):e for e in events}
    if len(by_uid)!=len(events):fail("ICS duplicate UID")
    for item in expected:
        e=by_uid.get(f"{item['id']}@davidportodiaz.com")
        if not e:fail(f"ICS missing {item['id']}")
        if e.get("DTSTART;VALUE=DATE")!=item["deadline"].replace("-",""):fail(f"ICS deadline mismatch {item['id']}")
        if unesc(e.get("SUMMARY",""))!=item["title"]:fail(f"ICS summary mismatch {item['id']}")
        if e.get("URL")!=item["source_url"]:fail(f"ICS URL mismatch {item['id']}")
        nxt=(iso(item["deadline"],item["id"])+timedelta(days=1)).strftime("%Y%m%d")
        if e.get("DTEND;VALUE=DATE")!=nxt:fail(f"ICS DTEND mismatch {item['id']}")
def main():
    check_editorials();check_radar();print("OK professional resources: data, detail coverage, generated outputs and ICS parity")
if __name__=="__main__":main()
