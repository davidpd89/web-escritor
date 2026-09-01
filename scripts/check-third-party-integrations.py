#!/usr/bin/env python3
"""Valida la autoridad de integraciones externas (E.8).

Contratos:
- schema/ids/estados/campos basicos coherentes;
- owner/evidence files existentes y strings de evidencia presentes;
- integraciones browser activas/condicionales permitidas por el CSP publico;
- disclosure de privacidad presente cuando el registro la exige;
- proveedores optional_disabled con activation_gate explicito.

No intenta descubrir todas las URLs externas del repo: enlaces editoriales, afiliados,
documentacion y referencias historicas no son integraciones runtime. La deteccion se
ancla en owners declarados para evitar falsos positivos.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = Path("data/third-party-integrations.json")
ALLOWED_STATUS = {"active", "conditional", "optional_disabled", "retired"}
ALLOWED_LAYER = {"browser", "browser_to_edge", "server_side"}

# El CSP generado usa content="..." y contiene tokens con comillas simples
# ('self', 'none', hashes). No se puede capturar el valor con una clase que
# trate ambos tipos de comilla como terminadores: debe respetarse el delimitador
# real del atributo HTML.
CSP_META_RE = re.compile(
    r'<meta\s+http-equiv=["\']Content-Security-Policy["\'][^>]*\scontent=(?:"([^"]*)"|\'([^\']*)\')',
    re.IGNORECASE,
)


def load_text(root: Path, rel: str, cache: dict[str, str], errors: list[str]) -> str | None:
    if rel in cache:
        return cache[rel]
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        errors.append(f"{rel}: owner fuera del repositorio")
        return None
    if not path.exists() or not path.is_file():
        errors.append(f"{rel}: fichero owner/evidence no existe")
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    cache[rel] = text
    return text


def parse_csp(text: str) -> dict[str, set[str]]:
    match = CSP_META_RE.search(text)
    if not match:
        return {}
    policy = html.unescape(match.group(1) if match.group(1) is not None else match.group(2) or "")
    directives: dict[str, set[str]] = {}
    for chunk in policy.split(";"):
        parts = chunk.strip().split()
        if not parts:
            continue
        directives[parts[0]] = set(parts[1:])
    return directives


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("manifest: schema_version debe ser 1")
    integrations = manifest.get("integrations")
    if not isinstance(integrations, list) or not integrations:
        errors.append("manifest: integrations debe ser lista no vacia")
        return errors

    seen: set[str] = set()
    for index, item in enumerate(integrations):
        prefix = f"integrations[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: debe ser objeto")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", item_id):
            errors.append(f"{prefix}.id invalido")
            item_id = prefix
        elif item_id in seen:
            errors.append(f"manifest: id duplicado {item_id}")
        else:
            seen.add(item_id)
        if item.get("status") not in ALLOWED_STATUS:
            errors.append(f"{item_id}: status invalido")
        if item.get("layer") not in ALLOWED_LAYER:
            errors.append(f"{item_id}: layer invalido")
        for field in ("provider", "purpose", "trigger", "failure_mode", "data_scope", "decision"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{item_id}: falta {field}")
        owners = item.get("owner_files")
        if not isinstance(owners, list) or not owners or not all(isinstance(v, str) and v for v in owners):
            errors.append(f"{item_id}: owner_files debe ser lista no vacia")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{item_id}: evidence debe ser lista no vacia")
        hosts = item.get("browser_hosts")
        if not isinstance(hosts, list):
            errors.append(f"{item_id}: browser_hosts debe ser lista")
        if item.get("layer") == "server_side" and hosts:
            errors.append(f"{item_id}: server_side no debe declarar browser_hosts")
        if item.get("status") == "optional_disabled":
            gate = item.get("activation_gate")
            if not isinstance(gate, list) or len(gate) < 2 or not all(isinstance(v, str) and v.strip() for v in gate):
                errors.append(f"{item_id}: optional_disabled requiere activation_gate explicito")
            if item.get("privacy_evidence"):
                errors.append(f"{item_id}: optional_disabled no debe fingir disclosure activo; usa activation_gate")
    return errors


def evaluate(root: Path, manifest: dict) -> list[str]:
    errors = validate_manifest(manifest)
    if errors:
        return errors

    cache: dict[str, str] = {}
    index_text = load_text(root, "index.html", cache, errors)
    csp = parse_csp(index_text or "")
    if not csp:
        errors.append("index.html: no se pudo leer CSP publico")

    privacy = load_text(root, "privacidad.html", cache, errors) or ""

    for item in manifest["integrations"]:
        item_id = item["id"]
        owners = set(item["owner_files"])
        for owner in owners:
            load_text(root, owner, cache, errors)

        for evidence in item["evidence"]:
            if not isinstance(evidence, dict):
                errors.append(f"{item_id}: evidence debe contener objetos")
                continue
            rel = evidence.get("file")
            needles = evidence.get("contains")
            if not isinstance(rel, str) or not rel:
                errors.append(f"{item_id}: evidence.file invalido")
                continue
            if rel not in owners:
                errors.append(f"{item_id}: evidence file {rel} no figura en owner_files")
            if not isinstance(needles, list) or not needles or not all(isinstance(v, str) and v for v in needles):
                errors.append(f"{item_id}: evidence.contains invalido para {rel}")
                continue
            text = load_text(root, rel, cache, errors)
            if text is None:
                continue
            for needle in needles:
                if needle not in text:
                    errors.append(f"{item_id}: falta evidencia en {rel}: {needle!r}")

        privacy_needles = item.get("privacy_evidence", [])
        if not isinstance(privacy_needles, list) or not all(isinstance(v, str) and v for v in privacy_needles):
            errors.append(f"{item_id}: privacy_evidence invalido")
        else:
            for needle in privacy_needles:
                if needle not in privacy:
                    errors.append(f"{item_id}: falta disclosure en privacidad.html: {needle!r}")

        if item["status"] in {"active", "conditional"}:
            for host_rule in item["browser_hosts"]:
                if not isinstance(host_rule, dict):
                    errors.append(f"{item_id}: browser_hosts contiene valor no objeto")
                    continue
                host = host_rule.get("host")
                directives = host_rule.get("directives")
                if not isinstance(host, str) or not host or not isinstance(directives, list) or not directives:
                    errors.append(f"{item_id}: browser host/directives invalidos")
                    continue
                for directive in directives:
                    if not isinstance(directive, str) or directive not in csp:
                        errors.append(f"{item_id}: CSP no contiene directiva {directive}")
                        continue
                    if host not in csp[directive] and f"https://{host}" not in csp[directive]:
                        errors.append(f"{item_id}: {host} no permitido por {directive} en CSP publico")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = root / manifest_path
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR manifest no legible: {exc}")
        return 1

    errors = evaluate(root, manifest)
    counts: dict[str, int] = {}
    for item in manifest.get("integrations", []):
        if isinstance(item, dict):
            status = str(item.get("status", "unknown"))
            counts[status] = counts.get(status, 0) + 1
            print(f"{item.get('id', '?')}: {status} · {item.get('layer', '?')} · {item.get('provider', '?')}")
    print("\nEstados:", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    for error in errors:
        print(f"ERROR {error}")
    print(f"Third-party integration check: {len(errors)} error(es).")
    return 1 if args.check and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
