#!/usr/bin/env python3
"""Preflight editorial para el cierre anual "Estado de David Porto" (doc 51).

No genera el articulo ni inventa el balance del ano; solo impide publicar un
borrador que no cumpla los minimos de fuente y certeza acordados.

Reglas de doc 51 SS10-11:
- bloquea publicacion con [[pendiente]];
- exige fecha de verificacion (verified_at);
- exige fuente para hitos declarados como verificados;
- obliga a clasificar previsiones como confirmed, target o aspiration;
- impide que una prevision confirmed carezca de fuente.

Uso:
  python scripts/validate-author-state.py <borrador.md> [...]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ALLOWED_STATUS = {"draft", "review", "published"}
FORECAST_CERTAINTY = {"confirmed", "target", "aspiration"}
MILESTONE_TAGS = {"verified", "unverified"}

# `- [tag] texto — fuente: lo que sea` con el separador de fuente opcional.
# El guion largo/medio antes de "fuente:" es intercambiable (—, --, -).
ITEM_RE = re.compile(
    r"^-\s*\[(?P<tag>[a-z]+)\]\s*(?P<text>.+?)(?:\s*[—–-]{1,2}\s*fuente:\s*(?P<source>.+))?$",
    re.IGNORECASE,
)


def is_pending(value: str) -> bool:
    return "[[pendiente" in (value or "").lower()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("Falta front matter inicial")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("Front matter sin cierre ---") from exc
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, body


def section(body: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)", re.MULTILINE)
    match = pattern.search(body)
    return match.group(1) if match else ""


def parse_items(section_text: str) -> list[dict[str, str]]:
    items = []
    for line in section_text.splitlines():
        m = ITEM_RE.match(line.strip())
        if m:
            items.append(
                {
                    "tag": m.group("tag").lower(),
                    "text": m.group("text").strip(),
                    "source": (m.group("source") or "").strip(),
                }
            )
    return items


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = Path(path).read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    status = meta.get("status", "")
    if status not in ALLOWED_STATUS:
        errors.append(f"status inválido: {status!r}")

    year = meta.get("year", "")
    if is_pending(year) or not re.fullmatch(r"\d{4}", year or ""):
        # Solo bloqueante al publicar; en draft/review se permite trabajar
        # sin el año todavía fijado.
        if status == "published":
            errors.append("year debe ser un año de 4 dígitos")

    if status == "published":
        if is_pending(meta.get("verified_at", "")) or not meta.get("verified_at", "").strip():
            errors.append("verified_at obligatorio (fecha de verificación)")
        if "[[pendiente" in text.lower():
            errors.append("Publicado con marcadores [[pendiente]]")

        milestones = parse_items(section(body, "Hitos verificados del año"))
        for item in milestones:
            if item["tag"] not in MILESTONE_TAGS:
                errors.append(f"Hito con etiqueta desconocida: {item['tag']!r}")
                continue
            if item["tag"] == "unverified":
                errors.append(f"Hito sin verificar no puede publicarse: {item['text']}")
            elif item["tag"] == "verified" and (not item["source"] or is_pending(item["source"])):
                errors.append(f"Hito verificado sin fuente: {item['text']}")

        forecasts = parse_items(section(body, "Previsiones"))
        for item in forecasts:
            if item["tag"] not in FORECAST_CERTAINTY:
                errors.append(f"Previsión sin clasificar como confirmed/target/aspiration: {item['text']}")
                continue
            if item["tag"] == "confirmed" and (not item["source"] or is_pending(item["source"])):
                errors.append(f"Previsión 'confirmed' sin fuente: {item['text']}")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: validate-author-state.py <borrador.md> [...]", file=sys.stderr)
        return 2
    failed = False
    for raw in sys.argv[1:]:
        path = Path(raw)
        errs = validate(path)
        if errs:
            failed = True
            print(f"FAIL {path}")
            for err in errs:
                print(f"  - {err}")
        else:
            print(f"PASS {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
