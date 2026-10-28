#!/usr/bin/env python3
"""Alimenta el directorio del Atlas con lugares literarios de Wikidata (CC0).

Consulta el servicio SPARQL público por tipo de lugar y país, aplica filtros de
calidad (notoriedad por sitelinks, web oficial HTTPS, coordenadas, etiqueta) y
escribe `data/atlas/directory.json`. Las entradas del directorio se publican sin
ficha propia: tarjeta en el catálogo con su web oficial. Nunca crea relaciones
obra-lugar: esas necesitan evidencia y pasan por la capa editorial.

Uso:
  python scripts/atlas_wikidata_feed.py --apply              # consulta y escribe
  python scripts/atlas_wikidata_feed.py                      # consulta y muestra el resumen
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "data" / "atlas" / "feed-config.json"
OUTPUT = ROOT / "data" / "atlas" / "directory.json"
ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "web-escritor-atlas/1.0 (https://davidportodiaz.com; datos CC0 de Wikidata)"
QID = re.compile(r"^Q[1-9][0-9]*$")
SHORTENERS = {"bit.ly", "t.co", "goo.gl", "tinyurl.com", "linktr.ee", "facebook.com", "instagram.com"}
PLACE_TYPES = {"bookshop", "library", "museum", "writer_house_museum", "booktown", "festival", "historic_site"}


class FeedError(Exception):
    pass


def slugify(text: str) -> str:
    plain = "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def sparql(kind_qid: str, isos: list[str], min_sitelinks: int, limit: int) -> str:
    values = " ".join(f'"{iso}"' for iso in isos)
    return f"""
SELECT ?item ?itemLabel ?itemDescription ?cityLabel ?coord ?website ?sitelinks ?iso WHERE {{
  VALUES ?iso {{ {values} }}
  ?country wdt:P297 ?iso .
  ?item wdt:P31 wd:{kind_qid} ; wdt:P17 ?country ; wdt:P625 ?coord ; wdt:P856 ?website ;
        wikibase:sitelinks ?sitelinks .
  FILTER(?sitelinks >= {min_sitelinks})
  OPTIONAL {{ ?item wdt:P131 ?city . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en,mul". }}
}}
ORDER BY DESC(?sitelinks)
LIMIT {limit}
""".strip()


def run_query(query: str, timeout: int = 60, attempts: int = 4, sleep=time.sleep) -> dict:
    """Una consulta con reintentos: 429/503 respetan Retry-After (máx. 90 s) y suben el tiempo de espera."""
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - endpoint fijo
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 503) or attempt == attempts:
                raise
            try:
                wait = float(exc.headers.get("Retry-After", ""))
            except ValueError:
                wait = 0.0
            sleep(min(90.0, max(wait, 10.0 * attempt)))
    raise FeedError("sin respuesta")


def valid_website(value: object) -> bool:
    if not isinstance(value, str) or re.search(r"[\s<>\x00-\x1f]", value):
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    host = (parts.hostname or "").lower()
    return (parts.scheme == "https" and bool(host) and "." in host and not parts.username and not parts.password
            and parts.port in (None, 443) and host.removeprefix("www.") not in SHORTENERS
            and not re.fullmatch(r"[\d.]+", host))


def parse_coord(value: str) -> tuple[float, float] | None:
    match = re.fullmatch(r"Point\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)", value.strip())
    if not match:
        return None
    lon, lat = float(match.group(1)), float(match.group(2))
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None


def parse_row(row: dict, place_type: str, iso2: str, min_sitelinks: int) -> dict | None:
    """Convierte una fila SPARQL en una entrada del directorio, o None si no pasa los filtros."""
    def val(key: str) -> str:
        return (row.get(key) or {}).get("value", "")

    qid = val("item").rsplit("/", 1)[-1]
    label = val("itemLabel").strip()
    city = val("cityLabel").strip()
    website = val("website").strip()
    coord = parse_coord(val("coord"))
    try:
        links = int(val("sitelinks"))
    except ValueError:
        return None
    if (not QID.fullmatch(qid) or not label or QID.fullmatch(label) or len(label) > 120
            or not city or QID.fullmatch(city) or len(city) > 80
            or not valid_website(website) or coord is None or links < min_sitelinks):
        return None
    description = val("itemDescription").strip()
    return {
        "qid": qid, "name": label, "city": city, "country_iso2": iso2, "place_type": place_type,
        "official_url": website, "latitude": round(coord[0], 5), "longitude": round(coord[1], 5),
        "sitelinks": links, "description": description[:200] if description and not QID.fullmatch(description) else "",
    }


def collect(config: dict, query_fn=run_query, sleep=time.sleep, clock=time.monotonic) -> tuple[list[dict], list[str]]:
    """Una consulta por tipo y grupo de países (`countries_per_query`, 1 por defecto: las consultas de
    varios países a la vez agotan el tiempo de WDQS en los tipos más comunes); tope por país al leer."""
    found: dict[str, dict] = {}
    errors: list[str] = []
    per_country = int(config["limit_per_query"])
    batch_size = max(1, int(config.get("countries_per_query", 1)))
    countries = list(config["countries"])
    batches = [countries[i:i + batch_size] for i in range(0, len(countries), batch_size)]
    deadline = clock() + float(config.get("max_runtime_seconds", 7200))
    for kind in config["kinds"]:
        min_links = kind.get("min_sitelinks", config["min_sitelinks"])
        for batch in batches:
            label = f"{kind['place_type']}/{'+'.join(batch)}"
            if clock() > deadline:  # el resto queda para la semana siguiente; lo ya visto se conserva en merge()
                errors.append(f"{label}: tiempo agotado")
                continue
            try:
                data = query_fn(sparql(kind["qid"], batch, min_links, per_country * len(batch)))
            except Exception as exc:  # red caída, límite de peticiones o consulta lenta: se sigue con el resto
                errors.append(f"{label}: {type(exc).__name__}")
                sleep(config.get("delay_seconds", 2))
                continue
            taken: dict[str, int] = {}
            for row in data.get("results", {}).get("bindings", []):
                iso = (row.get("iso") or {}).get("value", "") or (batch[0] if len(batch) == 1 else "")
                if iso not in batch:
                    continue
                entry = parse_row(row, kind["place_type"], iso, min_links)
                if not entry or taken.get(iso, 0) >= per_country:
                    continue
                if entry["qid"] not in found or entry["sitelinks"] > found[entry["qid"]]["sitelinks"]:
                    found[entry["qid"]] = entry
                taken[iso] = taken.get(iso, 0) + 1
            sleep(config.get("delay_seconds", 2))
    return sorted(found.values(), key=lambda e: (e["country_iso2"], e["place_type"], -e["sitelinks"], e["name"])), errors


def merge(previous: dict, fresh: list[dict], today: str, config: dict) -> dict:
    """Conserva lo anterior: tope de altas por ejecución y baja solo tras `keep_days` sin verse."""
    old = {e["qid"]: e for e in previous.get("places", [])}
    keep_days = int(config.get("keep_days", 30))
    max_new = int(config.get("max_new_per_run", 60))
    merged: dict[str, dict] = {}
    added = 0
    for entry in fresh:
        known = old.get(entry["qid"])
        if known is None:
            if added >= max_new:
                continue
            added += 1
            entry = {**entry, "first_seen": today}
        else:
            entry = {**entry, "first_seen": known.get("first_seen", today)}
        merged[entry["qid"]] = {**entry, "last_seen": today}
    for qid, known in old.items():
        if qid in merged:
            continue
        age = (date.fromisoformat(today) - date.fromisoformat(known.get("last_seen", today))).days
        if age < keep_days:
            merged[qid] = known
    places = sorted(merged.values(), key=lambda e: (e["country_iso2"], e["place_type"], -e["sitelinks"], e["name"]))
    return {"schema_version": 1, "updated": today, "source": "Wikidata (CC0 1.0)", "places": places}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Escribe data/atlas/directory.json")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    previous = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.is_file() else {"places": []}
    fresh, errors = collect(config)
    size = max(1, int(config.get("countries_per_query", 1)))
    queries = len(config["kinds"]) * -(-len(config["countries"]) // size)
    if len(errors) > queries // 2:
        print(f"FAIL: demasiadas consultas fallidas ({len(errors)}/{queries}); no se escribe nada", file=sys.stderr)
        return 1
    today = datetime.now(timezone.utc).date().isoformat()
    result = merge(previous, fresh, today, config)
    print(json.dumps({"consultas": queries, "errores": errors, "encontrados": len(fresh), "en_directorio": len(result["places"])}, ensure_ascii=False))
    if args.apply:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
