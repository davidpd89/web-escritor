#!/usr/bin/env python3
"""Experimental Google Books discovery -> deduplicated staging JSON (no web publication).

Execution is explicit. No API call without --live; --fixture exercises the same
pipeline offline. This stage never writes reading-catalogue.json or creates pages.
No AI, browser sessions, Amazon API, payment service or external Python deps.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from reading_intake_core import google_books_candidate, google_books_query, isbn13
from reading_intake_publishers import resolve_publishers

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.googleapis.com/books/v1/volumes"
_DEFAULT_CONFIG = ROOT / "data/reading-intake-sources.example.json"
_DEFAULT_EDITORIALES = ROOT / "data/editoriales.json"
_DEFAULT_OUTPUT = ROOT / ".ci/reading-intake/google-books-candidates.json"
_DEFAULT_STATE = ROOT / "data/reading-intake-state.json"


def read_json(path: Path, default=None):
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_if_changed(path: Path, value: dict) -> bool:
    """Atomic write, stable sorting; unchanged content never creates a commit."""
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == serialized:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(serialized, encoding="utf-8")
    temp.replace(path)
    return True


def existing_isbns(path: Path) -> set[str]:
    """Existing published ISBNs are never re-imported as a new work."""
    data = read_json(path)
    return {valid for b in data.get("libros", [])
            if (valid := isbn13(b.get("isbn13", ""))) is not None}


def fetch_google_books(params: dict, *, pause_seconds=0.3, retries=2):
    """Small retry budget, backoff and capped Retry-After. API key stays private."""
    url = BASE + "?" + urlencode(params)
    headers = {"User-Agent": "DavidPortoReadingCatalogue/1.0 (website: davidportodiaz.com)",
               "Accept": "application/json"}
    for attempt in range(retries + 1):
        try:
            if pause_seconds:
                time.sleep(pause_seconds)
            with urlopen(Request(url, headers=headers), timeout=20) as response:
                data = json.load(response)
                if not isinstance(data, dict):
                    raise ValueError("Respuesta Google Books no es un objeto")
                return data
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries:
                raise RuntimeError(f"Google Books HTTP {exc.code}") from exc
            retry = exc.headers.get("Retry-After", "")
            try:
                delay = max(0.0, min(30.0, float(retry)))
            except ValueError:
                delay = min(12.0, 2.0 ** attempt)
            time.sleep(delay)
        except (URLError, TimeoutError) as exc:
            if attempt == retries:
                raise RuntimeError("Google Books no disponible") from exc
            time.sleep(min(12.0, 2.0 ** attempt))
    raise RuntimeError("Agotados los reintentos")


def merge_candidate(state: dict, candidate: dict, today: str) -> bool:
    """Update only substantive changes; first_seen persists and no daily churn."""
    items = state.setdefault("items", {})
    key = candidate["candidate_key"]
    previous = items.get(key, {})
    normalized = dict(candidate)
    normalized["primera_deteccion"] = previous.get("primera_deteccion", today)
    normalized["ultima_modificacion"] = previous.get("ultima_modificacion", today)
    # If unchanged, retain previous exact record: stable JSON on reruns.
    comparable_old = {k: v for k, v in previous.items()
                      if k not in {"primera_deteccion", "ultima_modificacion"}}
    comparable_new = {k: v for k, v in normalized.items()
                      if k not in {"primera_deteccion", "ultima_modificacion"}}
    if previous and comparable_old == comparable_new:
        return False
    normalized["ultima_modificacion"] = today
    items[key] = normalized
    return True


def discover(config: dict, *, fixture: dict | None, api_key: str,
             max_requests: int, existing: set[str], state: dict,
             today: str, fetch_fn=fetch_google_books) -> dict:
    """Run bounded discovery with per-publisher errors, without changing site data."""
    allowed = config["publishers"]
    settings = config.get("google_books", {})
    pages = min(int(settings.get("pages_per_publisher", 1)), 10)
    per_page = min(int(settings.get("max_results_per_page", 40)), 40)
    stats = {"requests": 0, "seen": 0, "eligible": 0, "new": 0,
             "unchanged": 0, "already_published": 0, "ignored": 0, "errors": []}
    if not 1 <= max_requests <= 500:
        raise ValueError("max_requests debe estar entre 1 y 500")
    # Date-rotated discovery avoids starving later sellos under a small budget.
    # Stable within a day; no daily state cursor writes merely to rotate.
    active = [p for p in allowed if p.get("enabled") is not False]
    if not active:
        return stats
    offset = (date.fromisoformat(today).toordinal() * max(1, max_requests // pages)) % len(active)
    rotation = active[offset:] + active[:offset]
    for publisher in rotation:
        slug = publisher["slug"]
        if stats["requests"] >= max_requests:
            break
        for page in range(pages):
            if stats["requests"] >= max_requests:
                break
            try:
                if fixture is not None:
                    pages_for_publisher = (fixture.get("pages") or {}).get(slug, [])
                    if page >= len(pages_for_publisher):
                        break
                    stats["requests"] += 1
                    payload = pages_for_publisher[page]
                else:
                    params = google_books_query(publisher["name"], api_key,
                                                page=page, max_results=per_page)
                    # Count EVERY attempted request, including 429 / 403 / timeout.
                    # Otherwise a bad API key makes this loop exceed daily budget.
                    stats["requests"] += 1
                    payload = fetch_fn(params)
                if not isinstance(payload, dict):
                    raise ValueError("respuesta no es un objeto JSON")
                volumes = payload.get("items", [])
                if not isinstance(volumes, list):
                    raise ValueError("items no es lista")
                for item in volumes:
                    stats["seen"] += 1
                    if not isinstance(item, dict):
                        stats["ignored"] += 1
                        continue
                    book = google_books_candidate(item, allowed)
                    if book is None:
                        stats["ignored"] += 1
                        continue
                    stats["eligible"] += 1
                    if book["isbn13"] in existing:
                        stats["already_published"] += 1
                        continue
                    book["fuente"] = "google_books"
                    if merge_candidate(state, book, today):
                        stats["new"] += 1
                    else:
                        stats["unchanged"] += 1
                if len(volumes) < per_page:
                    break
            except (ValueError, KeyError, RuntimeError, OSError) as exc:
                stats["errors"].append({"publisher": slug, "page": page,
                                        "error": str(exc)[:250]})
                break
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--fixture", type=Path, help="JSON de respuestas, no hace HTTP")
    parser.add_argument("--editoriales", type=Path, default=_DEFAULT_EDITORIALES,
                        help="Registro de sellos existente de la web")
    parser.add_argument("--live", action="store_true",
                        help="Habilita llamadas API si config.google_books.enabled=true")
    parser.add_argument("--max-requests", type=int, default=30)
    parser.add_argument("--state", type=Path, default=_DEFAULT_STATE)
    parser.add_argument("--out", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--write-state", action="store_true",
                        help="Guarda staging durable; si no, solo emite informe")
    parser.add_argument("--today", help="Fecha de prueba ISO; default Europe/Madrid")
    args = parser.parse_args()
    config = read_json(args.config)
    config["publishers"] = resolve_publishers(read_json(args.editoriales),
                                             config.get("publishers", []))
    if bool(args.fixture) == bool(args.live):
        parser.error("Elegir exactamente una opción: --fixture o --live")
    if args.live and not config.get("google_books", {}).get("enabled"):
        parser.error("Conector Google Books deshabilitado en config")
    key = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()
    if args.live and not key:
        parser.error("Falta GOOGLE_BOOKS_API_KEY en entorno")
    today = args.today or datetime.now(ZoneInfo("Europe/Madrid")).date().isoformat()
    # Validate injected clock before persisting state.
    from datetime import date
    date.fromisoformat(today)
    state = read_json(args.state, {"schema_version": 1, "items": {}})
    if state.get("schema_version") != 1 or not isinstance(state.get("items"), dict):
        parser.error("Formato de estado no compatible")
    fixtures = read_json(args.fixture) if args.fixture else None
    stats = discover(config, fixture=fixtures, api_key=key,
                     max_requests=min(args.max_requests,
                                      int(config.get("google_books", {}).get("max_requests_per_run", 30))),
                     existing=existing_isbns(ROOT / "data/reading-catalogue.json"),
                     state=state, today=today)
    report = {
        "mode": "fixture" if fixtures is not None else "live",
        "stats": stats,
        "items": [state["items"][k] for k in sorted(state["items"])],
        "note": "Solo candidatos; NO indica existencia en Amazon ni publica fichas."
    }
    write_if_changed(args.out, report)
    if args.write_state:
        write_if_changed(args.state, state)
    print(json.dumps(stats, ensure_ascii=False, sort_keys=True))
    # Failure of one publisher doesn't prevent others; overall failure if no useful response.
    if stats["requests"] == 0 or (stats["errors"] and stats["eligible"] == 0):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
