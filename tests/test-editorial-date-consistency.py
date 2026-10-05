#!/usr/bin/env python3
"""Mutation regressions for editorial date consistency."""
from __future__ import annotations

import copy
import importlib.util
import json
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("builder",ROOT/"scripts"/"build-editoriales.py")
builder=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(builder)
payload=json.loads((ROOT/"data"/"editoriales.json").read_text(encoding="utf-8"))
base=next(r for r in payload["publishers"] if r.get("publish") is True)
today=date(2026,10,5)

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

print("test-editorial-date-consistency: OK")
