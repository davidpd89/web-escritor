#!/usr/bin/env python3
"""Funciones puras para la futura ingesta de libros (sin red, LLM ni efectos).

NO lee Amazon, NO descarga portadas, NO publica HTML.
Contrato de referencia: .github/plans/ingesta-automatica-libros-editoriales-2026-10-20.md.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from urllib.parse import urlencode

_ISBN13 = re.compile(r"97[89]\d{10}\Z")
_ISBN10 = re.compile(r"\d{9}[\dX]\Z")
_ASIN = re.compile(r"[A-Z0-9]{10}\Z")
_TAG = re.compile(r"[a-zA-Z0-9-]+\Z")
_PARTIAL_DATE = re.compile(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?\Z")
_UNKNOWN_PUBLISHERS = {
    "independently published", "kdp", "createspace independent publishing platform",
    "self-published", "autopublicado", "autoeditado",
}


def normalize_text(value: str) -> str:
    """Normalización para alias; NO usar como texto público ni ID canónico."""
    folded = unicodedata.normalize("NFKD", str(value).casefold())
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_text).split())


_SPACE_RUN = re.compile(r"\s{2,}")


def clean_title(value: str) -> str:
    """Texto público de título: colapsa secuencias de 2+ espacios (incluidos los
    Unicode) en un único espacio y recorta los bordes. Idempotente; un espacio
    suelto (p. ej. NBSP legítimo), la puntuación, tildes y demás Unicode no se tocan."""
    return _SPACE_RUN.sub(" ", str(value)).strip()


_NAME_PARTICLES = {"de", "del", "la", "las", "los", "y", "van", "von", "der", "da", "di", "du", "le"}


def clean_author(value: str) -> str:
    """Nombre de autor público: los que llegan enteros en mayúsculas («JØRN LIER HORST») pasan a
    «Jørn Lier Horst»; las partículas van en minúscula salvo al inicio. Los demás no se tocan."""
    name = clean_title(value)
    letters = [ch for ch in name if ch.isalpha()]
    # Un seudónimo de una palabra en mayúsculas («KKAM») es estilo del autor, no un fallo de la fuente.
    if " " not in name or not all(ch.isupper() for ch in letters):
        return name
    words = []
    for i, word in enumerate(name.lower().split(" ")):
        if i and word in _NAME_PARTICLES:
            words.append(word)
        else:
            words.append("-".join(re.sub(r"^(\W*)(\w)", lambda m: m.group(1) + m.group(2).upper(), part)
                                  for part in word.split("-")))
    return " ".join(words)


_SHOUT_WORD = re.compile(r"^[^\w]*(?:\d+|[^\W\d_]*[^\W\d_a-zà-ÿ]+)[^\w]*$")
_QUOTE = re.compile(r"^\s*[«“\"][^»”\"]{1,240}[»”\"]\s*")


def _is_shout(word: str) -> bool:
    letters = [ch for ch in word if ch.isalpha()]
    return bool(_SHOUT_WORD.match(word)) and all(ch.isupper() for ch in letters)


def strip_shouting(text: str) -> str:
    """Quita el marketing editorial pegado al inicio de un párrafo —titulares en mayúsculas
    de 3+ palabras y citas de prensa con su atribución— y pasa a minúscula los titulares que
    quedan dentro del texto («criar en EQUIPO DE VERDAD» → «criar en equipo de verdad»).
    Si limpiar dejara menos de 10 palabras, devuelve el original."""
    words = clean_title(text).split(" ")

    def run_end(i):
        j = i
        while j < len(words) and _is_shout(words[j]) and any(ch.isalpha() or ch.isdigit() for ch in words[j]):
            j += 1
        letters = sum(any(ch.isalpha() for ch in w) for w in words[i:j])
        return j if letters >= 3 else i

    i = 0
    while i < len(words):
        end = run_end(i)
        if end > i:
            i = end
            continue
        quote = _QUOTE.match(" ".join(words[i:]))
        if not quote:
            break
        i += len(quote.group(0).split())
        # Atribución de la cita: palabras capitalizadas hasta el siguiente titular en mayúsculas.
        j = i
        while j < len(words) and words[j][:1].isupper() and not _is_shout(words[j]):
            j += 1
        if j > i and (j == len(words) or run_end(j) > j):
            i = j
    rest = words[i:]
    out, k = [], 0
    while k < len(rest):
        end = k
        while end < len(rest) and _is_shout(rest[end]):
            end += 1
        if sum(any(ch.isalpha() for ch in w) for w in rest[k:end]) >= 3:
            chunk = [w.lower() for w in rest[k:end]]
            if not out or out[-1][-1:] in ".!?»":
                chunk[0] = re.sub(r"^(\W*)(\w)", lambda m: m.group(1) + m.group(2).upper(), chunk[0])
            if end < len(rest) and rest[end][:1].isupper() and chunk[-1][-1:].isalnum():
                chunk[-1] += "."
            out.extend(chunk)
            k = end
        else:
            out.append(rest[k])
            k += 1
    cleaned = " ".join(out)
    return cleaned if len(out) >= 10 else clean_title(text)


def isbn13(value: str) -> str | None:
    """Validar ISBN-13 o convertir ISBN-10 completo con X final si procede."""
    raw = re.sub(r"[\s-]", "", str(value).upper())
    if _ISBN10.fullmatch(raw):
        check10 = sum((10 - i) * (10 if ch == "X" else int(ch))
                      for i, ch in enumerate(raw))
        if check10 % 11:
            return None
        stem = "978" + raw[:9]
        checksum = (-sum(int(ch) * (1 if i % 2 == 0 else 3)
                         for i, ch in enumerate(stem))) % 10
        raw = stem + str(checksum)
    if not _ISBN13.fullmatch(raw):
        return None
    checksum = sum(int(ch) * (1 if i % 2 == 0 else 3)
                   for i, ch in enumerate(raw))
    return raw if checksum % 10 == 0 else None


def edition_date(value: str) -> tuple[str | None, str]:
    """(fecha, precisión); nunca inventar un día a partir de año/mes."""
    match = _PARTIAL_DATE.fullmatch(str(value).strip())
    if match is None:
        return None, "desconocida"
    year, month, day = match.groups()
    try:
        if day is not None:
            iso = date(int(year), int(month), int(day)).isoformat()
            return iso, "dia"
        if month is not None:
            if not 1 <= int(month) <= 12:
                return None, "desconocida"
            return f"{year}-{month}", "mes"
        if int(year) < 1000:
            return None, "desconocida"
        return year, "anio"
    except ValueError:
        return None, "desconocida"


def novelty_labels(published: str, today: date) -> tuple[str, ...]:
    """Solo fechas civiles completas; 30/90 recientes y próximos 30 días."""
    normalized, precision = edition_date(published)
    if precision != "dia" or normalized is None:
        return ()
    delta = (today - date.fromisoformat(normalized)).days
    if 0 <= delta < 30:
        return ("ultimos-30", "ultimos-90")
    if 30 <= delta < 90:
        return ("ultimos-90",)
    if -30 <= delta < 0:
        return ("proximos-30",)
    return ()


def publisher_slug(publisher: str, allowed: list[dict]) -> str | None:
    """Coincidencia EXACTA con sello o alias; desconocidos se quedan pendientes."""
    name = normalize_text(publisher)
    if not name or name in _UNKNOWN_PUBLISHERS:
        return None
    for record in allowed:
        if record.get("enabled") is False:
            continue
        options = [record.get("name", ""), *record.get("aliases", [])]
        if name in {normalize_text(item) for item in options if item}:
            return record["slug"]
    return None


def affiliate_destination(isbn: str, tag: str, asin: str | None = None) -> dict:
    """Dos destinos distintos: ASIN comprobado o búsqueda ISBN; no valida stock.

    Solo llamar con asin que se haya verificado por una fuente/producto real.
    """
    valid = isbn13(isbn)
    if valid is None:
        raise ValueError("ISBN no válido; no se puede generar enlace")
    if not _TAG.fullmatch(tag):
        raise ValueError("Identificador de afiliado no válido")
    if asin is not None:
        if not _ASIN.fullmatch(asin):
            raise ValueError("ASIN no válido")
        return {
            "tipo": "producto_verificado",
            "url": f"https://www.amazon.es/dp/{asin}?" + urlencode({"tag": tag}),
            "texto": "Ver en Amazon",
        }
    return {
        "tipo": "busqueda_isbn",
        "url": "https://www.amazon.es/s?" + urlencode({"k": valid, "tag": tag}),
        "texto": "Buscar este ISBN en Amazon",
    }


def google_books_query(publisher: str, api_key: str, *, page: int = 0,
                       max_results: int = 40) -> dict[str, str | int]:
    """Parámetros compatibles con volumes.list; el adaptador controla cuotas."""
    if not publisher.strip() or not api_key.strip():
        raise ValueError("Editorial y clave API son necesarias")
    if not 0 <= page <= 100 or not 1 <= max_results <= 40:
        raise ValueError("Fuera de paginación de búsqueda configurada")
    return {
        "q": f"inpublisher:{publisher}",
        "orderBy": "newest",
        "langRestrict": "es",
        "printType": "books",
        "showPreorders": "true",
        "maxResults": max_results,
        "startIndex": page * max_results,
        "key": api_key,
    }


def google_books_candidate(volume: dict, allowed: list[dict]) -> dict | None:
    """Recorta un resultado de Google Books a un candidato con ISBN verificable.

    NO transforma el candidato en ficha publicada. NO reutiliza la descripción
    de la fuente como una reseña propia.
    """
    info = volume.get("volumeInfo") or {}
    if info.get("language") not in ("es", None):
        return None
    slug = publisher_slug(info.get("publisher", ""), allowed)
    if slug is None:
        return None
    # Prefer an explicitly tagged ISBN-13 for the selected edition.
    # Never silently treat a valid-looking "OTHER" identifier as a book ISBN.
    identifiers = info.get("industryIdentifiers") or []
    primary = [isbn13(i.get("identifier", "")) for i in identifiers
               if i.get("type") == "ISBN_13"]
    fallback = [isbn13(i.get("identifier", "")) for i in identifiers
                if i.get("type") == "ISBN_10"]
    valid = next((x for x in primary + fallback if x is not None), None)
    if valid is None or not info.get("title") or not info.get("authors"):
        return None
    published, precision = edition_date(info.get("publishedDate") or "")
    return {
        "candidate_key": "isbn13:" + valid,
        "isbn13": valid,
        "titulo": clean_title(info["title"]),
        "autores": list(info["authors"]),
        "editorial_sello_slug": slug,
        "fecha_publicacion_edicion": published,
        "precision_fecha": precision,
        "google_volume_id": volume.get("id"),
        "google_categories": info.get("categories", []),
        "estado_ingesta": "descubierto",
    }
