#!/usr/bin/env python3
"""Intrinsic QA for professional writer resources; no network requests."""
from __future__ import annotations
import importlib.util,json,re,unicodedata
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
def editorials_builder():
    p=ROOT/"scripts/build-editoriales.py";spec=importlib.util.spec_from_file_location("editorials_builder",p);m=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(m);return m
def check_editorials():
    b=editorials_builder();real_today=date.today()
    src=load(Path("data/editoriales.json"));pub=load(Path("editoriales/editoriales-data.json"))
    items=src.get("publishers");public=pub.get("publishers")
    if not isinstance(items,list) or not isinstance(public,list):fail("editoriales: publishers[] missing")
    seen=set()
    for item in items:
        slug=item.get("slug")
        if not slug or slug in seen:fail(f"editoriales duplicate/missing slug {slug!r}")
        seen.add(slug)
        if item.get("status") not in STATUS:fail(f"{slug}: invalid status")
        verified=iso(item.get("verified_at"),f"{slug}.verified_at")
        if verified>real_today:fail(f"{slug}: verified_at is in the future")
        for key in ("submission_url","website_url"):
            if item.get(key):https(item[key],f"{slug}.{key}")
        for n,source in enumerate(item.get("sources",[])):
            https(source.get("url"),f"{slug}.sources[{n}]")
        if item.get("status")!="open" and item.get("submission_email"):fail(f"{slug}: submission email exposed while not open")
    published=[i for i in items if i.get("publish",True)]
    expected={i["slug"] for i in published}
    if {i.get("slug") for i in public}!=expected:fail("editoriales source/public mismatch")
    details={p.parent.name for p in (ROOT/"editoriales").glob("*/index.html")}
    if details!=expected:fail(f"editoriales detail coverage mismatch data={sorted(expected)} details={sorted(details)}")

    # Real-clock freshness: unlike a deadline, an editorial entry does not
    # disappear after N days; instead the builder marks >90-day verifications
    # as needing review. This guard makes that threshold advance with the real
    # execution date, so a static build cannot silently cross day 91 without
    # regenerating its warning state.
    stale_now=[i for i in published if b.stale(i,real_today)]
    index_html=(ROOT/"editoriales/index.html").read_text(encoding="utf-8")
    marker="Verificación antigua: revisa la fuente oficial antes de enviar."
    if index_html.count(marker)!=len(stale_now):
        fail(f"editoriales index stale-warning drift for {real_today}: expected {len(stale_now)} marker(s), found {index_html.count(marker)}")
    detail_marker="<strong>Revisión recomendada:</strong>"
    for item in published:
        detail=(ROOT/"editoriales"/item["slug"]/"index.html").read_text(encoding="utf-8")
        expected_stale=b.stale(item,real_today)
        if (detail_marker in detail)!=expected_stale:
            fail(f"{item['slug']}: detail stale-warning drift for real execution date {real_today}")
def normalized_title(value):
    folded=unicodedata.normalize("NFD",str(value)).encode("ascii","ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+"," ",folded).strip()
def check_radar_sources():
    src=load(Path("data/radar-sources.json"));sources=src.get("sources")
    if not isinstance(sources,list):fail("radar sources[] missing")
    ids=set();urls=set()
    for source in sources:
        sid=source.get("id");url=str(source.get("url") or "").rstrip("/").casefold()
        if not sid or sid in ids:fail(f"radar source duplicate/missing id {sid!r}")
        ids.add(sid)
        https(source.get("url"),f"radar source {sid}.url")
        if url in urls:fail(f"radar source duplicate URL {source.get('url')}")
        urls.add(url)
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
def check_radar_freshness(builder,items,published_items,generated_for,real_today):
    if generated_for>real_today:fail(f"radar generated_for {generated_for} is in the future relative to {real_today}")
    live_expected=builder.active_items(items,real_today)
    if published_items!=live_expected:
        live_ids=[item["id"] for item in live_expected]
        published_ids=[item.get("id") for item in published_items]
        fail(
            "radar public output is stale for real execution date "
            f"{real_today}: published={published_ids} expected={live_ids}; regenerate only after verifying official sources when required"
        )
def check_radar():
    b=radar_builder();src=load(Path("data/radar-opportunities.json"));items=src.get("items");watchlist=src.get("watchlist",[])
    if not isinstance(items,list):fail("radar source items[] missing")
    if not isinstance(watchlist,list):fail("radar source watchlist[] invalid")
    ids=set();semantic=set()
    for item in items:
        b.validate(item)
        if item["id"] in ids:fail(f"radar duplicate id {item['id']}")
        ids.add(item["id"])
        key=(item["deadline"],normalized_title(item["title"]))
        if key in semantic:fail(f"radar semantic duplicate deadline/title {key}")
        semantic.add(key)
    watch_ids=set()
    for item in watchlist:
        b.validate_watch(item)
        if item["id"] in ids or item["id"] in watch_ids:fail(f"radar duplicate id across items/watchlist {item['id']}")
        watch_ids.add(item["id"])
    real_today=date.today()
    for item in items:
        if item.get("published") and iso(item.get("verified_at"),f"{item.get('id')}.verified_at")>real_today:fail(f"{item['id']}: verified_at is in the future")
    for item in watchlist:
        if item.get("published") and iso(item.get("verified_at"),f"{item.get('id')}.verified_at")>real_today:fail(f"{item['id']}: watchlist verified_at is in the future")
    pub=load(Path("convocatorias-escritores/opportunities.json"));generated_for=iso(pub.get("generated_for"),"generated_for");expected=b.active_items(items,generated_for);expected_watch=b.watch_items(watchlist,generated_for)
    if pub.get("items")!=expected:fail("radar public JSON drifted from source/builder at its generated_for clock")
    if pub.get("watchlist",[])!=expected_watch:fail("radar public watchlist drifted from source/builder")
    check_radar_freshness(b,items,pub.get("items"),generated_for,real_today)
    if pub.get("watchlist",[])!=b.watch_items(watchlist,real_today):fail("radar watchlist public output is stale for real execution date")
    html=(ROOT/"convocatorias-escritores/index.html").read_text(encoding="utf-8")
    if html!=b.build_html(items,generated_for,watchlist):fail("radar HTML drifted from builder")
    if STATIC_DAYS.search(html):fail("radar HTML contains static countdown")
    if "connect-src 'none'" not in html:fail("radar CSP connect-src changed")
    ics=b.build_ics(items,generated_for).encode("utf-8")
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
    check_editorials();check_radar_sources();check_radar();print("OK professional resources: data, detail coverage, generated outputs, real-clock freshness and ICS parity")
if __name__=="__main__":main()
