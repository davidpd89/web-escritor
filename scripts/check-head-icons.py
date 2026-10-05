#!/usr/bin/env python3
"""Normalize lightweight favicon/touch-icon declarations across tracked public HTML and builders.

The site historically reused assets/david-porto-favicon.png (1254x1254,
~732 KiB) for both browser favicons and Apple touch icons. The repository
already ships purpose-specific assets:
- /favicon.ico (16/32/48 px, ~3.5 KiB) for browser favicons.
- /assets/icon-512.png (~153 KiB) for high-resolution install/touch surfaces.

This script keeps generated and hand-authored pages from drifting back to the
master PNG. Use --write for deterministic normalization or --check as a gate.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD="/assets/david-porto-favicon.png"
OLD_ICON='<link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />'
NEW_ICON='<link rel="icon" href="/favicon.ico" sizes="any" />'
OLD_TOUCH='<link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />'
NEW_TOUCH='<link rel="apple-touch-icon" href="/assets/icon-512.png" />'

def tracked_targets()->list[Path]:
    out=subprocess.run(
        ["git","ls-files","-z","*.html","scripts/*.py"],
        cwd=ROOT,capture_output=True,text=True,check=True,
    ).stdout
    return [ROOT/p for p in out.split("\0") if p]

def normalize(text:str)->str:
    return text.replace(OLD_ICON,NEW_ICON).replace(OLD_TOUCH,NEW_TOUCH)

def main()->int:
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--write",action="store_true")
    args=ap.parse_args()

    changed=[]
    unresolved=[]
    for path in tracked_targets():
        text=path.read_text(encoding="utf-8")
        updated=normalize(text)
        if args.write and updated!=text:
            path.write_text(updated,encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())
            text=updated
        else:
            text=updated if args.check else text

        if OLD in text:
            for n,line in enumerate(text.splitlines(),1):
                if OLD in line:
                    unresolved.append(f"{path.relative_to(ROOT).as_posix()}:{n}: {line.strip()}")

        if args.check and updated!=path.read_text(encoding="utf-8"):
            # In check mode, any normalizable legacy declaration is drift.
            changed.append(path.relative_to(ROOT).as_posix())

    if unresolved:
        print("HEAD ICON CONTRACT: FAIL — unresolved legacy master-PNG references")
        for row in unresolved[:100]: print(" -",row)
        return 1
    if args.check and changed:
        print("HEAD ICON CONTRACT: FAIL — normalization required")
        for path in sorted(set(changed)): print(" -",path)
        return 1

    action="normalized" if args.write else "verified"
    print(f"HEAD ICON CONTRACT: OK — {action}; changed={len(set(changed))}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
