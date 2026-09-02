#!/usr/bin/env python3
"""Build a static, verified publisher directory for davidportodiaz.com.

This builder only accepts an explicitly public JSON schema. It is designed to
fail if private editorial-research fields are accidentally copied into it.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto  # noqa: E402

STATUS_LABELS = {
    "open": "Acepta manuscritos",
    "closed": "Recepción cerrada",
    "indirect": "Vía indirecta",
    "award_only": "Solo convocatoria/premio",
    "unknown": "Estado por verificar",
}
STATUS_ORDER = {"open": 0, "award_only": 1, "indirect": 2, "closed": 3, "unknown": 4}
ALLOWED_STATUS = set(STATUS_LABELS)
FORBIDDEN_KEY_PARTS = {
    "ranking",
    "tier",
    "encaje",
    "encaje_noa",
    "prioridad",
    "estado_envio",
    "estado_de_envio",
    "fecha_envio",
    "fecha_de_envio",
    "proxima_accion",
    "notas_privadas",
    "noa",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ValidationError(Exception):
    pass


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def norm_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def parse_iso_date(value: str, field: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field}: fecha inválida {value!r}; usa YYYY-MM-DD") from exc


def require_https(value: str | None, field: str) -> None:
    if not value:
        raise ValidationError(f"{field}: URL obligatoria")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationError(f"{field}: debe ser una URL HTTPS absoluta: {value!r}")


def scan_forbidden_keys(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = norm_key(str(key))
            if normalized in FORBIDDEN_KEY_PARTS or any(
                part and part in normalized for part in FORBIDDEN_KEY_PARTS
            ):
                raise ValidationError(
                    f"Campo privado/prohibido detectado en {path}.{key}. "
                    "No exportes la hoja privada directamente."
                )
            scan_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_forbidden_keys(child, f"{path}[{index}]")


def validate_record(record: dict, seen: set[str], today: date) -> list[str]:
    warnings: list[str] = []
    required = [
        "slug", "name", "group", "publisher_type", "country", "genres", "status",
        "direct_submission", "submission_channel", "submission_url", "website_url",
        "requirements", "summary", "public_note", "verified_at", "page_updated_at",
        "sources", "history",
    ]
    missing = [key for key in required if key not in record]
    if missing:
        raise ValidationError(f"{record.get('name', '<sin nombre>')}: faltan campos {', '.join(missing)}")

    slug = record["slug"]
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise ValidationError(f"slug inválido: {slug!r}")
    if slug in seen:
        raise ValidationError(f"slug duplicado: {slug}")
    seen.add(slug)

    if record["status"] not in ALLOWED_STATUS:
        raise ValidationError(f"{slug}: status debe ser uno de {sorted(ALLOWED_STATUS)}")
    if not isinstance(record["direct_submission"], bool):
        raise ValidationError(f"{slug}: direct_submission debe ser booleano")
    if record["status"] == "closed" and record.get("submission_email"):
        raise ValidationError(
            f"{slug}: no publiques submission_email mientras la recepción esté cerrada; "
            "evita reutilizar correos históricos."
        )
    if record.get("submission_email") and not EMAIL_RE.fullmatch(record["submission_email"]):
        raise ValidationError(f"{slug}: submission_email inválido")

    require_https(record["submission_url"], f"{slug}.submission_url")
    require_https(record["website_url"], f"{slug}.website_url")

    genres = record["genres"]
    if not isinstance(genres, list) or not genres or not all(isinstance(g, str) and g.strip() for g in genres):
        raise ValidationError(f"{slug}: genres debe ser una lista no vacía de textos")
    requirements = record["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise ValidationError(f"{slug}: requirements debe ser una lista no vacía")
    if len(record["summary"].strip()) < 80:
        raise ValidationError(f"{slug}: summary demasiado breve; debe aportar contexto propio")
    if len(record["public_note"].strip()) < 40:
        raise ValidationError(f"{slug}: public_note demasiado breve")

    verified = parse_iso_date(record["verified_at"], f"{slug}.verified_at")
    parse_iso_date(record["page_updated_at"], f"{slug}.page_updated_at")
    age = (today - verified).days
    if age > 90:
        warnings.append(f"{slug}: verificación antigua ({age} días); mostrar aviso y revisar antes de enviar")
    if verified > today:
        raise ValidationError(f"{slug}: verified_at está en el futuro")

    sources = record["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValidationError(f"{slug}: sources debe contener al menos una fuente")
    if not any(source.get("primary") is True for source in sources if isinstance(source, dict)):
        raise ValidationError(f"{slug}: se exige al menos una fuente primaria")
    for idx, source in enumerate(sources):
        if not isinstance(source, dict) or not source.get("label"):
            raise ValidationError(f"{slug}.sources[{idx}]: label obligatorio")
        require_https(source.get("url"), f"{slug}.sources[{idx}].url")

    history = record["history"]
    if not isinstance(history, list) or not history:
        raise ValidationError(f"{slug}: history debe contener al menos una comprobación/cambio")
    for idx, event in enumerate(history):
        if not isinstance(event, dict) or not event.get("event"):
            raise ValidationError(f"{slug}.history[{idx}]: event obligatorio")
        parse_iso_date(event.get("date"), f"{slug}.history[{idx}].date")
        require_https(event.get("source_url"), f"{slug}.history[{idx}].source_url")

    if record.get("publish") is not True:
        warnings.append(f"{slug}: publish no es true; no se generará")
    return warnings


def load_and_validate(path: Path, today: date) -> tuple[dict, list[dict], list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    scan_forbidden_keys(raw)
    if raw.get("version") != 1:
        raise ValidationError("version debe ser 1")
    require_https(raw.get("site"), "site")
    records = raw.get("publishers")
    if not isinstance(records, list) or not records:
        raise ValidationError("publishers debe ser una lista no vacía")
    seen: set[str] = set()
    warnings: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise ValidationError("cada publisher debe ser un objeto")
        warnings.extend(validate_record(record, seen, today))
    published = [record for record in records if record.get("publish") is True]
    published.sort(key=lambda r: (STATUS_ORDER[r["status"]], r["name"].casefold()))
    return raw, published, warnings


SHARE_IMAGE = "https://davidportodiaz.com/assets/david-porto-imagen-compartir.jpg"
# Dimensiones reales del fichero, no las recomendadas. check-social-cards.py
# compara lo declarado con los bytes de la imagen y marca dimension-drift si no
# coinciden: declarar 1200x630 "porque es lo que pide Open Graph" seria mentir
# sobre un fichero que mide otra cosa.
SHARE_IMAGE_WIDTH = 1731
SHARE_IMAGE_HEIGHT = 909
SHARE_IMAGE_ALT = "David Porto Díaz, autor de Samuel entre mundos y Las manecillas del recuerdo"


def page_shell(*, title: str, description: str, canonical: str, main_html: str, jsonld: dict, js: bool = False, extra_css: str = "") -> str:
        # El shell (cabecera, Explorar y pie) no se escribe aqui: lo genera
        # scripts/build-site-shell.py desde data/navigation.json, igual que en las
        # 59 paginas escritas a mano. Las cadenas literales que habia debajo eran
        # una cuarta copia del shell y se quedaron atras en cuanto el shell paso a
        # generarse. Ver scripts/site_shell.py.
        script = '<script src="/assets/editoriales.js?v=1" defer></script>' if js else ""
        return f'''<!DOCTYPE html>
<html lang="es" class="v1">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-src 'none'">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <meta name="author" content="David Porto Díaz">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{esc(canonical)}">
    <meta property="og:site_name" content="David Porto Díaz">
    <meta property="og:locale" content="es_ES">
    <meta property="og:image" content="{SHARE_IMAGE}">
    <meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}">
    <meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}">
    <meta property="og:image:alt" content="{esc(SHARE_IMAGE_ALT)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(description)}">
    <meta name="twitter:image" content="{SHARE_IMAGE}">
    <meta name="twitter:image:alt" content="{esc(SHARE_IMAGE_ALT)}">
    <meta name="theme-color" content="#ffffff" />
    <link rel="canonical" href="{esc(canonical)}" />
    <link rel="icon" type="image/png" href="/assets/david-porto-favicon.png" />
    <link rel="apple-touch-icon" href="/assets/david-porto-favicon.png" />
    <link rel="manifest" href="/manifest.json" />

    <link rel="stylesheet" href="/assets/v1-fonts.css?v=1" />
    <link rel="stylesheet" href="/assets/v1-tokens.css?v=1" />
    <link rel="stylesheet" href="/assets/v1-base.css?v=1" />
    <!-- v1-shell-preload:start (generated by scripts/add_v1_shell_preloads.py -- do not edit by hand) -->
    <link rel="preload" as="style" href="/assets/v1-shell-base.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-shell-lrb-v2.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-lrb-material-v2.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-home-editorial-v3.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-editorial-interior-v4.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-editorial-interactions-v4.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-site-cohesion-v6.css?v=1" />
    <link rel="preload" as="style" href="/assets/v1-reflow-hardening-v7.css?v=1" />
    <!-- v1-shell-preload:end -->
    <link rel="stylesheet" href="/assets/v1-shell.css?v=1" />
    <link rel="stylesheet" href="/assets/v1-components.css?v=2" />
    <link rel="stylesheet" href="/assets/v1-families.css?v=1" />
    <link rel="stylesheet" href="/assets/v1-tools.css?v=1" />
    <link rel="stylesheet" href="/assets/editoriales.css?v=1" />{"" if not extra_css else chr(10) + "    " + extra_css}
    <script type="application/ld+json">{html.escape(json.dumps(jsonld, ensure_ascii=False, separators=(',', ':')), quote=False)}</script>
</head>

<body>
    <a href="#contenido" class="skip-link">Saltar al contenido</a>

    <header class="site-header" data-header></header>

    <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog></dialog>

{main_html}

    <footer class="site-footer"></footer>

    <script defer src="/assets/v1-shell.js?v=1"></script>
    {script}
</body>
</html>
'''


def breadcrumbs(items: list[tuple[str, str | None]]) -> str:
    rendered = []
    for label, url in items:
        rendered.append(f'<li><a href="{esc(url)}">{esc(label)}</a></li>' if url else f'<li aria-current="page">{esc(label)}</li>')
    return '<nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol>' + ''.join(rendered) + '</ol></nav>'


def breadcrumb_jsonld(base: str, items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label, "item": url}
            for i, (label, url) in enumerate(items)
        ],
    }


def status_badge(record: dict) -> str:
    cls = "open" if record["status"] == "open" else "closed" if record["status"] == "closed" else "neutral"
    return f'<span class="editorial-badge editorial-badge--{cls}">{esc(STATUS_LABELS[record["status"]])}</span>'


def stale(record: dict, today: date) -> bool:
    return (today - parse_iso_date(record["verified_at"], "verified_at")).days > 90


def render_index(site: str, records: list[dict], today: date) -> str:
    genres = sorted({genre for r in records for genre in r["genres"]}, key=str.casefold)
    cards = []
    for r in records:
        genres_pipe = "|".join(r["genres"])
        tags = "".join(f'<span class="editorial-genre">{esc(g)}</span>' for g in r["genres"])
        stale_note = '<p class="tool-note">Verificación antigua: revisa la fuente oficial antes de enviar.</p>' if stale(r, today) else ""
        cards.append(f'''
<article class="id-card editorial-card" data-editorial-card data-name="{esc(r['name'])}" data-group="{esc(r['group'])}" data-genres="{esc(genres_pipe)}" data-status="{esc(r['status'])}" data-direct="{'true' if r['direct_submission'] else 'false'}">
    <div class="editorial-card__head"><div><h2><a href="/editoriales/{esc(r['slug'])}/">{esc(r['name'])}</a></h2><p class="tool-meta">{esc(r['group'])}</p></div>{status_badge(r)}</div>
  <p>{esc(r['summary'])}</p>
    <div class="editorial-genres">{tags}</div>
  <p class="editorial-verified">Comprobado: <time datetime="{esc(r['verified_at'])}">{esc(r['verified_at'])}</time></p>
  {stale_note}
    <div class="id-card__actions"><a class="text-action" href="/editoriales/{esc(r['slug'])}/">Ver requisitos y fuentes<span class="sr-only"> de {esc(r['name'])}</span></a></div>
</article>''')

    genre_options = ''.join(f'<option value="{esc(g)}">{esc(g)}</option>' for g in genres)
    canonical = f"{site}/editoriales/"
    description = "Directorio verificado de editoriales: recepción de manuscritos, requisitos, canal oficial, fecha de comprobación e historial de cambios."
    main = f'''
<main id="contenido" tabindex="-1" class="v1-main" data-family="tool" data-editoriales-directory>
  {breadcrumbs([('Inicio', '/'), ('Editoriales', None)])}
    <header class="tool-hero">
        <p class="eyebrow">Recurso para escritores</p>
        <h1>Editoriales y recepción de manuscritos, verificadas.</h1>
        <p class="tool-hero__lead">No es una lista copiada de contactos. Cada ficha separa hechos públicos, fecha de comprobación y fuente oficial para que puedas saber qué acepta una editorial y qué pide antes de enviar.</p>
        <p class="tool-note"><strong>Importante:</strong> davidportodiaz.com no representa a estas editoriales ni garantiza que una convocatoria siga abierta después de la fecha indicada. Comprueba siempre la fuente oficial antes de enviar. <a href="/metodologia-editorial/">Cómo se verifica y se corrige esta información</a>.</p>
    </header>
    <section class="tool-finder" aria-label="Filtrar editoriales">
        <div class="tool-options">
            <div class="tool-field"><label class="tool-field-label" for="editoriales-q">Buscar</label><input class="tool-input" id="editoriales-q" type="search" autocomplete="off" enterkeyhint="search" placeholder="Editorial, sello, género…" data-editoriales-search></div>
            <div class="tool-field"><label class="tool-field-label" for="editoriales-genero">Género</label><select class="tool-select" id="editoriales-genero" data-editoriales-genre><option value="">Todos</option>{genre_options}</select></div>
            <div class="tool-field"><label class="tool-field-label" for="editoriales-estado">Estado</label><select class="tool-select" id="editoriales-estado" data-editoriales-status><option value="">Todos</option><option value="open">Acepta manuscritos</option><option value="closed">Recepción cerrada</option><option value="indirect">Vía indirecta</option><option value="award_only">Solo convocatoria/premio</option><option value="unknown">Por verificar</option></select></div>
        </div>
        <label class="tool-check"><input type="checkbox" data-editoriales-direct> <span>Solo envío directo</span></label>
        <div class="tool-actions"><button class="text-action" type="button" data-editoriales-reset>Limpiar</button></div>
        <p class="tool-count"><strong data-editoriales-count role="status" aria-live="polite">{len(records)} editoriales</strong> · Los filtros se guardan en el fragmento <code>#</code>; no crean páginas SEO nuevas.</p>
  </section>
    <section class="v1-section" aria-label="Directorio de editoriales"><div class="id-cards">{''.join(cards)}</div>
    <p class="tool-note" data-editoriales-empty hidden>No hay editoriales que coincidan con esos filtros.</p>
    </section>
</main>'''
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical,
                "url": canonical,
                "name": "Editoriales y recepción de manuscritos, verificadas",
                "description": description,
                "inLanguage": "es",
                "isPartOf": {"@id": f"{site}/#website"},
                "author": {"@id": f"{site}/#author"},
            },
            breadcrumb_jsonld(site, [("Inicio", f"{site}/"), ("Editoriales", canonical)]),
        ],
    }
    return page_shell(title="Editoriales que aceptan manuscritos | David Porto Díaz", description=description, canonical=canonical, main_html=main, jsonld=jsonld, js=True)


def render_detail(site: str, record: dict, today: date) -> str:
    canonical = f"{site}/editoriales/{record['slug']}/"
    status = STATUS_LABELS[record["status"]]
    requirements = ''.join(f'<li>{esc(item)}</li>' for item in record["requirements"])
    sources = ''.join(
        f'<li><a href="{esc(source["url"])}" target="_blank" rel="noopener noreferrer">{esc(source["label"])}</a>{" · fuente primaria" if source.get("primary") else ""}</li>'
        for source in record["sources"]
    )
    history = ''.join(
        f'<li><time datetime="{esc(event["date"])}">{esc(event["date"])}</time> — {esc(event["event"])} <a href="{esc(event["source_url"])}" target="_blank" rel="noopener noreferrer">Fuente</a></li>'
        for event in sorted(record["history"], key=lambda e: e["date"], reverse=True)
    )
    genre_tags = ''.join(f'<span class="editorial-genre">{esc(g)}</span>' for g in record["genres"])
    email = record.get("submission_email")
    email_html = f'<a href="mailto:{esc(email)}">{esc(email)}</a>' if email else "No se publica un correo de envío para el estado actual."
    response = esc(record.get("response_time") or "No se publica un plazo oficial en esta ficha.")
    stale_html = '<p class="tool-note"><strong>Revisión recomendada:</strong> esta ficha lleva más de 90 días sin verificarse. Comprueba la fuente oficial antes de usar los datos.</p>' if stale(record, today) else ""
    description = f"{record['name']}: estado de recepción de manuscritos, requisitos, canal oficial, fuentes y fecha de comprobación."

    main = f'''
<main id="contenido" tabindex="-1" class="v1-main" data-family="tool">
  {breadcrumbs([('Inicio', '/'), ('Editoriales', '/editoriales/'), (record['name'], None)])}
    <header class="tool-hero"><p class="eyebrow">Ficha editorial verificada</p><h1>{esc(record['name'])}</h1><div class="editorial-genres editorial-genres--spaced">{status_badge(record)}<span class="editorial-badge">{esc(record['publisher_type'])}</span></div><p class="tool-hero__lead">{esc(record['summary'])}</p><div class="editorial-genres">{genre_tags}</div></header>
    <section class="v1-section">
        {stale_html}
        <dl class="spec-ledger"><div class="editorial-fact"><dt>Estado de originales</dt><dd>{esc(status)}</dd></div><div class="editorial-fact"><dt>Última comprobación</dt><dd><time datetime="{esc(record['verified_at'])}">{esc(record['verified_at'])}</time></dd></div><div class="editorial-fact"><dt>Canal</dt><dd>{esc(record['submission_channel'])}</dd></div><div class="editorial-fact"><dt>Correo de envío</dt><dd>{email_html}</dd></div><div class="editorial-fact"><dt>Grupo / tipo</dt><dd>{esc(record['group'])}</dd></div><div class="editorial-fact"><dt>País</dt><dd>{esc(record['country'])}</dd></div></dl>

        <div class="tool-findings-block"><h2>Qué pide ahora</h2><ul class="tool-findings">{requirements}</ul><p class="tool-actions"><a class="text-action" href="{esc(record['submission_url'])}" target="_blank" rel="noopener noreferrer">Comprobar las instrucciones oficiales</a></p></div>
        <div class="tool-findings-block"><h2>Plazo de respuesta publicado</h2><p>{response}</p></div>
        <div class="tool-findings-block"><h2>Nota editorial</h2><p>{esc(record['public_note'])}</p></div>
        <div class="tool-findings-block"><h2>Historial de comprobaciones y cambios</h2><ul class="tool-findings">{history}</ul></div>
        <div class="tool-findings-block"><h2>Fuentes</h2><ul class="tool-source-list">{sources}</ul><p class="tool-note">Esta ficha distingue siempre la fuente oficial de nuestro resumen.</p></div>
        <p class="tool-note"><strong>No es asesoramiento ni representación.</strong> Esta ficha es informativa. {esc(record['name'])} no participa en su redacción y sus instrucciones oficiales prevalecen siempre. <a href="/metodologia-editorial/">Cómo se verifica y se corrige esta información</a>.</p>
    </section>
</main>'''

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": f"{record['name']} — manuscritos y requisitos",
                "description": description,
                "dateModified": record["page_updated_at"],
                "inLanguage": "es",
                "isPartOf": {"@id": f"{site}/#website"},
                "author": {"@id": f"{site}/#author"},
                "about": {"@type": "Organization", "name": record["name"], "url": record["website_url"]},
            },
            breadcrumb_jsonld(site, [
                ("Inicio", f"{site}/"),
                ("Editoriales", f"{site}/editoriales/"),
                (record["name"], canonical),
            ]),
        ],
    }
    return page_shell(title=f"{record['name']}: manuscritos y requisitos | David Porto Díaz", description=description, canonical=canonical, main_html=main, jsonld=jsonld, extra_css='<link rel="stylesheet" href="/assets/v1-editoriales-detail.css?v=1" />')


def render_sitemap(site: str, records: list[dict]) -> str:
    rows = [(f"{site}/editoriales/", max(r["page_updated_at"] for r in records))]
    rows.extend((f"{site}/editoriales/{r['slug']}/", r["page_updated_at"]) for r in records)
    # La metodologia forma parte del directorio y el builder la genera junto al
    # resto, asi que tambien va en este sitemap parcial. El sitemap canonico
    # (sitemap.xml) ya la incluia; faltaba solo aqui.
    rows.append((f"{site}/{METHODOLOGY_SLUG}/", methodology_date_modified(records)))
    urls = ''.join(f'<url><loc>{esc(loc)}</loc><lastmod>{esc(lastmod)}</lastmod></url>' for loc, lastmod in rows)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'


METHODOLOGY_SLUG = "metodologia-editorial"

# Fecha de la ultima revision real del TEXTO de la pagina de metodologia.
# Se sube a mano cuando cambia lo que la pagina afirma.
#
# No se usa `today` para el dateModified: el contrato del doc 31 prohibe
# expresamente que una simple comprobacion aparente una actualizacion
# editorial, y con `today.isoformat()` bastaba ejecutar el builder para que la
# pagina dijera haber cambiado hoy sin haber cambiado nada. La fecha efectiva
# es el maximo entre esta revision y la ultima actualizacion real de las
# fichas, porque la pagina afirma cuantas fichas publica el directorio.
METHODOLOGY_REVISED = "2026-08-20"


def methodology_date_modified(records: list[dict]) -> str:
    """dateModified determinista: depende del contenido, no de cuando se ejecute."""
    dates = [METHODOLOGY_REVISED] + [r["page_updated_at"] for r in records]
    return max(dates)


def plural_fichas(count: int) -> str:
    """"1 ficha" / "2 fichas". Publicar "3 ficha(s)" es dejar ver el molde."""
    return f"{count} ficha" if count == 1 else f"{count} fichas"


def render_methodology(site: str, records: list[dict], today: date) -> str:
    """Página de metodología exigida por el contrato del doc 31 (bloque 11).

    Todo lo que afirma se deriva del propio validador/builder de este archivo
    o del dataset: los estados permitidos son los que valida load_and_validate,
    la caducidad de 90 días es la que aplica stale(), y la separación hoja
    privada / dataset público es la que hace safe_payload en build(). No se
    documenta ningún proceso que el código no haga de verdad.
    """
    canonical = f"{site}/{METHODOLOGY_SLUG}/"
    states = "".join(
        f"<div class=\"editorial-fact\"><dt>{esc(code)}</dt><dd>{esc(label)}</dd></div>"
        for code, label in (
            ("open", "La editorial acepta envíos directos según su propia página oficial."),
            ("closed", "La recepción está cerrada en la fecha de comprobación."),
            ("indirect", "Solo admite manuscritos por vía indirecta, por ejemplo a través de agencia."),
            ("award_only", "Solo recibe originales dentro de una convocatoria o premio concreto."),
            ("unknown", "No hay fuente oficial suficiente para afirmar el estado."),
        )
    )
    count = len(records)
    description = (
        "Cómo se verifica, se fecha y se corrige la información de las fichas de "
        "editoriales: fuentes primarias, estados permitidos, caducidad y correcciones."
    )
    main_html = f'''
<main id="contenido" tabindex="-1" class="v1-main" data-family="tool">
  {breadcrumbs([('Inicio', '/'), ('Editoriales', '/editoriales/'), ('Metodología', None)])}
    <header class="tool-hero"><p class="eyebrow">Metodología</p><h1>Cómo se verifica esta información.</h1><p class="tool-hero__lead">Cada ficha del directorio se genera a partir de un dataset validado, no se escribe a mano. Esta página explica de dónde sale cada dato, cuándo caduca y cómo se corrige.</p></header>

    <section class="v1-section">
        <div class="tool-findings-block"><h2>De dónde sale cada dato</h2><p>Los datos de recepción de manuscritos proceden de la página oficial de cada editorial. Cada ficha enlaza esa fuente primaria y separa siempre el hecho publicado por la editorial de cualquier resumen propio. Cuando la editorial no publica una vía de envío directa, la ficha lo dice en vez de deducirlo.</p><p>Actualmente el directorio publica {plural_fichas(count)}.</p></div>

        <div class="tool-findings-block"><h2>Estados de recepción</h2><p>El estado es un valor cerrado, no texto libre, para que no aparezcan variantes contradictorias entre fichas:</p><dl class="spec-ledger">{states}</dl></div>

        <div class="tool-findings-block"><h2>Fechas y caducidad</h2><p>Cada ficha distingue dos fechas: <strong>última comprobación</strong> (cuándo se revisó la fuente oficial) y <strong>última actualización de la página</strong> (cuándo cambió de forma significativa el contenido publicado aquí). Una ficha comprobada hace más de 90 días se marca para revisión: la información de recepción cambia sin aviso y una fecha vieja no es una garantía.</p></div>

        <div class="tool-findings-block"><h2>Qué no se publica</h2><p>El dataset público se genera filtrando la hoja de trabajo interna, así que notas privadas y campos de seguimiento no llegan a la web. Los correos de contacto solo se publican cuando la propia editorial los ofrece como vía de envío y la recepción está abierta: publicar un correo histórico de una recepción cerrada solo genera envíos que nadie va a leer.</p><p>No hay valoraciones, rankings ni recomendaciones de una editorial sobre otra. El builder falla si alguien intenta introducir un campo de ranking.</p></div>

        <div class="tool-findings-block"><h2>Correcciones</h2><p>Si eres responsable de una editorial listada o detectas un dato incorrecto u obsoleto, escribe a <a href="mailto:davidportodiaz@gmail.com">davidportodiaz@gmail.com</a> indicando la ficha y la fuente oficial. Las correcciones con fuente se aplican y quedan reflejadas en el historial de comprobaciones de la ficha correspondiente.</p></div>

        <p class="tool-note"><strong>No es asesoramiento ni representación.</strong> davidportodiaz.com no representa a ninguna de estas editoriales. Las instrucciones oficiales de cada editorial prevalecen siempre sobre lo que se resuma aquí.</p>
    </section>
</main>'''

    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": "Metodología del directorio de editoriales",
                "description": description,
                "dateModified": methodology_date_modified(records),
                "inLanguage": "es",
                "isPartOf": {"@id": f"{site}/editoriales/"},
                "author": {"@id": f"{site}/#author"},
            }
        ],
    }
    return page_shell(
        title="Metodología del directorio de editoriales | David Porto Díaz",
        description=description,
        canonical=canonical,
        main_html=main_html,
        jsonld=jsonld,
    )


def write_page(path: Path, html: str) -> None:
    """Escribe una página generada del directorio editorial V1."""
    path.write_text(html, encoding="utf-8")


def with_site_shell(html: str) -> str:
    """Sustituye el shell de la plantilla por el generado desde el contrato."""
    return inject_shell_auto(html)


def build(data_path: Path, output: Path, today: date, check_only: bool) -> tuple[int, list[str]]:
    raw, records, warnings = load_and_validate(data_path, today)
    if check_only:
        return len(records), warnings

    target = output / "editoriales"
    target.mkdir(parents=True, exist_ok=True)
    write_page(target / "index.html", with_site_shell(render_index(raw["site"].rstrip('/'), records, today)))
    for record in records:
        detail_dir = target / record["slug"]
        detail_dir.mkdir(parents=True, exist_ok=True)
        write_page(detail_dir / "index.html", with_site_shell(render_detail(raw["site"].rstrip('/'), record, today)))

    methodology_dir = output / METHODOLOGY_SLUG
    methodology_dir.mkdir(parents=True, exist_ok=True)
    write_page(
        methodology_dir / "index.html",
        with_site_shell(render_methodology(raw["site"].rstrip('/'), records, today)),
    )

    safe_payload = {"version": raw["version"], "publishers": records}
    (target / "editoriales-data.json").write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "editoriales-sitemap.xml").write_text(render_sitemap(raw["site"].rstrip('/'), records), encoding="utf-8")
    return len(records), warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="JSON público validado")
    parser.add_argument("--output", type=Path, default=Path("dist-editoriales"), help="Directorio de salida")
    parser.add_argument("--check", action="store_true", help="Solo validar; no generar archivos")
    parser.add_argument("--today", default=date.today().isoformat(), help="Fecha de referencia YYYY-MM-DD para QA reproducible")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        today = parse_iso_date(args.today, "today")
        count, warnings = build(args.data, args.output, today, args.check)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"OK: {count} editoriales publicables validadas")
    for warning in warnings:
        print(f"AVISO: {warning}")
    if not args.check:
        print(f"Generado en: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
