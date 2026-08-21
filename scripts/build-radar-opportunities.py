#!/usr/bin/env python3
"""Valida oportunidades verificadas y genera página estática, JSON público y calendario ICS."""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

STALE_DAYS = 30
TITLE = "Convocatorias para escritores: concursos, becas y manuscritos | David Porto Díaz"
DESCRIPTION = "Radar de concursos, premios, becas, ayudas y convocatorias para escritores, verificados contra su fuente oficial y ordenados por fecha límite."
CANONICAL = "https://davidportodiaz.com/convocatorias-escritores/"
SHARE_IMAGE = "https://davidportodiaz.com/assets/david-porto-imagen-compartir.webp"
SHARE_IMAGE_WIDTH = 1731
SHARE_IMAGE_HEIGHT = 909
ALLOWED_TYPES = {"concurso", "premio", "ayuda", "beca", "residencia", "manuscritos"}
REQ = {"id", "title", "type", "organizer", "deadline", "genres", "source_url", "verified_at", "published", "fee_eur"}
FORBIDDEN_URL = re.compile(r"[\s\\\x00-\x1f\x7f<>\"{}|^`]")

def iso_date(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field}: debe ser string ISO")
    try:
        return date.fromisoformat(value)
    except Exception as exc:
        raise ValueError(f"{field}: fecha ISO inválida: {value!r}") from exc

def esc(value):
    return html.escape(str(value or ""), quote=True)

def slug_ok(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", value))

def https_url(value):
    if not isinstance(value, str) or not value or FORBIDDEN_URL.search(value):
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    try:
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and port in (None, 443)
    )

def validate(item):
    if not isinstance(item, dict):
        raise ValueError("cada oportunidad debe ser un objeto")
    missing = REQ - set(item)
    if missing:
        raise ValueError(f"{item.get('id', '?')}: faltan {sorted(missing)}")
    if not slug_ok(item["id"]):
        raise ValueError(f"id inválido: {item['id']!r}")
    for field in ("title", "organizer"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise ValueError(f"{item['id']}: {field} vacío")
    if item["type"] not in ALLOWED_TYPES:
        raise ValueError(f"{item['id']}: type no permitido")
    if not https_url(item["source_url"]):
        raise ValueError(f"{item['id']}: source_url HTTPS inválida")
    if not isinstance(item["genres"], list) or not item["genres"] or not all(isinstance(g, str) and g.strip() for g in item["genres"]):
        raise ValueError(f"{item['id']}: genres inválido")
    if not isinstance(item["published"], bool):
        raise ValueError(f"{item['id']}: published debe ser boolean")
    fee = item["fee_eur"]
    if fee is not None and (isinstance(fee, bool) or not isinstance(fee, (int, float)) or fee < 0):
        raise ValueError(f"{item['id']}: fee_eur debe ser número >= 0 o null cuando la fuente no indica tasa")
    iso_date(item["deadline"], "deadline")
    iso_date(item["verified_at"], "verified_at")

def state(item, today):
    deadline = iso_date(item["deadline"], "deadline")
    verified = iso_date(item["verified_at"], "verified_at")
    if deadline < today:
        return "expired"
    if today - verified > timedelta(days=STALE_DAYS):
        return "stale"
    if (deadline - today).days <= 7:
        return "closing_soon"
    return "open"

def fee_label(item):
    fee = item["fee_eur"]
    if fee is None:
        return "No indicado en la fuente oficial"
    if fee == 0:
        return "Sin tasa"
    return f"{fee:g} €"

def card(item):
    genres = ", ".join(item["genres"])
    prize = f'<div><dt>Premio/ayuda</dt><dd>{esc(item.get("prize"))}</dd></div>' if item.get("prize") else ""
    note = f'<p class="radar-note">{esc(item.get("editorial_note"))}</p>' if item.get("editorial_note") else ""
    deadline_label = iso_date(item["deadline"], "deadline").strftime("%d/%m/%Y")
    verified_label = iso_date(item["verified_at"], "verified_at").strftime("%d/%m/%Y")
    return f'''<article class="radar-card" data-radar-item data-type="{esc(item['type'])}" data-genres="{esc('|'.join(item['genres']).lower())}" data-title="{esc(item['title'].lower())}" data-organizer="{esc(item['organizer'].lower())}" data-deadline="{esc(item['deadline'])}" data-verified-at="{esc(item['verified_at'])}">
<div class="radar-card__top"><span class="radar-badge" data-radar-status>Plazo verificado</span><span>{esc(item['type'].capitalize())}</span></div>
<h2>{esc(item['title'])}</h2><p class="radar-org">{esc(item['organizer'])}</p>
<dl><div><dt>Fecha límite</dt><dd><time datetime="{esc(item['deadline'])}">{deadline_label}</time><span class="radar-relative" data-radar-relative aria-hidden="true"></span></dd></div><div><dt>Géneros</dt><dd>{esc(genres)}</dd></div><div><dt>Coste</dt><dd>{esc(fee_label(item))}</dd></div>{prize}</dl>
{note}
<p class="radar-verified">Verificado: <time datetime="{esc(item['verified_at'])}">{verified_label}</time></p>
<p><a class="button secondary" data-radar-source data-radar-source-type="{esc(item['type'])}" href="{esc(item['source_url'])}" target="_blank" rel="noopener noreferrer">Ver fuente oficial</a></p></article>'''

def active_items(items, today):
    active = [item for item in items if item.get("published") and state(item, today) in {"open", "closing_soon"}]
    return sorted(active, key=lambda item: item["deadline"])

def build_html(items, today):
    active = active_items(items, today)
    cards = "\n".join(card(item) for item in active) or '<p data-radar-empty>No hay oportunidades verificadas activas ahora mismo.</p>'
    types = sorted({item["type"] for item in active})
    genres = sorted({genre for item in active for genre in item["genres"]})
    options = lambda values: "\n".join(f'<option value="{esc(value)}">{esc(value.capitalize())}</option>' for value in values)
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Convocatorias para escritores",
        "url": CANONICAL,
        "inLanguage": "es",
        "isPartOf": {"@id": "https://davidportodiaz.com/#website"},
    }, ensure_ascii=False, separators=(",", ":"))
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{TITLE}</title><meta name="description" content="{DESCRIPTION}"><meta property="og:title" content="{TITLE}"><meta property="og:description" content="{DESCRIPTION}"><meta property="og:type" content="website"><meta property="og:url" content="{CANONICAL}"><meta property="og:image" content="{SHARE_IMAGE}"><meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}"><meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}"><meta property="og:image:alt" content="{TITLE}"><meta property="og:locale" content="es_ES"><meta property="og:site_name" content="David Porto Díaz"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{TITLE}"><meta name="twitter:description" content="{DESCRIPTION}"><meta name="twitter:image" content="{SHARE_IMAGE}"><meta name="twitter:image:alt" content="{TITLE}"><link rel="canonical" href="{CANONICAL}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="stylesheet" href="/styles.css?v=202609-launch-1"><link rel="stylesheet" href="/assets/radar-convocatorias.css"><script type="application/ld+json">{schema}</script></head><body><a href="#main-content" class="skip-link">Saltar al contenido</a><main id="main-content" tabindex="-1" class="radar-page"><nav class="breadcrumb" aria-label="Ruta de navegación"><a href="/">Inicio</a> › <a href="/herramientas/">Herramientas</a> › Convocatorias</nav><header class="radar-hero"><p class="eyebrow">Radar para escritores · fuentes verificadas</p><h1>Convocatorias que todavía están a tiempo.</h1><p class="lead">Concursos, premios, ayudas, becas, residencias y recepción de manuscritos. Cada ficha enlaza la fuente oficial y muestra cuándo se comprobó.</p><p><a data-radar-calendar href="/convocatorias-escritores/deadlines.ics" download="convocatorias-escritores.ics">Añadir fechas a mi calendario</a></p></header><noscript><p class="radar-note" role="status">JavaScript está desactivado. La lista completa y sus fuentes siguen visibles, pero los filtros y la búsqueda necesitan JavaScript.</p></noscript><section class="radar-filters" aria-label="Filtrar convocatorias"><label>Buscar <input type="search" data-radar-search autocomplete="off" placeholder="Título u organizador"></label><label>Tipo <select data-radar-type><option value="">Todos</option>{options(types)}</select></label><label>Género <select data-radar-genre><option value="">Todos</option>{options(genres)}</select></label><label class="radar-check"><input type="checkbox" data-radar-soon> Cierra en 7 días</label><button type="button" class="button secondary" data-radar-clear>Limpiar</button></section><p class="radar-count" role="status" aria-live="polite" data-radar-count>{len(active)} convocatorias verificadas</p><section class="radar-grid" data-radar-grid>{cards}</section><div class="radar-empty" data-radar-filter-empty hidden><p>No hay coincidencias con estos filtros.</p><button type="button" class="button secondary" data-radar-empty-clear>Limpiar filtros</button></div><section class="radar-method"><h2>Cómo se mantiene este radar</h2><p>Una lista de fuentes oficiales se revisa para detectar posibles cambios y nuevas convocatorias. Nada se publica automáticamente: una oportunidad solo aparece después de revisar la fuente oficial, su fecha límite y sus condiciones básicas. Una convocatoria activa que lleva más de 30 días sin volver a comprobarse deja de mostrarse aquí aunque su plazo siga abierto.</p></section></main><script src="/assets/radar-convocatorias.js" defer></script></body></html>'''

def ics_escape(value):
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")

def fold_ics_line(line):
    chunks = []
    current = ""
    for char in line:
        candidate = current + char
        if len(candidate.encode("utf-8")) > 75:
            chunks.append(current)
            current = " " + char
        else:
            current = candidate
    chunks.append(current)
    return "\r\n".join(chunks)

def build_ics(items, today):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//David Porto Diaz//Radar escritores//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Convocatorias para escritores",
    ]
    for item in active_items(items, today):
        deadline = iso_date(item["deadline"], "deadline")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{item['id']}@davidportodiaz.com",
            f"DTSTART;VALUE=DATE:{deadline:%Y%m%d}",
            f"DTEND;VALUE=DATE:{deadline + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{ics_escape(item['title'])}",
            f"DESCRIPTION:{ics_escape(item['organizer'])}",
            f"URL:{item['source_url']}",
            "END:VEVENT",
        ])
    lines.extend(["END:VCALENDAR", ""])
    return "\r\n".join(fold_ics_line(line) for line in lines)

def public_json(items, today):
    return json.dumps({"generated_for": today.isoformat(), "items": active_items(items, today)}, ensure_ascii=False, indent=2) + "\n"

def load_items(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("dataset: se esperaba objeto con items[]")
    items = payload["items"]
    ids = set()
    for item in items:
        validate(item)
        if item["id"] in ids:
            raise ValueError(f"id duplicado: {item['id']}")
        ids.add(item["id"])
    return items

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    items = load_items(args.data)
    today = iso_date(args.today, "today")
    if args.check:
        states = {name: sum(state(item, today) == name and item.get("published") for item in items) for name in ("open", "closing_soon", "stale", "expired")}
        print(f"OK items={len(items)} active={states['open'] + states['closing_soon']} stale={states['stale']} expired={states['expired']}")
        return
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(build_html(items, today), encoding="utf-8")
    (out / "opportunities.json").write_text(public_json(items, today), encoding="utf-8")
    (out / "deadlines.ics").write_text(build_ics(items, today), encoding="utf-8", newline="")
    active = len(active_items(items, today))
    print(f"built active={active} hidden={len(items) - active}")

if __name__ == "__main__":
    main()
