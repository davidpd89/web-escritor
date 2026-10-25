#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from hashlib import sha256
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "press-kit" / "package-manifest.json"
ALLOWED_RELEASE = {"approved"}


def parse_args():
    p = ArgumentParser(description="Construye un press-kit ZIP reproducible desde datos y assets canónicos.")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--check", action="store_true", help="Valida inputs y, si el ZIP existe, comprueba que está actualizado.")
    p.add_argument("--output", help="Sobrescribe la ruta output del manifiesto (útil en fixtures).")
    return p.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rel(raw: str) -> str:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"ruta no permitida en ZIP/manifiesto: {raw!r}")

    forbidden = set('\\:<>"|?*')
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        *(f'COM{i}' for i in range(1, 10)),
        *(f'LPT{i}' for i in range(1, 10)),
    }
    parts = raw.split('/')

    if (
        raw.startswith('/')
        or any(ch in forbidden or ord(ch) < 32 or ord(ch) == 127 for ch in raw)
        or any(
            not part
            or part in ('.', '..')
            or part.endswith(('.', ' '))
            or part.split('.')[0].upper() in reserved
            for part in parts
        )
    ):
        raise ValueError(f"ruta no permitida en ZIP/manifiesto: {raw!r}")

    return PurePosixPath(raw).as_posix()


def zip_info(name: str, stamp: tuple[int, int, int, int, int, int]) -> ZipInfo:
    info = ZipInfo(filename=safe_rel(name), date_time=stamp)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def canonical_stamp(book: dict, author: dict):
    dates = [
        datetime.fromisoformat(raw)
        for raw in (book.get("lastUpdated"), author.get("lastUpdated"))
        if raw
    ]
    dt = max(dates) if dates else datetime.fromisoformat("2026-01-01")
    return (dt.year, dt.month, dt.day, 0, 0, 0)


def normalized_json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def make_readme(book: dict, author: dict, manifest: dict) -> bytes:
    contact = author.get("contact") or {}
    contact_page = str(contact.get("contactPage") or "").strip()
    email = str(contact.get("email") or "").strip()
    press_page = str(contact.get("pressKit") or "").strip()
    contact_value = f"[{contact_page}]({contact_page})" if contact_page else email
    press_value = f"[{press_page}]({press_page})" if press_page else ""
    genres = ", ".join(book.get("genres", []))
    lines = [
        "KIT DE PRENSA — DAVID PORTO D\u00cdAZ / LAS MANECILLAS DEL RECUERDO",
        "=" * 67,
        "",
        f"Autor: {author.get('name', '')}",
        f"Web: {author.get('website', '')}",
        f"Contacto de prensa: {contact_value}",
        "",
        f"Título: {book.get('title', '')}",
        f"Editorial: {book.get('publisher', '')}",
        f"Fecha de publicación: {book.get('publicationDate', '')}",
        f"ISBN: {book.get('isbn', '')}",
        f"Extensión de maqueta: {book.get('pages', '')} páginas",
        f"PVP comunicado: {book.get('priceEUR', '')} EUR",
        f"Géneros/posicionamiento: {genres}",
        "",
        "SINOPSIS BREVE",
        book.get("synopsis", {}).get("short", ""),
        "",
        "BIO BREVE",
        author.get("shortBio", ""),
        "",
        "CONTENIDO DEL PAQUETE",
    ]
    for asset in manifest.get("assets", []):
        if asset.get("releaseStatus") in ALLOWED_RELEASE:
            lines.append(f"- {asset.get('archivePath')}: {asset.get('label', '')}")
    lines += [
        "- datos/: fichas JSON usadas para generar este paquete",
        "- CHECKSUMS_SHA256.txt: hashes de integridad",
        "- MANIFEST.json: manifiesto exacto del paquete",
        "",
        "USO",
        "Material preparado para información, reseñas, entrevistas, librerías, bibliotecas y cobertura editorial.",
        "No alterar la portada ni atribuir al autor/editorial datos que no aparezcan en las fichas incluidas.",
        "Para una versión actualizada, usar siempre la página oficial de prensa.",
        "",
        f"Página de prensa: {press_value}",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def valid_isbn(value):
    if not isinstance(value, str):
        return False
    if not re.fullmatch(r'[0-9Xx -]+', value, flags=re.ASCII):
        return False
    if not re.fullmatch(r'[0-9Xx]+(?:[- ][0-9Xx]+)*', value, flags=re.ASCII):
        return False
    code = value.replace('-', '').replace(' ', '').upper()
    if len(code) == 10:
        if not re.fullmatch(r'[0-9]{9}[0-9X]', code, flags=re.ASCII):
            return False
        return sum((10 - i) * (10 if ch == 'X' else int(ch)) for i, ch in enumerate(code)) % 11 == 0
    if len(code) == 13 and code.isascii() and code.isdecimal():
        return sum(int(ch) * (1 if i % 2 == 0 else 3) for i, ch in enumerate(code)) % 10 == 0
    return False


def valid_price(value):
    return (type(value) in (int, float)
            and math.isfinite(value)
            and value >= 0)


def valid_pages(value):
    return type(value) is int and value > 0


def validate(manifest: dict, book: dict, author: dict, editorial: dict):
    errors = []
    incident = editorial.get("knownEditorialIncident", {})
    if incident.get("status") != "resolved":
        errors.append("incidencia editorial de cubierta no resuelta")

    seen_archives = set()
    for item in manifest.get("assets", []):
        source = ROOT / safe_rel(item["source"])
        archive = safe_rel(item["archivePath"])
        if archive in seen_archives:
            errors.append(f"archivePath duplicado: {archive}")
        seen_archives.add(archive)
        if item.get("required") and item.get("releaseStatus") not in ALLOWED_RELEASE:
            errors.append(f"asset obligatorio no autorizado: {item['source']} ({item.get('releaseStatus')})")
        if not source.exists():
            errors.append(f"falta asset: {item['source']}")

    for item in manifest.get("documents", []):
        source = ROOT / safe_rel(item["source"])
        archive = safe_rel(item["archivePath"])
        if archive in seen_archives:
            errors.append(f"archivePath duplicado: {archive}")
        seen_archives.add(archive)
        if not source.exists():
            errors.append(f"falta documento: {item['source']}")

    if not book.get("title") or not book.get("isbn") or not book.get("publicationDate"):
        errors.append("faltan hechos mínimos del libro")
    contact = author.get("contact") or {}
    email = str(contact.get("email") or "").strip()
    contact_page = str(contact.get("contactPage") or "").strip()
    if not author.get("name") or not (email or contact_page.startswith("https://") and len(contact_page) > len("https://")):
        errors.append("faltan hechos mínimos del autor/contacto")

    canon = editorial.get("books", {}).get("lasManecillasDelRecuerdo", {})
    for source, facts, pages_key in (
        ('press-kit', book, 'pages'),
        ('editorial-facts', canon, 'numberOfPages'),
    ):
        if not valid_pages(facts.get(pages_key)):
            errors.append(f'{source}: paginas invalidas: {facts.get(pages_key)!r}')
        if not valid_price(facts.get('priceEUR')):
            errors.append(f'{source}: PVP invalido: {facts.get("priceEUR")!r}')
        if not valid_isbn(facts.get('isbn')):
            errors.append(f'{source}: ISBN invalido: {facts.get("isbn")!r}')

    comparisons = [
        ("title", book.get("title"), canon.get("title")),
        ("publisher", book.get("publisher"), canon.get("publisher")),
        ("publicationDate", book.get("publicationDate"), canon.get("publicationDate")),
        ("numberOfPages", book.get("pages"), canon.get("numberOfPages")),
    ]
    for label, packaged, canonical in comparisons:
        if packaged != canonical:
            errors.append(f"deriva entre press-kit y editorial-facts en {label}: {packaged!r} != {canonical!r}")
    digits = lambda value: "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits(book.get("isbn")) != digits(canon.get("isbn")):
        errors.append("deriva entre press-kit y editorial-facts en ISBN")
    press_price = book.get("priceEUR")
    if press_price != canon.get("priceEUR"):
        errors.append(f"deriva entre press-kit y editorial-facts en PVP: {press_price!r} != {canon.get('priceEUR')!r}")
    return errors


def build_bytes(manifest: dict, book: dict, author: dict) -> tuple[bytes, list[tuple[str, str]]]:
    import io
    buffer = io.BytesIO()
    stamp = canonical_stamp(book, author)
    checksums: list[tuple[str, str]] = []

    entries: list[tuple[str, bytes]] = []
    entries.append(("README.txt", make_readme(book, author, manifest)))
    entries.append(("MANIFEST.json", normalized_json_bytes(manifest)))

    for item in manifest.get("documents", []):
        data = (ROOT / safe_rel(item["source"])).read_bytes()
        entries.append((safe_rel(item["archivePath"]), data))
    for item in manifest.get("assets", []):
        if item.get("releaseStatus") not in ALLOWED_RELEASE:
            continue
        data = (ROOT / safe_rel(item["source"])).read_bytes()
        entries.append((safe_rel(item["archivePath"]), data))

    entries.sort(key=lambda x: x[0])
    for name, data in entries:
        checksums.append((name, sha256(data).hexdigest()))

    checksum_bytes = "".join(f"{digest}  {name}\n" for name, digest in checksums).encode("utf-8")
    entries.append(("CHECKSUMS_SHA256.txt", checksum_bytes))
    entries.sort(key=lambda x: x[0])

    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in entries:
            zf.writestr(zip_info(name, stamp), data)
    return buffer.getvalue(), checksums


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest).resolve()
    try:
        manifest = load_json(manifest_path)
        book = load_json(ROOT / safe_rel(manifest["bookFacts"]))
        author = load_json(ROOT / safe_rel(manifest["authorFacts"]))
        editorial = load_json(ROOT / safe_rel(manifest["editorialFacts"]))
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"PRESS KIT: FAILED\n- {exc}")
        return 1

    errors = validate(manifest, book, author, editorial)
    if errors:
        print("PRESS KIT: BLOCKED")
        for err in errors:
            print(f"- {err}")
        return 1

    payload, _ = build_bytes(manifest, book, author)
    max_bytes = int(manifest.get("maxPackageBytes", 0) or 0)
    if max_bytes and len(payload) > max_bytes:
        print(f"PRESS KIT: FAILED — {len(payload)} bytes supera maxPackageBytes={max_bytes}")
        return 1
    output = Path(args.output).resolve() if args.output else ROOT / safe_rel(manifest["output"])

    if args.check:
        if not output.exists():
            print(f"PRESS KIT: STALE — falta {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
            return 1
        if output.read_bytes() != payload:
            print("PRESS KIT: STALE — el ZIP no coincide con fuentes/manifest")
            return 1
        print("PRESS KIT: OK")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    print(f"PRESS KIT: BUILT {output} · {len(payload)} bytes · sha256={sha256(payload).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
