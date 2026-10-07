#!/usr/bin/env python3
"""Contract for issue #555 manual QA documentation.

The issue is intentionally not an automated browser gate: it covers physical
devices, screen readers, external preview caches, webmaster tools and Brevo
side effects. This test only protects the manual runbook so the scope cannot be
silently narrowed later.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "qa" / "PENDING-REAL-DEVICE-AUDITS.md"

text = DOC.read_text(encoding="utf-8")
lower = text.lower()
normalized = " ".join(lower.split())

required_terms = [
    "#555",
    "iphone",
    "ipad",
    "safari",
    "pwa instalada",
    "primer arranque",
    "segundo arranque",
    "modo avion",
    "android",
    "talkback",
    "windows",
    "nvda",
    "jaws",
    "macos",
    "voiceover",
    "whatsapp",
    "telegram",
    "discord",
    "slack",
    "linkedin",
    "x",
    "facebook",
    "search console",
    "bing webmaster",
    "brevo",
    "alta",
    "confirmacion",
    "baja",
    "error de proveedor",
]

required_evidence_fields = [
    "fecha y zona horaria",
    "persona que ejecuta",
    "dispositivo fisico o servicio",
    "sistema operativo y version",
    "navegador, app o lector de pantalla",
    "url o flujo probado",
    "resultado `pass`, `fail`, `blocked`, `waived` o `not_applicable`",
    "evidencia",
    "incidencias abiertas",
]

for term in required_terms:
    assert term in lower, f"Manual QA doc no longer covers {term!r}"

for field in required_evidence_fields:
    assert field in lower, f"Manual QA doc missing evidence field {field!r}"

assert "no se deben marcar como superadas por inferencia" in normalized
assert "no convertir esta matriz en un gate automatico" in normalized
assert "blocked` solo es valido" in lower
assert "`waived` solo es valido" in lower
assert "`not_applicable` solo es valido" in lower
assert "nunca usar direcciones de terceros" in lower

evidence_path = ROOT / "docs" / "qa" / "REAL-DEVICE-SERVICE-EVIDENCE-2026-10-07.md"
evidence = evidence_path.read_text(encoding="utf-8").lower()
for term in [
    "edge real en windows - pass",
    "dispositivos apple fisicos y pwa ios - waived",
    "android con talkback - waived",
    "windows con nvda o jaws - waived",
    "macos con voiceover y safari - waived",
    "google search console - pass",
    "bing webmaster tools - pass",
    "brevo/newsletter - pass",
]:
    assert term in evidence, f"Issue #555 evidence missing {term!r}"

print("OK: issue #555 real-device/manual-service QA contract is preserved.")
