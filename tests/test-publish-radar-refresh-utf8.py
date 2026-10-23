#!/usr/bin/env python3
"""gh() must decode subprocess output as UTF-8, not the Windows locale (cp1252)."""
from __future__ import annotations
import importlib.util, locale, subprocess
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("publish_radar_refresh",ROOT/"scripts"/"publish-radar-refresh.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

PAYLOAD="Convocatoria — «Ñandú» ✓ 日本".encode("utf-8")
seen={}
def fake_run(cmd,**kw):
    seen.update(kw)
    # emulate text=True decoding with the declared encoding, as subprocess does
    out=PAYLOAD.decode(kw.get("encoding") or locale.getpreferredencoding(False),errors=kw.get("errors") or "strict")
    return subprocess.CompletedProcess(cmd,0,stdout=out+"\n",stderr="")

with mock.patch.object(mod.subprocess,"run",fake_run):
    assert mod.gh("x")==PAYLOAD.decode("utf-8")
assert seen.get("encoding")=="utf-8",seen
assert seen.get("errors")=="replace",seen
print("ok publish-radar-refresh utf-8 decoding")
