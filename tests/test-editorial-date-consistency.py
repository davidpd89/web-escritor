#!/usr/bin/env python3
"""Mutation regressions for editorial date consistency."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("builder",ROOT/"scripts"/"build-editoriales.py")
sys.path.insert(0,str(ROOT/"scripts"))
from site_clock import site_today
builder=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(builder)
payload=json.loads((ROOT/"data"/"editoriales.json").read_text(encoding="utf-8"))
real_today=site_today()
# Fecha civil Europe/Madrid; inyectable con SITE_TODAY=YYYY-MM-DD. Nunca se deriva
# de los datos: así un registro con fecha futura no puede validarse a sí mismo.
today=date.fromisoformat(os.environ["SITE_TODAY"]) if os.environ.get("SITE_TODAY") else real_today
# Registro base coherente con `today` (sea cual sea): las mutaciones solo pueden
# fallar por el motivo que prueban, no porque los datos reales sean "futuro".
base=copy.deepcopy(next(r for r in payload["publishers"] if r.get("publish") is True))
base["verified_at"]=(today-timedelta(days=10)).isoformat()
base["page_updated_at"]=(today-timedelta(days=5)).isoformat()
for h in base["history"]:
    h["date"]=(today-timedelta(days=20)).isoformat()
builder.validate_record(copy.deepcopy(base),set(),today)

def expect_invalid(record:dict,needle:str)->None:
    try:
        builder.validate_record(record,set(),today)
    except builder.ValidationError as exc:
        assert needle in str(exc),f"expected {needle!r} in {exc!r}"
    else:
        raise AssertionError(f"mutation unexpectedly accepted; expected {needle!r}")

future_page=copy.deepcopy(base)
future_page["page_updated_at"]=(today+timedelta(days=1)).isoformat()
expect_invalid(future_page,"page_updated_at está en el futuro")

future_history=copy.deepcopy(base)
future_history["page_updated_at"]=today.isoformat()
future_history["history"][0]["date"]=(today+timedelta(days=1)).isoformat()
expect_invalid(future_history,"history[0].date está en el futuro")

history_after_page=copy.deepcopy(base)
history_after_page["page_updated_at"]=(today-timedelta(days=3)).isoformat()
history_after_page["history"][0]["date"]=(today-timedelta(days=1)).isoformat()
expect_invalid(history_after_page,"no puede ser posterior")

# Los datos reales no pueden estar fechados después de hoy (Madrid).
for r in payload["publishers"]:
    for k in ("verified_at","page_updated_at"):
        assert date.fromisoformat(r[k])<=real_today,f"{r.get('slug')}.{k} en el futuro respecto a {real_today}"
    for h in r.get("history",[]):
        assert date.fromisoformat(h["date"])<=real_today,f"{r.get('slug')} history en el futuro respecto a {real_today}"

# Regresión negativa: con hoy inyectado anterior a la verificación más reciente, se rechaza.
latest=max(date.fromisoformat(r["page_updated_at"]) for r in payload["publishers"] if r.get("publish") is True)
rec=next(r for r in payload["publishers"] if r.get("publish") is True and date.fromisoformat(r["page_updated_at"])==latest)
try:
    builder.validate_record(copy.deepcopy(rec),set(),latest-timedelta(days=1))
except builder.ValidationError as exc:
    assert "futuro" in str(exc),exc
else:
    raise AssertionError("fecha futura aceptada con hoy inyectado anterior")

print("test-editorial-date-consistency: OK")
