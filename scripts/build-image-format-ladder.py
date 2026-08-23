#!/usr/bin/env python3
"""Pipeline reproducible de la escalera AVIF -> WebP (L.1, 2026-08-23).

Solo procesa las parejas declaradas en data/image-format-ladder.json.
El WebP es la fuente/fallback y el AVIF su derivada. La procedencia se fija
con SHA-256 de ambos ficheros y con una version/calidad de encoder declaradas
en el manifest. No se usan mtime, fecha de ejecucion ni solo dimensiones.

Usage:
    python scripts/build-image-format-ladder.py
    python scripts/build-image-format-ladder.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import PIL
    from PIL import Image
except ImportError:  # pragma: no cover - el workflow instala requirements.txt
    PIL = None
    Image = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(root: Path) -> tuple[Path, dict]:
    path = root / "data" / "image-format-ladder.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def manifest_contract_errors(manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 2:
        errors.append("manifest: schema_version debe ser 2")
    encoder = manifest.get("encoder")
    if not isinstance(encoder, dict):
        errors.append("manifest: falta encoder")
        return errors
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


def entry_errors(entry: object, index: int) -> list[str]:
    if not isinstance(entry, dict):
        return [f"manifest: eligible_sources[{index}] debe ser un objeto"]
    errors: list[str] = []
    source = entry.get("source")
    derivative = entry.get("derivative")
    if not isinstance(source, str) or not source.endswith(".webp"):
        errors.append(f"manifest: eligible_sources[{index}].source debe ser WebP")
    if not isinstance(derivative, str) or not derivative.endswith(".avif"):
        errors.append(f"manifest: eligible_sources[{index}].derivative debe ser AVIF")
    if isinstance(source, str) and isinstance(derivative, str):
        expected = Path(source).with_suffix(".avif").as_posix()
        if derivative != expected:
            errors.append(f"{source}: derivative debe ser el hermano {expected}")
    for field in ("source_sha256", "derivative_sha256"):
        value = entry.get(field)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            errors.append(f"manifest: eligible_sources[{index}].{field} debe ser SHA-256 hexadecimal")
    return errors


def generate(source: Path, derivative: Path, quality: int) -> None:
    assert Image is not None
    with Image.open(source) as image:
        prepared = image if image.mode in ("RGB", "RGBA") else image.convert("RGB")
        prepared.save(derivative, format="AVIF", quality=quality)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--check", action="store_true", help="no escribe; valida procedencia y frescura")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if PIL is None or Image is None:
        print("ERROR entorno: Pillow no disponible; instala scripts/requirements.txt")
        return 1

    manifest_path, manifest = load_manifest(root)
    errors = manifest_contract_errors(manifest)
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1

    entries = manifest["eligible_sources"]
    quality = manifest["encoder"]["quality"]
    generated: list[str] = []
    changed_manifest = False

    for index, entry in enumerate(entries):
        structural = entry_errors(entry, index)
        if structural:
            errors.extend(structural)
            continue
        assert isinstance(entry, dict)
        source_rel = entry["source"]
        derivative_rel = entry["derivative"]
        source = root / source_rel
        derivative = root / derivative_rel

        if not source.exists():
            errors.append(f"{source_rel}: fuente WebP no existe")
            continue

        source_hash = sha256_file(source)
        source_stale = source_hash != entry["source_sha256"]
        derivative_missing = not derivative.exists()
        derivative_stale = False
        dimensions_stale = False

        if not derivative_missing:
            derivative_stale = sha256_file(derivative) != entry["derivative_sha256"]
            try:
                with Image.open(source) as webp, Image.open(derivative) as avif:
                    dimensions_stale = webp.size != avif.size
            except Exception as exc:  # noqa: BLE001
                derivative_stale = True
                errors.append(f"{source_rel}: derivada AVIF no decodificable ({exc})")
                if args.check:
                    continue

        stale = source_stale or derivative_missing or derivative_stale or dimensions_stale
        if args.check:
            if source_stale:
                errors.append(
                    f"{source_rel}: source_sha256 obsoleto; el WebP cambio y la derivada debe regenerarse"
                )
            if derivative_missing:
                errors.append(f"{source_rel}: falta la derivada AVIF ({derivative_rel})")
            elif derivative_stale:
                errors.append(
                    f"{source_rel}: derivative_sha256 no coincide; el AVIF fue reemplazado/corrompido o esta obsoleto"
                )
            if dimensions_stale:
                errors.append(f"{source_rel}: dimensiones WebP/AVIF no coinciden")
            continue

        if stale:
            try:
                generate(source, derivative, quality)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source_rel}: no se pudo generar {derivative_rel} ({exc})")
                continue
            generated.append(derivative_rel)

        # Tras una generacion (o para una pareja ya valida), la autoridad se
        # actualiza con los bytes reales. No depende de reloj ni metadata FS.
        new_source_hash = sha256_file(source)
        new_derivative_hash = sha256_file(derivative)
        if entry["source_sha256"] != new_source_hash:
            entry["source_sha256"] = new_source_hash
            changed_manifest = True
        if entry["derivative_sha256"] != new_derivative_hash:
            entry["derivative_sha256"] = new_derivative_hash
            changed_manifest = True

    if changed_manifest and not args.check:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for path in generated:
        print(f"REGENERATED {path}")
    for error in errors:
        print(f"ERROR {error}")

    print(
        f"\nFormat ladder: {len(entries)} fuente(s) elegibles, "
        f"{len(generated)} regenerada(s), {len(errors)} error(es)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
