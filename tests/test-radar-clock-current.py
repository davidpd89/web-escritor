#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=json.loads((ROOT/"convocatorias-escritores"/"opportunities.json").read_text(encoding="utf-8"))
CHECKER=ROOT/"scripts"/"check-radar-clock-current.py"
generated_for=date.fromisoformat(PUBLIC["generated_for"])

current=subprocess.run([sys.executable,str(CHECKER),"--today",generated_for.isoformat()],cwd=ROOT,text=True,capture_output=True)
assert current.returncode==0,current.stdout+current.stderr

deadlines=sorted(date.fromisoformat(item["deadline"]) for item in PUBLIC.get("items",[]) if item.get("deadline"))
assert deadlines,"public radar has no dated active items to exercise clock drift"
probe=deadlines[0]+timedelta(days=1)
future=subprocess.run([sys.executable,str(CHECKER),"--today",probe.isoformat()],cwd=ROOT,text=True,capture_output=True)
assert future.returncode==1,(
    "clock checker failed to detect expiration after earliest committed deadline "
    f"{deadlines[0]} on {probe}:\n{future.stdout}{future.stderr}"
)
assert "REFRESH REQUIRED" in (future.stdout+future.stderr)
print(f"PASS radar clock-current regression: committed clock {generated_for}; {probe} requires refresh")
