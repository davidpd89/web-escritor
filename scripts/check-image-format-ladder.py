#!/usr/bin/env python3
"""Gate de formato/procedencia AVIF->WebP (L.1, 2026-08-23).

Responsabilidad de #67:
- existencia de fuente WebP y derivada AVIF;
- procedencia/frescura por SHA-256 de ambos ficheros;
- igualdad de dimensiones entre ambos formatos;
- correspondencia AVIF/WebP y orden de la escalera en <picture>.

No duplica #61: width/height HTML, srcset/sizes, loading y fetchpriority
siguen siendo responsabilidad de scripts/check-responsive-images.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import PIL
    from PIL import Image
except ImportError:  # pragma: no cover - CI instala scripts/requirements.txt
    PIL = None
    Image = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel and "lab/" not in rel and "lab\\" not in rel]


def src_urls(tag: str) -> list[str]:
    match = re.search(r'(?:srcset|src)="([^"]*)"', tag, re.I)
    if not match:
        return []
    value = match.group(1).strip()
    if "srcset=" in match.group(0).lower():
        return [candidate.strip().split()[0] for candidate in value.split(",") if candidate.strip()]
    return [value] if value else []


def manifest_errors(manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 2:
        errors.append("manifest: schema_version debe ser 2")
    encoder = manifest.get("encoder")
    if not isinstance(encoder, dict):
        errors.append("manifest: falta encoder")
    else:
        if encoder.get("format") != "AVIF":
            errors.append("manifest: encoder.format debe ser AVIF")
        if not isinstance(encoder.get("quality"), int):
            errors.append("manifest: encoder.quality debe ser entero")
        expected_pillow = encoder.get("pillow_version")
        if not isinstance(expected_pillow, str) or not expected_pillow:
            errors.append("manifest: falta encoder.pillow_version")
        elif PIL is not None and PIL.__version__ != expected_pillow:
            errors.append(
                f"entorno: Pillow {PIL.__version__} no coincide con la version fijada {expected_pillow}; "
                "instala scripts/requirements.txt"
            )
    entries = manifest.get("eligible_sources")
    if not isinstance(entries, list) or not entries:
        errors.append("manifest: eligible_sources debe ser una lista no vacia")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if PIL is None or Image is None:
        print("ERROR entorno: Pillow no disponible; instala scripts/requirements.txt")
        return 1

    manifest = json.loads((root / "data" / "image-format-ladder.json").read_text(encoding="utf-8"))
    errors = manifest_errors(manifest)
    entries = manifest.get("eligible_sources") if isinstance(manifest.get("eligible_sources"), list) else []

    source_by_basename: dict[str, dict] = {}
    seen_sources: set[str] = set()
    seen_derivatives: set[str] = set()

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"manifest: eligible_sources[{index}] debe ser un objeto")
            continue
        source_rel = entry.get("source")
        derivative_rel = entry.get("derivative")
        source_hash = entry.get("source_sha256")
        derivative_hash = entry.get("derivative_sha256")
        if not isinstance(source_rel, str) or not source_rel.endswith(".webp"):
            errors.append(f"manifest: eligible_sources[{index}].source debe ser WebP")
            continue
        if not isinstance(derivative_rel, str) or not derivative_rel.endswith(".avif"):
            errors.append(f"{source_rel}: derivative debe ser AVIF")
            continue
        expected_derivative = Path(source_rel).with_suffix(".avif").as_posix()
        if derivative_rel != expected_derivative:
            errors.append(f"{source_rel}: derivative debe ser el hermano {expected_derivative}")
        if source_rel in seen_sources:
            errors.append(f"{source_rel}: fuente duplicada en manifest")
        if derivative_rel in seen_derivatives:
            errors.append(f"{derivative_rel}: derivada duplicada en manifest")
        seen_sources.add(source_rel)
        seen_derivatives.add(derivative_rel)
        source_by_basename[Path(source_rel).name] = entry

        source = root / source_rel
        derivative = root / derivative_rel
        if not source.exists():
            errors.append(f"{source_rel}: fuente WebP no existe")
            continue
        if not derivative.exists():
            errors.append(f"{source_rel}: falta el AVIF hermano ({derivative_rel})")
            continue

        actual_source_hash = sha256_file(source)
        actual_derivative_hash = sha256_file(derivative)
        if not isinstance(source_hash, str) or actual_source_hash != source_hash:
            errors.append(
                f"{source_rel}: source_sha256 no coincide; el WebP cambio y la derivada debe regenerarse"
            )
        if not isinstance(derivative_hash, str) or actual_derivative_hash != derivative_hash:
            errors.append(
                f"{source_rel}: derivative_sha256 no coincide; el AVIF fue reemplazado/corrompido o esta obsoleto"
            )
        try:
            with Image.open(source) as webp, Image.open(derivative) as avif:
                if webp.size != avif.size:
                    errors.append(f"{source_rel}: dimensiones no coinciden (webp={webp.size}, avif={avif.size})")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{source_rel}: no se pudieron decodificar/comparar formatos ({exc})")

    tag_re = re.compile(r'<source\b[^>]*>|<img\b[^>]*>', re.I)
    media_re = re.compile(r'media="([^"]*)"', re.I)
    type_re = re.compile(r'type="([^"]*)"', re.I)

    for path in tracked_html(root):
        html = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        tags = list(tag_re.finditer(html))
        for index, match in enumerate(tags):
            tag = match.group(0)
            urls = src_urls(tag)
            matching_name = next(
                (Path(url.split("?", 1)[0]).name for url in urls if Path(url.split("?", 1)[0]).name in source_by_basename),
                None,
            )
            if matching_name is None:
                continue

            entry = source_by_basename[matching_name]
            expected_avif_name = Path(entry["derivative"]).name
            own_media = media_re.search(tag)
            own_media_value = own_media.group(1) if own_media else None
            if index == 0:
                errors.append(f"{rel}: {matching_name} referenciado sin ningun <source> AVIF precedente")
                continue

            previous = tags[index - 1].group(0)
            previous_type = type_re.search(previous)
            if not (previous_type and previous_type.group(1).lower() == "image/avif"):
                errors.append(f"{rel}: {matching_name} no tiene un <source type=\"image/avif\"> inmediatamente antes")
                continue

            previous_urls = src_urls(previous)
            previous_names = {Path(url.split("?", 1)[0]).name for url in previous_urls}
            if expected_avif_name not in previous_names:
                errors.append(
                    f"{rel}: {matching_name} tiene un AVIF precedente que no corresponde; esperado {expected_avif_name}"
                )

            previous_media = media_re.search(previous)
            previous_media_value = previous_media.group(1) if previous_media else None
            if previous_media_value != own_media_value:
                errors.append(
                    f"{rel}: {matching_name} -- el <source> AVIF precedente tiene media='{previous_media_value}', "
                    f"esperado '{own_media_value}'"
                )

    for error in errors:
        print(f"ERROR {error}")
    print(f"\nImage format ladder check: {len(entries)} fuente(s) elegibles, {len(errors)} incumplimiento(s).")
    return 1 if args.check and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
