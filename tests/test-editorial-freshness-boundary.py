#!/usr/bin/env python3
"""Boundary regression for the editorial 90-day freshness contract."""
from __future__ import annotations

import importlib.util
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("builder",ROOT/"scripts"/"build-editoriales.py")
builder=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(builder)

today=date(2026,10,5)

def record(days:int)->dict:
    return {
        "slug":"qa-editorial",
        "name":"QA Editorial",
        "group":"QA",
        "publisher_type":"editorial tradicional",
        "country":"España",
        "genres":["narrativa"],
        "status":"open",
        "direct_submission":True,
        "submission_channel":"Formulario",
        "submission_url":"https://example.com/manuscritos",
        "submission_email":None,
        "website_url":"https://example.com/",
        "response_time":None,
        "requirements":["Enviar sinopsis."],
        "summary":"Registro sintético para probar exclusivamente la frontera de frescura.",
        "public_note":"Registro sintético de QA.",
        "verified_at":(today-timedelta(days=days)).isoformat(),
        "page_updated_at":(today-timedelta(days=days)).isoformat(),
        "sources":[{"label":"Fuente oficial","url":"https://example.com/manuscritos","primary":True}],
        "history":[{"date":(today-timedelta(days=days)).isoformat(),"event":"Comprobación QA.","source_url":"https://example.com/manuscritos"}],
        "publish":True,
    }

r90=record(90)
r91=record(91)
assert builder.stale(r90,today) is False,"90 days must not be stale"
assert builder.stale(r91,today) is True,"91 days must be stale"

index90=builder.render_index("https://davidportodiaz.com",[r90],today)
index91=builder.render_index("https://davidportodiaz.com",[r91],today)
detail90=builder.render_detail("https://davidportodiaz.com",r90,today)
detail91=builder.render_detail("https://davidportodiaz.com",r91,today)

assert "Verificación antigua:" not in index90
assert "Verificación antigua:" in index91
assert "<strong>Revisión recomendada:</strong>" not in detail90
assert "<strong>Revisión recomendada:</strong>" in detail91

print("test-editorial-freshness-boundary: OK (90=current, 91=review)")
