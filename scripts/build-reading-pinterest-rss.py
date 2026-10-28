#!/usr/bin/env python3
"""Genera feeds RSS 2.0 nativos para Pinterest desde fichas WEB publicadas.

SIN API de Pinterest, SIN acceso Amazon, SIN IA, SIN publicación remota.
Pinterest puede consumir cada feed en su tablero después de conectarlo
MANUALMENTE en una cuenta Business con davidportodiaz.com reclamado.

Uso:
  python scripts/build-reading-pinterest-rss.py --preview
  python scripts/build-reading-pinterest-rss.py --assign
  python scripts/build-reading-pinterest-rss.py --check

--assign mantiene en data/reading-pinterest-state.json un registro estable:
hasta N libros nuevos por fecha civil, no 100 pines el primer día.
--check no escribe archivos y detecta cambios en XML/state.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, datetime, time, timezone, timedelta
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path("data/reading-pinterest-boards.json")
CATALOG = Path("data/reading-catalogue.json")
STATE = Path("data/reading-pinterest-state.json")
OUTPUT = Path("assets/pinterest/feeds")
MEDIA_NS = "http://search.yahoo.com/mrss/"
ET.register_namespace("media", MEDIA_NS)

ALLOWED_IMAGE_EXTENSIONS = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                            ".png": "image/png", ".webp": "image/webp"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def json_read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def as_day(text: str) -> date | None:
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def source_categories(dataset: dict) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for pair in dataset.get("libro_categorias", []):
        result.setdefault(pair["libro_id"], set()).add(pair["categoria_id"])
    return result


def suitable_books(root: Path, data: dict, board_config: dict, today: date,
                   state: dict | None = None) -> list[dict]:
    """Only published pages; keep the originally assigned board on future runs."""
    categories = source_categories(data)
    pinned = (state or {}).get("pins", {})
    board_by_slug = {board["slug"]: board for board in board_config["boards"]}
    results = []
    for book in data.get("libros", []):
        if book.get("estado") != "publicado":
            continue
        book_id, slug = book.get("id", ""), book.get("slug", "")
        if not SLUG.fullmatch(slug) or not book_id:
            continue
        page = root / "recomendaciones" / "libros" / slug / "index.html"
        if not page.is_file():
            continue
        image = book.get("portada_local", "")
        if not isinstance(image, str) or not image.startswith("/assets/"):
            continue
        if ".." in Path(image).parts or Path(image).suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        if not (root / image.lstrip("/")).is_file():
            continue
        if not book.get("titulo") or not book.get("autores") or not book.get("descripcion_breve"):
            continue
        # A queued item must never move to another RSS feed just because
        # its 90-day novelty window expires or new categories are attached.
        queued = pinned.get(book_id)
        assigned = board_by_slug.get(queued.get("board_slug")) if isinstance(queued, dict) else None
        published = as_day(book.get("fecha_publicacion", ""))
        for board in ([] if assigned else sorted(board_config["boards"], key=lambda b: b["priority"])):
            book_cats = categories.get(book_id, set())
            category_match = bool(book_cats & set(board.get("categories", [])))
            is_recent = bool(
                board.get("recent_days") and published is not None
                and 0 <= (today - published).days < board["recent_days"]
            )
            if board.get("recent_days"):
                # "Novedades de fantasía" never takes unrelated new books.
                matches = is_recent and (
                    category_match if board.get("category_match_mode") == "date_and_category"
                    else True
                )
            else:
                matches = category_match or board.get('match_all', False)
            if matches:
                assigned = board
                break
        if assigned:
            results.append({"book": book, "board": assigned, "image": image})
    return sorted(results, key=lambda r: (r["book"].get("fecha_actualizacion", ""),
                                          r["book"]["id"]))


def assign_queue(entries: list[dict], state: dict, today: date, budget: int) -> bool:
    """Stable one-book/one-board schedule, max budget over ALL feeds per day."""
    if type(budget) is not int or not 1 <= budget <= 20:
        raise ValueError("daily_new_pin_budget debe estar entre 1 y 20")
    pins = state.setdefault("pins", {})
    allocated = Counter(entry["scheduled_date"] for entry in pins.values()
                        if isinstance(entry, dict) and entry.get("scheduled_date"))
    # New candidates must not jump ahead of an existing future backlog.
    backlog = [as_day(day) for day in allocated]
    backlog = [day for day in backlog if day is not None and day >= today]
    next_available = max(backlog, default=today)
    changed = False
    for entry in entries:
        book = entry["book"]
        if book["id"] in pins:
            continue
        candidate_day = next_available
        while allocated[candidate_day.isoformat()] >= budget:
            candidate_day += timedelta(days=1)
        key = candidate_day.isoformat()
        next_available = candidate_day
        pins[book["id"]] = {
            "book_id": book["id"],
            "slug": book["slug"],
            "board_slug": entry["board"]["slug"],
            "scheduled_date": key,
            "guid": f"urn:davidportodiaz:pinterest:libro:{book['id']}:v1"
        }
        allocated[key] += 1
        changed = True
    return changed


def rss_text(title: str, max_length: int) -> str:
    title = " ".join(str(title).split())
    if len(title) <= max_length:
        return title
    return title[:max_length - 1].rsplit(" ", 1)[0].rstrip(".,;: ") + "…"


def pin_title(book: dict, board: dict) -> str:
    # Descriptive search terms only. No invented personal endorsement/reading.
    return rss_text(f"{book['titulo']}: {board['keyword']}", 100)


def pin_description(book: dict, board: dict) -> str:
    authors = ", ".join(book["autores"])
    synopsis = rss_text(book.get('sinopsis_breve') or book["descripcion_breve"], 470)
    return rss_text(
        f"{synopsis} Ficha de {book['titulo']}, de {authors}: "
        f"edición, géneros, sinopsis y enlaces de lectura disponibles. "
        f"Explora más {board['keyword']} en davidportodiaz.com.", 800
    )


def target_url(site: str, slug: str, book_id: str, board_slug: str) -> str:
    url = site.rstrip("/") + f"/recomendaciones/libros/{slug}/"
    query = urlencode({"utm_source": "pinterest", "utm_medium": "organic",
                       "utm_campaign": board_slug, "utm_content": book_id})
    return url + "?" + query


def build_feed(board: dict, entries: list[dict], state: dict,
               today: date, site: str, cap: int) -> str:
    root = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(root, "channel")
    for tag, value in (("title", board["name"]),
                       ("link", site + "/recomendaciones/"),
                       ("description", board["description"]),
                       ("language", "es-ES")):
        ET.SubElement(ch, tag).text = value
    ready = []
    for entry in entries:
        book = entry["book"]
        queued = state.get("pins", {}).get(book["id"])
        if queued is None or queued["board_slug"] != board["slug"]:
            continue
        if queued["scheduled_date"] > today.isoformat():
            continue
        ready.append((queued["scheduled_date"], book["id"], entry, queued))
    # Only the most recently queued items; output oldest first, as Pinterest processes.
    ready = sorted(ready)[-cap:]
    for _date, _id, entry, queued in ready:
        book = entry["book"]
        item = ET.SubElement(ch, "item")
        ET.SubElement(item, "title").text = pin_title(book, board)
        ET.SubElement(item, "description").text = pin_description(book, board)
        ET.SubElement(item, "link").text = target_url(site, book["slug"], book["id"], board["slug"])
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = queued["guid"]
        dt = datetime.combine(date.fromisoformat(queued["scheduled_date"]),
                              time(hour=9), tzinfo=timezone.utc)
        ET.SubElement(item, "pubDate").text = format_datetime(dt, usegmt=True)
        path = entry["image"]
        ET.SubElement(item, f"{{{MEDIA_NS}}}content", {
            "url": site + path,
            "type": ALLOWED_IMAGE_EXTENSIONS[Path(path).suffix.lower()]
        })
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def expected_files(root: Path, config: dict, data: dict, state: dict,
                   today: date) -> tuple[dict[Path, str], list[dict]]:
    if config.get("schema_version") != 1 or state.get("schema_version") != 1:
        raise ValueError("Schema de feeds o cola incompatible")
    site = config.get("site")
    url = urlsplit(site)
    if url.scheme != "https" or url.hostname != "davidportodiaz.com" or url.path:
        raise ValueError("Site debe ser https://davidportodiaz.com")
    entries = suitable_books(root, data, config, today, state=state)
    # When RSS is disabled, publish valid empty RSS channels only. Existing
    # queued books MUST NOT leak into Pinterest on accidental feed connection.
    if not config.get("rss_enabled", False):
        entries = []
    elif config.get("pilot_book_id"):
        # Activate at most ONE real book while validating the RSS connection.
        entries = [entry for entry in entries
                   if entry["book"]["id"] == config["pilot_book_id"]]
    cap = int(config.get("max_feed_items_per_board", 150))
    if not 1 <= cap <= 500:
        raise ValueError("Cap de elementos inválido")
    outputs = {}
    for board in config["boards"]:
        slug = board["slug"]
        if not SLUG.fullmatch(slug):
            raise ValueError("Slug de tablero inválido")
        outputs[root / OUTPUT / (slug + ".xml")] = build_feed(
            board, entries, state, today, site, cap)
    return outputs, entries


def write_if_changed(path: Path, data: str, *, check: bool) -> bool:
    if path.is_file() and path.read_text(encoding="utf-8") == data:
        return False
    if check:
        raise RuntimeError(f"RSS/cola desactualizado: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", help="Fecha ISO de prueba; por defecto Europe/Madrid")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--assign", action="store_true",
                      help="Añade hasta 2 nuevos pines al día a la cola; nunca publica")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--preview", action="store_true",
                      help="Mostrar asignaciones sin escribir ni conectar Pinterest")
    args = parser.parse_args()
    from zoneinfo import ZoneInfo
    today = date.fromisoformat(args.today) if args.today else datetime.now(
        ZoneInfo("Europe/Madrid")).date()
    root = args.root.resolve()
    config = json_read(root / CONFIG)
    data = json_read(root / CATALOG)
    state = json_read(root / STATE) if (root / STATE).exists() else {
        "schema_version": 1, "pins": {}
    }
    # Preview evaluates the hypothetical eligible content with RSS enabled,
    # but NEVER changes the actual activation flag or writes XML/state.
    evaluation_config = {**config, "rss_enabled": True} if args.preview else config
    outputs, eligible = expected_files(root, evaluation_config, data, state, today)
    if args.assign:
        if not config.get("rss_enabled", False):
            parser.error("RSS desactivado: no se asignan pines; activar solo tras conexión con Pinterest.")
        assign_queue(eligible, state, today, int(config["daily_new_pin_budget"]))
        outputs, _ = expected_files(root, config, data, state, today)
        write_if_changed(root / STATE, json.dumps(
            state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", check=False)
    if args.preview:
        # Report what WOULD be queued, without changing state or RSS on disk.
        preview_state = json.loads(json.dumps(state))
        assign_queue(eligible, preview_state, today, int(config["daily_new_pin_budget"]))
        print(json.dumps({"eligible": len(eligible), "queue": preview_state["pins"],
                          "feeds": [p.relative_to(root).as_posix() for p in outputs]},
                         ensure_ascii=False, indent=2))
        return 0
    changed = sum(write_if_changed(path, content, check=args.check)
                  for path, content in outputs.items())
    print(f"Pinterest RSS: {len(eligible)} fichas elegibles, {len(outputs)} feeds, "
          f"{changed} XML modificados; no se ha enviado nada a Pinterest.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, RuntimeError, OSError) as exc:
        print(f"Pinterest RSS: {exc}", file=sys.stderr)
        sys.exit(1)
