#!/usr/bin/env python3
"""Valida oportunidades verificadas y genera página estática, JSON público y calendario ICS."""
from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date, timedelta
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto  # noqa: E402

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

def render_page_body(items, today):
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
    return f'''<!DOCTYPE html>
<html lang="es" class="v1">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
  <meta name="robots" content="index,follow,max-image-preview:large">
  <title>{TITLE}</title>
  <meta name="description" content="{DESCRIPTION}">
  <meta property="og:title" content="{TITLE}">
  <meta property="og:description" content="{DESCRIPTION}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{CANONICAL}">
  <meta property="og:image" content="{SHARE_IMAGE}">
  <meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}">
  <meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}">
  <meta property="og:image:alt" content="{TITLE}">
  <meta property="og:locale" content="es_ES">
  <meta property="og:site_name" content="David Porto Díaz">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{TITLE}">
  <meta name="twitter:description" content="{DESCRIPTION}">
  <meta name="twitter:image" content="{SHARE_IMAGE}">
  <meta name="twitter:image:alt" content="{TITLE}">
  <meta name="theme-color" content="#F4EFE7" />
  <link rel="canonical" href="{CANONICAL}">
  <link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />
  <link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />
  <link rel="manifest" href="/manifest.json" />

  <link rel="stylesheet" href="/assets/v1-fonts.css" />
  <link rel="stylesheet" href="/assets/v1-tokens.css" />
  <link rel="stylesheet" href="/assets/v1-base.css" />
  <link rel="stylesheet" href="/assets/v1-shell.css" />
  <link rel="stylesheet" href="/assets/v1-components.css" />
  <link rel="stylesheet" href="/assets/v1-families.css" />
  <link rel="stylesheet" href="/assets/v1-tools.css" />
  <link rel="stylesheet" href="/assets/radar-convocatorias.css">
  <script type="application/ld+json">{schema}</script>
</head>
<body>
  <a href="#contenido" class="skip-link">Saltar al contenido</a>

  <header class="site-header" data-header>
    <div class="site-header__inner">
      <a class="brand" href="/" aria-label="David Porto Díaz — inicio">
        <span class="brand__name">David Porto Díaz</span>
        <span class="brand__role">Escritor</span>
      </a>
      <nav class="primary-nav" aria-label="Navegación principal">
        <a href="/libros/">Obra</a>
        <a href="/cuaderno/">Cuaderno</a>
        <a href="/herramientas/" aria-current="page">Herramientas</a>
      </nav>
      <button class="explore-trigger" type="button" aria-haspopup="dialog" aria-controls="explore-dialog" aria-expanded="false" data-explore-open>
        Explorar
      </button>
    </div>
  </header>

  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog>
    <div class="explore-dialog__shell">
      <div class="explore-dialog__head">
        <div>
          <p class="eyebrow">Índice general</p>
          <h2 id="explore-title">Explorar</h2>
        </div>
        <button class="icon-button" type="button" aria-label="Cerrar Explorar" data-explore-close>
          <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path d="M5 5l14 14M19 5L5 19"/></svg>
        </button>
      </div>
      <div class="explore-dialog__grid">
        <nav class="explore-list" aria-label="Destinos de la web">
          <a class="explore-row" href="/las-manecillas-del-recuerdo/" data-preview="manecillas"><span class="explore-row__index">01</span><span class="explore-row__body"><strong>Las manecillas del recuerdo</strong><small>La obra actual.</small></span></a>
          <a class="explore-row" href="/autor.html" data-preview="autor"><span class="explore-row__index">02</span><span class="explore-row__body"><strong>Autor</strong><small>Biografía, obra y trayectoria.</small></span></a>
          <a class="explore-row" href="/libros/samuel-entre-mundos/" data-preview="samuel"><span class="explore-row__index">03</span><span class="explore-row__body"><strong>Samuel entre mundos</strong><small>Primera novela publicada.</small></span></a>
          <a class="explore-row" href="/cuaderno/" data-preview="cuaderno"><span class="explore-row__index">04</span><span class="explore-row__body"><strong>Cuaderno</strong><small>Artículos y piezas editoriales.</small></span></a>
          <a class="explore-row" href="/herramientas/" data-preview="herramientas"><span class="explore-row__index">05</span><span class="explore-row__body"><strong>Herramientas</strong><small>Utilidades gratuitas para escritores.</small></span></a>
          <a class="explore-row" href="/prensa.html" data-preview="prensa"><span class="explore-row__index">06</span><span class="explore-row__body"><strong>Prensa y eventos</strong><small>Apariciones, materiales y agenda.</small></span></a>
        </nav>
        <aside class="explore-preview" aria-live="polite" aria-atomic="true" data-explore-preview>
          <div class="explore-preview__media" aria-hidden="true" data-preview-media></div>
          <p class="explore-preview__label" data-preview-label>Herramientas</p>
          <p class="explore-preview__copy" data-preview-copy>Utilidades gratuitas para escritores.</p>
        </aside>
      </div>
    </div>
  </dialog>

  <main id="contenido" tabindex="-1" class="v1-main" data-family="tool">
    <nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/herramientas/">Herramientas</a></li><li aria-current="page">Convocatorias</li></ol></nav>

    <header class="tool-hero">
      <p class="eyebrow">Radar para escritores · fuentes verificadas</p>
      <h1>Convocatorias que todavía están a tiempo.</h1>
      <p class="tool-hero__lead">Concursos, premios, ayudas, becas, residencias y vías de envío de manuscritos revisadas contra la fuente oficial. Se ocultan automáticamente cuando vencen o la verificación supera 30 días.</p>
      <p class="tool-note"><strong>Importante:</strong> esta web no organiza estas convocatorias ni garantiza que sigan abiertas después de la fecha mostrada. Confirma siempre en la fuente oficial antes de enviar.</p>
      <p class="tool-hero__actions"><a class="button secondary" data-radar-calendar href="/convocatorias-escritores/deadlines.ics" download="convocatorias-escritores.ics">Añadir fechas a mi calendario</a></p>
    </header>

    <noscript><p class="tool-note" role="status">JavaScript está desactivado. La lista completa y sus fuentes siguen visibles, pero los filtros y la búsqueda necesitan JavaScript.</p></noscript>

    <section class="tool-finder" aria-label="Filtrar convocatorias">
      <div class="tool-options">
        <div class="tool-field"><label class="tool-field-label" for="radar-search">Buscar</label><input class="tool-input" id="radar-search" type="search" data-radar-search placeholder="Entidad, premio, género…"></div>
        <div class="tool-field"><label class="tool-field-label" for="radar-type">Tipo</label><select class="tool-select" id="radar-type" data-radar-type><option value="">Todos</option>{options(types)}</select></div>
        <div class="tool-field"><label class="tool-field-label" for="radar-genre">Género</label><select class="tool-select" id="radar-genre" data-radar-genre><option value="">Todos</option>{options(genres)}</select></div>
      </div>
      <label class="tool-check"><input type="checkbox" data-radar-soon> <span>Cierra en 7 días</span></label>
      <div class="tool-actions"><button type="button" class="text-action" data-radar-clear>Limpiar</button></div>
      <p class="tool-count" role="status" aria-live="polite" data-radar-count>{len(active)} convocatorias verificadas</p>
    </section>

    <section class="radar-grid" data-radar-grid>{cards}</section>
    <div class="radar-empty" data-radar-filter-empty hidden><p>No hay coincidencias con estos filtros.</p><button type="button" class="button secondary" data-radar-empty-clear>Limpiar filtros</button></div>

    <section class="v1-section">
      <div class="tool-findings-block"><h2>Cómo se mantiene este radar</h2><p>Una lista de fuentes oficiales se revisa para detectar posibles cambios y nuevas convocatorias. Nada se publica automáticamente: una oportunidad solo aparece después de revisar la fuente oficial, su fecha límite y sus condiciones básicas. Una convocatoria activa que lleva más de 30 días sin volver a comprobarse deja de mostrarse aquí aunque su plazo siga abierto.</p></div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="site-footer__grid">
      <div>
        <strong class="brand__name">David Porto Díaz</strong>
        <p>Autor de Las manecillas del recuerdo y Samuel entre mundos.</p>
        <div class="social-row">
          <a class="social-icon" href="https://www.instagram.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.3" cy="6.7" r="0.6" fill="currentColor" stroke="none"/></svg></a>
          <a class="social-icon" href="https://www.facebook.com/profile.php?id=61590793667301" target="_blank" rel="noopener noreferrer me" aria-label="Facebook" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M16.7 3H7.3A4.3 4.3 0 0 0 3 7.3v9.4A4.3 4.3 0 0 0 7.3 21h4.2v-6.6H9.4v-2.6h2.1V9.8c0-2.1 1.3-3.3 3.2-3.3.9 0 1.7.1 1.9.1v2.2h-1.3c-1 0-1.2.5-1.2 1.2v1.7h2.4l-.3 2.6h-2.1V21h2.6a4.3 4.3 0 0 0 4.3-4.3V7.3A4.3 4.3 0 0 0 16.7 3z"/></svg></a>
          <a class="social-icon" href="https://www.tiktok.com/@davidportoescritor" target="_blank" rel="noopener noreferrer me" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M14 3c.4 2.2 2 3.8 4.2 4.1v2.7c-1.5 0-2.9-.4-4.1-1.2v6.1a4.9 4.9 0 1 1-4.2-4.9v2.7a2.2 2.2 0 1 0 1.6 2.1V3h2.5z"/></svg></a>
          <a class="social-icon" href="https://www.threads.net/@davidportodiaz" target="_blank" rel="noopener noreferrer me" aria-label="Threads" title="Threads"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><path d="M12 21c4.4 0 7-2.8 7-7.5C19 8 16.5 4 12 4 8 4 5.5 6.8 5.5 11c0 3 1.8 4.8 4.3 4.8 2 0 3.4-1.2 3.4-3 0-1.4-.9-2.3-2.1-2.3-.9 0-1.5.5-1.7 1.2"/></svg></a>
          <a class="social-icon" href="https://bsky.app/profile/davidportoescritor.bsky.social" target="_blank" rel="noopener noreferrer me" aria-label="Bluesky" title="Bluesky"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 7c-1.6-2.3-4.6-3.6-6.7-3.2-.3 2.3.4 5.4 2 7.1-1.6.1-2.8.8-3 1.7.7.9 2.3 1.3 3.8 1-.9 1.1-1.1 2.6-.5 3.8 1.6.1 3.7-1.1 4.6-2.8.4 1 .9 1.9 1.5 2.6.6-.7 1.1-1.6 1.5-2.6.9 1.7 3 2.9 4.6 2.8.6-1.2.4-2.7-.5-3.8 1.5.3 3.1-.1 3.8-1-.2-.9-1.4-1.6-3-1.7 1.6-1.7 2.3-4.8 2-7.1-2.1-.4-5.1.9-6.7 3.2-.2.3-.4.6-.5 1-.1-.4-.3-.7-.5-1z"/></svg></a>
          <a class="social-icon" href="https://www.pinterest.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Pinterest" title="Pinterest"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 2C6.5 2 3 5.6 3 10c0 3.2 1.8 5.1 3 5.7.2.1.4 0 .4-.3l.4-1.5c0-.2 0-.3-.1-.5-.4-.5-.7-1.4-.7-2.3 0-3 2.2-5.7 5.8-5.7 3.1 0 4.9 1.9 4.9 4.5 0 3.4-1.5 5.6-3.5 5.6-1.1 0-2-.9-1.7-2.1.3-1.3.9-2.7.9-3.7 0-.8-.5-1.5-1.4-1.5-1.1 0-2 1.2-2 2.7 0 1 .3 1.7.3 1.7s-1.2 4.9-1.4 5.8c-.4 1.6-.1 3.6 0 3.8.1.1.2.1.3 0 .1-.2 1.5-1.9 2-3.5.1-.4.6-2.3.6-2.3.3.6 1.2 1.1 2.2 1.1 2.9 0 5-2.7 5-6.4C20 5.7 16.5 2 12 2z"/></svg></a>
          <a class="social-icon" href="https://www.linkedin.com/in/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM3.5 9h3v12h-3V9zm6.5 0h2.9v1.6c.5-.9 1.7-1.9 3.4-1.9 3.6 0 4.6 2.3 4.6 5.4V21h-3v-6.1c0-1.5-.5-2.5-1.9-2.5-1.4 0-2 1-2 2.4V21h-3V9z"/></svg></a>
          <a class="text-action" href="https://www.goodreads.com/author/show/66843136.David_Porto_D_az" target="_blank" rel="noopener noreferrer">Goodreads</a>
        </div>
      </div>
      <nav aria-label="Obra"><h2>Obra</h2><a href="/las-manecillas-del-recuerdo/">Las manecillas del recuerdo</a><a href="/libros/samuel-entre-mundos/">Samuel entre mundos</a><a href="/fragmento/">Fragmento gratis</a></nav>
      <nav aria-label="Leer y recursos"><h2>Leer</h2><a href="/cuaderno/">Cuaderno</a><a href="/herramientas/" aria-current="page">Herramientas</a><a href="/mapa-del-sitio/">Mapa del sitio</a></nav>
      <nav aria-label="Información"><h2>Información</h2><a href="/autor.html">Autor</a><a href="/prensa.html">Prensa</a><a href="/eventos.html">Eventos</a><a href="/privacidad.html">Privacidad</a><a href="/aviso-legal.html">Aviso legal</a><a href="/ai/">Para IA</a></nav>
    </div>
  </footer>

  <script defer src="/assets/v1-shell.js"></script>
  <script src="/assets/radar-convocatorias.js" defer></script>
</body>
</html>'''

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

def build_html(items, today):
    """Pagina completa del radar, con el shell generado desde el contrato.

    El shell ya no vive en la plantilla de este fichero: lo pone
    scripts/build-site-shell.py desde data/navigation.json, igual que en el
    resto del sitio. Ver scripts/site_shell.py.
    """
    return inject_shell_auto(render_page_body(items, today))


if __name__ == "__main__":
    main()
