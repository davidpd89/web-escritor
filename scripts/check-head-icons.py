#!/usr/bin/env python3
"""Normalize the browser favicon to the lightweight approved ICO asset.

The approved yellow DP brand is available in several purpose-specific files.
Browser tabs should use /favicon.ico (~7 KiB) instead of the much larger master
PNG. Apple touch icons deliberately keep the approved master PNG; the current
512px PWA PNG is not smaller and is reserved for manifest/install surfaces.

Use --write for deterministic normalization or --check as a read-only gate.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD_ICON='<link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />'
NEW_ICON='<link rel="icon" href="/favicon.ico" sizes="any" />'
LEGACY_ICON_RE=re.compile(r'<link\\b(?=[^>]*\\brel=["\\\'][^"\\\']*\\bicon\\b[^"\\\']*["\\\'])(?=[^>]*\\bhref=["\\\']/assets/david-porto-favicon\\.png["\\\'])[^>]*>',re.I)


def tracked_targets()->list[Path]:
    out=subprocess.run(
        ["git","ls-files","-z","*.html","scripts/*.py"],
        cwd=ROOT,capture_output=True,text=True,check=True,
    ).stdout
    paths=[]
    for rel in out.split("\0"):
        if not rel or rel=="scripts/check-head-icons.py":
            continue
        paths.append(ROOT/rel)
    return paths


def normalize(text:str)->str:
    return LEGACY_ICON_RE.sub(NEW_ICON,text)


def main()->int:
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--write",action="store_true")
    args=ap.parse_args()

    changed=[]
    for path in tracked_targets():
        original=path.read_text(encoding="utf-8")
        updated=normalize(original)
        if updated==original:
            continue
        rel=path.relative_to(ROOT).as_posix()
        changed.append(rel)
        if args.write:
            path.write_text(updated,encoding="utf-8")

    if args.check and changed:
        print("HEAD ICON CONTRACT: FAIL — browser favicon normalization required")
        for path in changed[:200]:
            print(" -",path)
        return 1

    action="normalized" if args.write else "verified"
    print(f"HEAD ICON CONTRACT: OK — {action}; changed={len(changed)}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
