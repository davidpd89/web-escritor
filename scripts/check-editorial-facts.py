#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FACTS_PATH = ROOT / "editorial-facts.json"
FACTS = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
BOOK = FACTS["books"]["lasManecillasDelRecuerdo"]
SAMUEL = FACTS["books"]["samuelEntreMundos"]
PUBLICATION_DATE = date.fromisoformat(BOOK["publicationDate"])
MADRID = ZoneInfo("Europe/Madrid")

CRITICAL_SURFACES = [
    "index.html",
    "autor.html",
    "libros/index.html",
    "las-manecillas-del-recuerdo/index.html",
    "prensa.html",
    "premios.html",
    "ai/index.html",
    "llms.txt",
    "llms-full.txt",
    "humans.txt",
    "press-kit/david-porto-diaz.json",
    "press-kit/las-manecillas-del-recuerdo.json",
    "manifest.json",
]

FORBIDDEN_GLOBAL = [
    (re.compile(r"@davidpuede", re.I), "handle erróneo de la cubierta"),
]

FORBIDDEN_AWARD_WORDING = [
    (re.compile(r"\bI\s*(?:º|°|o)?\s*Premio\s+Letras\s+Como\s+Espada", re.I), "denominación ambigua del premio Letras Como Espada"),
    (re.compile(r"\bPrimer\s+Premio\s+Letras\s+Como\s+Espada\s+2026", re.I), "denominación incompleta del premio Letras Como Espada"),
]

FORBIDDEN_SAMUEL_CANON = [
    (re.compile(r"Samuel entre mundos.{0,240}\b412\s+páginas\b", re.I | re.S), "412 páginas de Samuel incorrecto (dato de retailer, no del editor); el valor correcto es 422 (409 numeradas + portada/contraportada, confirmado contra el ejemplar físico y la ficha de Libros Indie)"),
    # Edad: sin fuente primaria (la ficha de Libros Indie no publica un rango de
    # edad; Casa del Libro dice 15+ pero es un retailer, la misma fuente que dio
    # el dato de páginas incorrecto). No se afirma ningún número concreto.
    # Anchored to actual age phrasing ("X años", "X+ años", "a partir de X años")
    # so it doesn't false-positive on timestamps/date ranges elsewhere on a page
    # that happens to mention Samuel entre mundos within the lookaround window.
    (re.compile(r"Samuel entre mundos.{0,240}\b\d{1,2}\s*(?:\+\s*años|\+(?!\d)|años en adelante|(?:años? )?en adelante)", re.I | re.S), "edad objetivo de Samuel no verificada (sin fuente primaria; no afirmar un número concreto)"),
    (re.compile(r"\ba partir de\s+\d{1,2}\s*años.{0,240}Samuel entre mundos", re.I | re.S), "edad objetivo de Samuel no verificada (sin fuente primaria; no afirmar un número concreto)"),
    (re.compile(r"Samuel entre mundos.{0,240}\ba partir de\s+\d{1,2}\s*años", re.I | re.S), "edad objetivo de Samuel no verificada (sin fuente primaria; no afirmar un número concreto)"),
    (re.compile(r"Samuel entre mundos.{0,260}(?:9\s+calificaciones|11\s+valoraciones|aggregateRating)", re.I | re.S), "valoraciones de Samuel no aptas como dato canónico durable"),
    # Año resuelto el 19/08/2026: 2025 es correcto, 2026 es el valor incorrecto que circulaba.
    # Este patrón exige que el paréntesis con el año venga pegado al título (permitiendo
    # </em>/* de cierre de énfasis y "de David Porto Díaz"), para no disparar con años
    # correctos de OTRA obra o premio que aparezcan más adelante en la misma frase.
    (re.compile(r"Samuel entre mundos(?:</em>|\*)?(?:\s*de David Porto D[ií]az)?\s*\([^)]{0,40}2026\)", re.I), "año de Samuel incorrecto (2026) pegado al título; el año correcto es 2025"),
    (re.compile(r"Samuel entre mundos.{0,100}\bpublicad[oa]\s+(?:en\s+)?2026\b", re.I | re.S), "año de publicación de Samuel incorrecto (2026); el año correcto es 2025"),
]

PRELAUNCH_AVAILABLE = [
    re.compile(r"Las manecillas del recuerdo.{0,180}(?:ya\s+)?disponibles?(?:\s+ahora)?", re.I | re.S),
    re.compile(r"(?:ya\s+)?disponibles?(?:\s+ahora)?.{0,180}Las manecillas del recuerdo", re.I | re.S),
    re.compile(r"[\"']status[\"']\s*:\s*[\"']available[\"']", re.I),
    re.compile(r"buy_(?:open|click)_manecillas", re.I),
]

# Honest future/conditional phrasing ("los enlaces aparecerán... en cuanto
# estén disponibles") is the CORRECT prelaunch copy (see this session's
# Manecillas UX fixes) and must not be flagged as a premature availability
# claim just because the word "disponible(s)" appears near the title. Only
# treat a PRELAUNCH_AVAILABLE match as real if "disponible(s)" itself isn't
# immediately preceded by a conditional/future marker.
CONDITIONAL_AVAILABILITY_MARKERS = re.compile(r"(?:en\s+cuanto|cuando)\s+est[ée]n?\s*$", re.I)

# El kit de prensa marca cada recurso (bio, foto, portada) con
# <span class="status-badge status--available">Disponible</span>: eso dice que
# el RECURSO se puede copiar/descargar, no que el libro esté a la venta. Como
# esas tarjetas citan el título en el texto de la bio, el badge caía dentro de
# la ventana de 180 caracteres y se contaba como anuncio prematuro de compra.
# Se eliminan esos badges antes de buscar afirmaciones de disponibilidad.
ASSET_STATUS_BADGE = re.compile(
    r"<span[^>]*class=\"[^\"]*status-badge[^\"]*\"[^>]*>.*?</span>", re.I | re.S
)


def _strip_asset_status_badges(text: str) -> str:
    return ASSET_STATUS_BADGE.sub(" ", text)


def _is_conditional_availability(text: str, match: "re.Match") -> bool:
    """True if the 'disponible(s)' in this match is future/conditional
    phrasing ("en cuanto/cuando esté(n) disponible(s)"), not a present-tense
    availability claim."""
    lowered_match = match.group(0).lower()
    idx = lowered_match.find("disponible")
    if idx == -1:
        return False
    preceding = match.group(0)[:idx]
    return bool(CONDITIONAL_AVAILABILITY_MARKERS.search(preceding))

LAUNCH_STALE = [
    re.compile(r"Las manecillas del recuerdo.{0,220}(?:próxima novela|próximamente|en proceso de publicación|fecha de publicación por confirmar|avísame|avísame cuando)", re.I | re.S),
    re.compile(r"(?:próxima novela|próximamente|en proceso de publicación|fecha de publicación por confirmar|avísame|avísame cuando).{0,220}Las manecillas del recuerdo", re.I | re.S),
    re.compile(r"[\"']status[\"']\s*:\s*[\"'](?:announced|scheduled|prelaunch)[\"']", re.I),
]

PLACEHOLDERS = [
    (re.compile(r"\[\[[A-ZÁÉÍÓÚÜÑ0-9_ -]{2,80}\]\]"), "placeholder [[...]]"),
    (re.compile(r"\b(?:REPLACE_ME|CHANGEME|YOUR_[A-Z0-9_]+)\b"), "placeholder técnico"),
    (re.compile(r"https?://(?:www\.)?example\.com\b", re.I), "URL example.com"),
]

SCAN_SUFFIXES = {".html", ".json", ".txt", ".xml", ".webmanifest"}
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "scripts",
    "WEB DAVID PORTO nuevas ideas", "archive", ".codex_work",
    # data/ son fuentes de build (datasets gated, fixtures, entradas de
    # builders). build-public-dist.py las excluye enteras del output público,
    # así que no son "superficie pública" y no deben juzgarse como tal: el
    # placeholder example.com de data/autores-red.json (dataset con gate, sin
    # página publicada) mantenía este checker en rojo permanente sin que nada
    # de eso llegara nunca a un visitante.
    "data",
    ".preview-dist", "dist",
}


def parse_args():
    parser = ArgumentParser(description="Comprueba hechos editoriales y estado de lanzamiento.")
    parser.add_argument("--mode", choices=("auto", "prelaunch", "launch"), default="auto")
    parser.add_argument("--date", help="Fecha YYYY-MM-DD para fixtures/simulación; por defecto hoy en Europe/Madrid")
    return parser.parse_args()


def resolve_today(raw: str | None) -> date:
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(MADRID).date()


def resolve_mode(requested: str, today: date) -> str:
    if requested != "auto":
        return requested
    return "launch" if today >= PUBLICATION_DATE else "prelaunch"


def read(rel: str) -> str | None:
    path = ROOT / rel
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def git_tracked_files() -> set[str]:
    """Files actually tracked by git - i.e. what GitHub Pages can serve.

    A filesystem walk alone doesn't reflect what's public: this repo keeps
    several real, sizeable internal notes files on disk (gitignored) that a
    naive rglob() would wrongly treat as public surfaces, producing
    permanent false-positive findings for content nobody has ever published.
    Falls back to a filesystem walk (old behavior) if git isn't available,
    so this still works in odd environments/CI without git in PATH.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        return {line.strip() for line in out.splitlines() if line.strip()}
    except (OSError, subprocess.CalledProcessError):
        return set()


def public_text_files():
    tracked = git_tracked_files()
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        rel_posix = rel.as_posix()
        if tracked and rel_posix not in tracked:
            continue
        yield rel_posix, path.read_text(encoding="utf-8", errors="replace")



def iter_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def json_documents(rel: str, text: str):
    docs = []
    if rel.endswith(".json"):
        try:
            docs.append(json.loads(text))
        except json.JSONDecodeError:
            return docs
    elif rel.endswith(".html"):
        for match in re.finditer(
            r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
            text,
            re.I | re.S,
        ):
            try:
                docs.append(json.loads(match.group(1)))
            except json.JSONDecodeError:
                continue
    return docs


def samuel_semantic_errors(rel: str, text: str):
    errors = []
    field_groups = []
    if SAMUEL.get("publicationYear") is None:
        field_groups.append(({"datePublished", "publicationDate", "publicationYear", "year"}, "año/fecha de publicación de Samuel"))
    if SAMUEL.get("numberOfPages") is None:
        field_groups.append(({"numberOfPages", "pages", "manuscriptPages"}, "páginas de Samuel"))
    if SAMUEL.get("typicalAgeRange") is None:
        field_groups.append(({"typicalAgeRange", "suggestedMinAge", "ageRange"}, "edad/rango de Samuel"))
    if SAMUEL.get("rating") is None or SAMUEL.get("ratingCount") is None:
        field_groups.append(({"aggregateRating", "rating", "ratingCount", "reviewCount"}, "valoraciones de Samuel"))

    for doc in json_documents(rel, text):
        for obj in iter_dicts(doc):
            label = obj.get("name") or obj.get("title")
            if label != SAMUEL.get("title"):
                continue
            for fields, reason in field_groups:
                present = sorted(field for field in fields if field in obj and obj.get(field) not in (None, "", [], {}))
                if present:
                    errors.append(f"{rel}: {reason} no verificado en JSON/JSON-LD ({', '.join(present)})")
    return errors



def manecillas_semantic_errors(rel: str, text: str):
    errors = []
    for doc in json_documents(rel, text):
        for obj in iter_dicts(doc):
            label = obj.get("name") or obj.get("title")
            if label != BOOK.get("title"):
                continue

            if BOOK.get("format") is None:
                present = sorted(
                    field for field in {"bookFormat", "format"}
                    if field in obj and obj.get(field) not in (None, "", [], {})
                )
                if present:
                    errors.append(
                        f"{rel}: formato de Manecillas no verificado en JSON/JSON-LD ({', '.join(present)})"
                    )

            if not BOOK.get("purchaseUrl"):
                for nested in iter_dicts(obj):
                    nested_type = nested.get("@type")
                    if nested_type == "Offer" or (isinstance(nested_type, list) and "Offer" in nested_type):
                        errors.append(f"{rel}: Offer de Manecillas sin purchaseUrl canónica")
                        break
                for field in {"purchaseUrl", "buyUrl", "orderUrl"}:
                    if field in obj and obj.get(field) not in (None, "", [], {}):
                        errors.append(f"{rel}: {field} de Manecillas sin purchaseUrl canónica")
    return errors

def manecillas_offer_present(rel: str, text: str) -> bool:
    """True only if an Offer node is actually nested under a Manecillas Book,
    not merely co-present anywhere on a page that also mentions the title
    (e.g. an unrelated Offer for Samuel's historical events on /eventos.html)."""
    for doc in json_documents(rel, text):
        for obj in iter_dicts(doc):
            if obj.get("name") != BOOK.get("title") and obj.get("title") != BOOK.get("title"):
                continue
            for nested in iter_dicts(obj):
                nested_type = nested.get("@type")
                if nested_type == "Offer" or (isinstance(nested_type, list) and "Offer" in nested_type):
                    return True
    return False


def main() -> int:
    args = parse_args()
    today = resolve_today(args.date)
    mode = resolve_mode(args.mode, today)
    errors: list[str] = []
    warnings: list[str] = []

    existing: list[tuple[str, str]] = []
    for rel in CRITICAL_SURFACES:
        text = read(rel)
        if text is None:
            if mode == "prelaunch" and rel == "press-kit/las-manecillas-del-recuerdo.json":
                continue
            errors.append(f"FALTA superficie crítica: {rel}")
            continue
        existing.append((rel, text))

    # Autoridad editorial transversal: un hecho retirado no puede sobrevivir en una
    # página secundaria solo porque no esté en CRITICAL_SURFACES. La fuente
    # editorial-facts.json se excluye porque documenta deliberadamente incidencias
    # y valores null que no deben interpretarse como contenido público.
    public_surfaces = [
        (rel, text) for rel, text in public_text_files()
        if rel != "editorial-facts.json"
    ]

    for rel, text in public_surfaces:
        for pattern, reason in FORBIDDEN_GLOBAL:
            if pattern.search(text):
                errors.append(f"{rel}: {reason}")

        # La misma distinción usada en el canon debe sobrevivir a HTML: se
        # normalizan etiquetas para detectar variantes visuales como
        # <span>I°</span><span>Premio Letras Como Espada</span>.
        if "letras como espada" in text.lower():
            plain = re.sub(r"<[^>]+>", " ", text)
            plain = re.sub(r"\s+", " ", plain)
            for pattern, reason in FORBIDDEN_AWARD_WORDING:
                if pattern.search(plain):
                    errors.append(f"{rel}: {reason}")

        if SAMUEL.get("title", "").lower() in text.lower():
            for pattern, reason in FORBIDDEN_SAMUEL_CANON:
                if pattern.search(text):
                    errors.append(f"{rel}: {reason}")
            errors.extend(samuel_semantic_errors(rel, text))

        if BOOK.get("title", "").lower() in text.lower():
            errors.extend(manecillas_semantic_errors(rel, text))

    # Hechos positivos mínimos de la ficha de Manecillas en ambos estados.
    manecillas_rel = "las-manecillas-del-recuerdo/index.html"
    manecillas_text = read(manecillas_rel)
    if manecillas_text is not None:
        required = {
            "ISBN": BOOK["isbn"],
            "fecha ISO": BOOK["publicationDate"],
            "páginas": str(BOOK["numberOfPages"]),
            "editorial": BOOK["publisher"],
        }
        for label, needle in required.items():
            if needle not in manecillas_text:
                errors.append(f"{manecillas_rel}: falta {label} canónico ({needle})")

    if mode == "prelaunch":
        # No anunciar disponibilidad ni Offer si todavía no existe compra verificada.
        if BOOK.get("purchaseUrl") is None:
            for rel, text in public_surfaces:
                availability_text = _strip_asset_status_badges(text)
                for pattern in PRELAUNCH_AVAILABLE:
                    m = pattern.search(availability_text)
                    if m and not _is_conditional_availability(availability_text, m):
                        errors.append(f"{rel}: estado de compra/disponibilidad prematuro para Manecillas")
                if manecillas_offer_present(rel, text):
                    errors.append(f"{rel}: Offer de Manecillas antes de existir purchaseUrl canónica")

    if mode == "launch":
        for rel, text in public_surfaces:
            for pattern in LAUNCH_STALE:
                if pattern.search(text):
                    errors.append(f"{rel}: estado prepublicación de Manecillas sobrevivió al lanzamiento")

        # La publicación no depende de que una tienda haya creado ya su ficha.
        # Si purchaseUrl o format siguen sin verificar, deben omitirse; nunca inventarse.
        if not BOOK.get("purchaseUrl"):
            for rel, text in public_surfaces:
                if manecillas_offer_present(rel, text):
                    errors.append(f"{rel}: Offer de Manecillas sin purchaseUrl canónica")
        if not BOOK.get("format"):
            warnings.append("editorial-facts.json: format sigue null; se permite publicar si se omite de las superficies públicas")
        if not BOOK.get("purchaseUrl"):
            warnings.append("editorial-facts.json: purchaseUrl sigue null; se permite publicar sin CTA/Offer de compra")

        incident = FACTS.get("knownEditorialIncident", {})
        if incident.get("status") != "resolved":
            errors.append("editorial-facts.json: incidencia @davidpuede no está marcada como resolved")

    # Ningún placeholder estructurado debe llegar a superficies públicas, en ningún modo.
    for rel, text in public_surfaces:
        for pattern, reason in PLACEHOLDERS:
            if pattern.search(text):
                errors.append(f"{rel}: {reason} sin resolver")

    # Estado de hechos declarados debe corresponder al modo esperado.
    expected = BOOK["statusBeforePublication"] if mode == "prelaunch" else BOOK["statusFromPublicationDate"]
    if not expected:
        errors.append(f"editorial-facts.json: falta estado esperado para {mode}")

    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))

    print(f"EDITORIAL FACT CHECK · mode={mode} · date={today.isoformat()} · publication={PUBLICATION_DATE.isoformat()}")
    if warnings:
        for warning in warnings:
            print(f"WARN - {warning}")
    if errors:
        print("EDITORIAL FACT CHECK: FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("EDITORIAL FACT CHECK: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
