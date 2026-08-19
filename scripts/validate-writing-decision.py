#!/usr/bin/env python3
"""Preflight editorial para borradores de decisiones de escritura.

No genera contenido ni decide si una página es buena. Solo impide publicar
borradores sin los mínimos de trazabilidad acordados para la IDEA 38.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

VALID_SPOILERS = {"none", "light", "chapter", "full"}
VALID_VARIANTS = {"decision", "before_after", "discard"}
REQUIRED_META = {
    "status", "content_variant", "book_slug", "public_slug", "title", "spoiler_level",
    "source_evidence", "evidence_private", "decision_date", "last_verified",
    "contains_third_party_editorial_text", "editorial_permission"
}
REQUIRED_SECTIONS = [
    "La decisión en una frase",
    "Qué no funcionaba",
    "Qué opciones reales tenía",
    "Qué elegí",
    "Qué perdí o qué coste tuvo",
    "Qué cambió después",
    "Lo que haría hoy",
    "Evidencia interna",
]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError("Falta front matter inicial")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("Front matter sin cierre ---") from exc
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"\'')
    return meta, body


def meaningful_section(body: str, heading: str) -> bool:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)", re.MULTILINE
    )
    match = pattern.search(body)
    if not match:
        return False
    content = match.group(1)
    content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
    content = re.sub(r"\[\[[^\]]+\]\]", "", content)
    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+", content)
    return len(words) >= 3


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    missing = sorted(REQUIRED_META - meta.keys())
    if missing:
        errors.append("Faltan metadatos: " + ", ".join(missing))

    variant = meta.get("content_variant", "")
    if variant not in VALID_VARIANTS:
        errors.append(f"content_variant inválido: {variant!r}")

    spoiler = meta.get("spoiler_level", "")
    if spoiler not in VALID_SPOILERS:
        errors.append(f"spoiler_level inválido: {spoiler!r}")

    status = meta.get("status", "")
    if status not in {"draft", "review", "published", "archived"}:
        errors.append(f"status inválido: {status!r}")

    title = meta.get("title", "").strip()
    if re.fullmatch(r"(?i)decisi[oó]n\s*\d+", title):
        errors.append("Título genérico: describe la decisión concreta")

    third_party = meta.get("contains_third_party_editorial_text", "").lower() == "true"
    permission = meta.get("editorial_permission", "")
    if permission not in {"not_applicable", "granted", "pending"}:
        errors.append(f"editorial_permission inválido: {permission!r}")
    if third_party and permission != "granted":
        errors.append("Incluye texto editorial de tercero sin permiso granted")

    if status == "published":
        for key in ("book_slug", "public_slug", "title", "source_evidence", "last_verified"):
            if not meta.get(key, "").strip():
                errors.append(f"Publicado sin {key}")
        if "[[pendiente" in text.lower():
            errors.append("Publicado con marcadores [[pendiente]]")
        for section in REQUIRED_SECTIONS:
            if not meaningful_section(body, section):
                errors.append(f"Sección ausente o vacía: {section}")

    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: validate-writing-decision.py <borrador.md> [...]", file=sys.stderr)
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
