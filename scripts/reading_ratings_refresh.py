#!/usr/bin/env python3
"""Aggregate ratings with exact ISBN+author+title matching and no LLM.

Google Books and Hardcover use optional server-side API credentials.
Goodreads uses bounded public ISBN pages and stops on denial or rate limits.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = "https://www.googleapis.com/books/v1/volumes"
VALID_VOLUME_ID = re.compile(r"[A-Za-z0-9_-]{1,150}\Z")
VALID_ISBN13 = re.compile(r"97[89]\d{10}\Z")
_hardcover_last_request = 0.0


def isbn13(raw: str) -> str | None:
    raw = re.sub(r"[\s-]", "", str(raw).upper())
    if re.fullmatch(r"\d{9}[0-9X]", raw):
        if sum((10 - i) * (int(c) if c != "X" else 10)
               for i, c in enumerate(raw)) % 11:
            return None
        stem = "978" + raw[:9]
        raw = stem + str(-sum(int(c) * (1 if i % 2 == 0 else 3)
                                   for i, c in enumerate(stem)) % 10)
    if not VALID_ISBN13.fullmatch(raw):
        return None
    return raw if sum(int(c) * (1 if i % 2 == 0 else 3)
                      for i, c in enumerate(raw)) % 10 == 0 else None


def key(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    no_marks = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.sub("[^a-z0-9]+", " ", no_marks).split())


def title_matches(title: str, canonical: str) -> bool:
    a, b = key(title), key(canonical)
    if not a or not b:
        return False
    return a == b or a.startswith(b + " ") or b.startswith(a + " ")


def author_matches(source: str, catalogued: str) -> bool:
    """Handle reversed Spanish cataloging order, without fuzzy cross-author joins."""
    a, b = key(source), key(catalogued)
    return bool(a and b and (a == b or (
        len(a.split()) >= 2 and sorted(a.split()) == sorted(b.split())
    )))


def select_rating(book: dict, api_response: dict) -> dict | None:
    """Reject unrelated editions or authors returned by volume search.

    Multiple books can share ambiguous short names; exact ISBN and author
    are required. Prefer highest number of votes among matching volumes.
    """
    wanted = isbn13(book.get("isbn13", ""))
    if not wanted:
        return None
    chosen = []
    for volume in api_response.get("items", []):
        if not isinstance(volume, dict) or not VALID_VOLUME_ID.fullmatch(str(volume.get("id", ""))):
            continue
        info = volume.get("volumeInfo") or {}
        if not isinstance(info, dict):
            continue
        ids = {isbn13(x.get("identifier", "")) for x in info.get("industryIdentifiers", [])
               if isinstance(x, dict) and x.get("type") in {"ISBN_13", "ISBN_10"}}
        if wanted not in ids:
            continue
        if not title_matches(str(info.get("title") or ""), book["titulo"]):
            continue
        response_authors = [key(str(x)) for x in info.get("authors", []) if isinstance(x, str)]
        desired_authors = [key(x) for x in book.get("autores", [])]
        if not response_authors or not desired_authors:
            continue
        # Initials/full-name handling may be expanded with reviewed aliases,
        # but never choose a rating for a different author's homonymous book.
        if not any(author_matches(a, b) for a in response_authors for b in desired_authors):
            continue
        rating, votes = info.get("averageRating"), info.get("ratingsCount")
        if isinstance(rating, bool) or isinstance(votes, bool):
            continue
        if not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
            continue
        if not isinstance(votes, int) or votes < 1:
            continue
        chosen.append((votes, float(rating), str(volume["id"])))
    if not chosen:
        return None
    votes, rating, volume_id = max(chosen)
    return {
        "libro_id": book["id"],
        "puntuacion": round(rating, 2),
        "numero_valoraciones": votes,
        "fuente": "google_books",
        "url": "https://books.google.com/books?" + urlencode({"id": volume_id}),
    }


def select_hardcover_rating(book: dict, api_response: dict) -> dict | None:
    """Optional server-side Hardcover aggregate; only exact edition matching."""
    editions = (api_response.get("data") or {}).get("editions") or []
    wanted = isbn13(book.get("isbn13", ""))
    if not wanted:
        return None
    matches = []
    for edition in editions:
        if not isinstance(edition, dict):
            continue
        if wanted not in {isbn13(edition.get("isbn_13", "")),
                          isbn13(edition.get("isbn_10", ""))}:
            continue
        source = edition.get("book") or {}
        if not title_matches(str(source.get("title") or ""), book["titulo"]):
            continue
        contributors = source.get("contributions") or []
        authors = [key(str((c.get("author") or {}).get("name", "")))
                   for c in contributors if isinstance(c, dict)
                   and c.get("contribution") in (None, "Author")]
        if not any(author_matches(a, name) for a in authors for name in book.get("autores", [])):
            continue
        slug = str(source.get("slug") or "")
        rating, votes = source.get("rating"), source.get("ratings_count")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            continue
        if isinstance(rating, bool) or isinstance(votes, bool):
            continue
        if not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
            continue
        if not isinstance(votes, int) or votes < 1:
            continue
        matches.append((votes, float(rating), slug))
    if not matches:
        return None
    votes, rating, slug = max(matches)
    return {"libro_id": book["id"], "puntuacion": round(rating, 2),
            "numero_valoraciones": votes, "fuente": "hardcover",
            "url": "https://hardcover.app/books/" + slug}


def hardcover_response(isbn: str, api_token: str, timeout=18) -> dict:
    """Query modeled on MIT-licensed Bookery provider. Never expose token in JS."""
    global _hardcover_last_request
    query = """
    query ByIsbn($isbn: String!) {
      editions(
        where: {_or: [{isbn_13: {_eq: $isbn}}, {isbn_10: {_eq: $isbn}}]},
        limit: 5
      ) {
        isbn_13
        isbn_10
        book {
          title slug rating ratings_count
          contributions { author {name} contribution }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"isbn": isbn}}).encode("utf-8")
    request = Request("https://api.hardcover.app/v1/graphql", data=payload,
                      headers={"Authorization": "Bearer " + api_token,
                               "Content-Type": "application/json",
                               "User-Agent": "DavidPortoReadingCatalogue/1.0"})
    # The free account permits 60 requests/minute and bursts of ten.
    # The writer is sequential; spacing requests avoids exhausting either limit.
    time.sleep(max(0, 1.1 - (time.monotonic() - _hardcover_last_request)))
    _hardcover_last_request = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Hardcover HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Hardcover temporalmente no disponible") from exc
    if not isinstance(result, dict) or result.get("errors"):
        raise RuntimeError("Hardcover GraphQL error o respuesta inválida")
    return result


def google_response(isbn: str, key_env: str, timeout=18) -> dict:
    params = urlencode({"q": f"isbn:{isbn}", "maxResults": 10, "printType": "books",
                        "key": key_env})
    request = Request(API + "?" + params, headers={
        "Accept": "application/json",
        "User-Agent": "DavidPortoReadingCatalogue/1.0 (davidportodiaz.com)",
    })
    try:
        with urlopen(request, timeout=timeout) as response:
            obj = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Google Books HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Google Books temporalmente no disponible") from exc
    if not isinstance(obj, dict) or (obj.get("items") is not None and not isinstance(obj["items"], list)):
        raise RuntimeError("Respuesta Google Books con estructura inesperada")
    return obj


def refresh(catalogue: dict, existing: dict, provider, *, now: datetime,
            budget: int, source: str = "google_books") -> tuple[dict, dict]:
    """Merge provider-sourced ratings, keep Goodreads legacy separate.

    Repeated runs cannot create duplicates per (book, source). No network calls
    when budget=0; no fake "updated today" on a missing rating or API failure.
    """
    if not 0 <= budget <= 100:
        raise ValueError("El presupuesto debe estar entre 0 y 100 llamadas")
    if source not in {"google_books", "hardcover", "goodreads"}:
        raise ValueError("Origen de valoración desconocido")
    # Validate catalogue identity before querying providers or merging ratings.
    seen_book_ids = {}
    for book in catalogue.get("libros", []):
        book_id = book.get("id")
        raw_isbn = str(book.get("isbn13") or "").replace("-", "").replace(" ", "").strip()
        book_isbn = isbn13(raw_isbn) or raw_isbn
        if book_id in seen_book_ids and seen_book_ids[book_id] != book_isbn:
            raise ValueError(
                f"Identificador editorial duplicado con ISBN diferentes: {book_id!r}"
            )
        seen_book_ids[book_id] = book_isbn
    others = [r for r in existing.get("ratings", [])
              if r.get("fuente", "goodreads") != source]
    old_source = {r.get("libro_id"): r for r in existing.get("ratings", [])
                  if r.get("fuente", "goodreads") == source}
    stats = {"attempted": 0, "updated": 0, "unrated": 0, "failures": []}
    published = [b for b in catalogue.get("libros", [])
                 if b.get("estado") in {"listo", "publicado"}
                 and isbn13(b.get("isbn13", ""))]
    published_ids = {b["id"] for b in published}
    after = {book_id: rating for book_id, rating in old_source.items()
             if book_id in published_ids}
    # Rotate fair slices to cover the entire growing catalogue.
    offset = (now.astimezone(timezone.utc).date().toordinal() * max(budget, 1)) % len(published) if published else 0
    queued = published[offset:] + published[:offset]
    for book in queued:
        if stats["attempted"] >= budget:
            break
        if book.get("estado") not in {"listo", "publicado"} or not isbn13(book.get("isbn13", "")):
            continue
        stats["attempted"] += 1
        try:
            response = provider(book["isbn13"])
            if source == 'goodreads':
                from reading_goodreads import select_goodreads_rating
                selector = select_goodreads_rating
            else:
                selector = select_hardcover_rating if source == 'hardcover' else select_rating
            rated = selector(book, response)
            if rated is None:
                stats["unrated"] += 1
                # Do not resurrect stale data by refreshing timestamps blindly.
                continue
            timestamp = now.astimezone(timezone.utc)
            rated["actualizado_en"] = timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")
            rated["caduca_en"] = (timestamp + timedelta(days=7)).isoformat(timespec="seconds").replace("+00:00", "Z")
            after[book["id"]] = rated
            stats["updated"] += 1
        except (RuntimeError, OSError, ValueError, TypeError) as exc:
            stats["failures"].append({"book_id": book["id"], "error": str(exc)[:140]})
            if isinstance(exc, RuntimeError):
                # An unavailable or throttled provider must not receive another
                # request for every remaining ISBN in this daily batch.
                stats["stopped"] = True
                break
    payload = {
        "schema_version": 1,
        "offers": existing.get("offers", []),
        "ratings": others + [after[i] for i in sorted(after)],
    }
    return payload, stats


def write_changed(path: Path, payload: dict) -> bool:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", type=Path, help="Respuestas por ISBN para pruebas offline")
    source.add_argument("--live", action="store_true", help="API oficial Google Books")
    source.add_argument("--hardcover", action="store_true", help="API Hardcover opcional")
    source.add_argument("--goodreads", action="store_true", help="Valoraciones públicas por ISBN, sin cuenta")
    parser.add_argument("--catalogue", type=Path, default=ROOT / "data/reading-catalogue.json")
    parser.add_argument("--market", type=Path, default=ROOT / "assets/reading-market.json")
    parser.add_argument("--out", type=Path, help="Ruta alternativa; no altera la web")
    parser.add_argument("--budget", type=int, default=25)
    parser.add_argument("--now", type=str, help="Instante ISO UTC de prueba")
    args = parser.parse_args()
    api_key = os.environ.get("GOOGLE_BOOKS_API_KEY", "").strip()
    hardcover_key = os.environ.get("HARDCOVER_API_KEY", "").strip()
    if args.live and not api_key:
        parser.error("GOOGLE_BOOKS_API_KEY no configurada. No se hace llamada HTTP.")
    if args.hardcover and not hardcover_key:
        parser.error("HARDCOVER_API_KEY no configurada. No se hace llamada HTTP.")
    fixture = json.loads(args.fixture.read_text(encoding="utf-8")) if args.fixture else {}
    provider = (lambda isbn: fixture.get(isbn, {"items": []})) if args.fixture else (
        (lambda isbn: hardcover_response(isbn, hardcover_key)) if args.hardcover
        else (lambda isbn: google_response(isbn, api_key)))
    if args.goodreads:
        from reading_goodreads import GoodreadsPublic
        provider = GoodreadsPublic()
    now = datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        parser.error("--now debe contener zona horaria")
    catalogue = json.loads(args.catalogue.read_text(encoding="utf-8"))
    market = json.loads(args.market.read_text(encoding="utf-8"))
    result, stats = refresh(catalogue, market, provider, now=now, budget=args.budget,
                            source="goodreads" if args.goodreads else "hardcover" if args.hardcover else "google_books")
    output = args.out or args.market
    changed = write_changed(output, result)
    print(json.dumps({"output": str(output), "changed": changed, **stats},
                     ensure_ascii=False, sort_keys=True))
    return 0 if not stats["failures"] else 2


if __name__ == "__main__":
    sys.exit(main())
