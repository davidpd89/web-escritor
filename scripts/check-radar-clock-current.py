#!/usr/bin/env python3
"""Detect whether committed radar outputs still match the source at a civil date."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from site_clock import site_today  # noqa: E402
BUILDER_PATH=ROOT/"scripts"/"build-radar-opportunities.py"
SOURCE_PATH=ROOT/"data"/"radar-opportunities.json"
PUBLIC_PATH=ROOT/"convocatorias-escritores"/"opportunities.json"

def load_builder():
    spec=importlib.util.spec_from_file_location("radar_builder_clock",BUILDER_PATH)
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

def main()->int:
    ap=argparse.ArgumentParser()
    # Madrid civil date, not the runner's UTC date: the daily refresh is generated
    # for Madrid's day, so between 00:00 and 02:00 Madrid (UTC still "yesterday")
    # an UTC default made every refresh PR fail its own merge gate.
    ap.add_argument("--today",default=site_today().isoformat())
    args=ap.parse_args()
    builder=load_builder()
    today=builder.iso_date(args.today,"today")
    source=json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    public=json.loads(PUBLIC_PATH.read_text(encoding="utf-8"))
    items=source.get("items",[])
    watchlist=source.get("watchlist",[])
    for item in items: builder.validate(item)
    for item in watchlist: builder.validate_watch(item)
    builder.ensure_disjoint_ids(items,watchlist)
    expected_items=builder.active_items(items,today)
    expected_watch=builder.watch_items(watchlist,today)
    current_items=public.get("items",[])
    current_watch=public.get("watchlist",[])
    if current_items==expected_items and current_watch==expected_watch:
        print(f"RADAR CLOCK: CURRENT for {today.isoformat()} (active={len(expected_items)} watch={len(expected_watch)}; generated_for={public.get('generated_for')})")
        return 0
    current_ids={item.get("id") for item in current_items}
    expected_ids={item.get("id") for item in expected_items}
    current_watch_ids={item.get("id") for item in current_watch}
    expected_watch_ids={item.get("id") for item in expected_watch}
    print(f"RADAR CLOCK: REFRESH REQUIRED for {today.isoformat()}",file=sys.stderr)
    changes=[
        ("active should add",sorted(expected_ids-current_ids)),
        ("active should remove",sorted(current_ids-expected_ids)),
        ("watch should add",sorted(expected_watch_ids-current_watch_ids)),
        ("watch should remove",sorted(current_watch_ids-expected_watch_ids)),
    ]
    emitted=False
    for label,values in changes:
        if values:
            emitted=True
            print(f"  {label}: {values}",file=sys.stderr)
    if not emitted:
        print("  item payload/order drifted from deterministic builder output",file=sys.stderr)
    return 1

if __name__=="__main__":
    raise SystemExit(main())
