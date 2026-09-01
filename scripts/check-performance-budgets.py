#!/usr/bin/env python3
"""Budget determinista de bytes/requests del artifact (E.5).

Mide grupos declarados en data/performance-budgets.json. Sigue:
- @import locales de CSS de forma transitiva;
- import/export estaticos locales de JS/MJS de forma transitiva.

No sigue import() dinamico: una carga diferida relevante debe declararse como
entrypoint de su propio budget para no convertir optional/lazy code en critical
shell por accidente.

El modo `report` siempre informa y solo falla por contrato roto (manifest o
ficheros/imports locales inexistentes). El modo `enforce` compara contra limits.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path("data/performance-budgets.json")

CSS_IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*)?[\"']([^\"']+)[\"']\s*\)?",
    re.IGNORECASE,
)
JS_IMPORT_RE = re.compile(
    r"^\s*import\s+(?!\()(?:(?:[^;]*?)\sfrom\s+)?[\"']([^\"']+)[\"']\s*;",
    re.MULTILINE | re.DOTALL,
)
JS_EXPORT_RE = re.compile(
    r"^\s*export\s+[^;]*?\sfrom\s+[\"']([^\"']+)[\"']\s*;",
    re.MULTILINE | re.DOTALL,
)

METRIC_KEYS = ("total_bytes", "css_bytes", "js_bytes", "font_bytes", "other_bytes", "request_count")


def _strip_suffixes(specifier: str) -> str:
    return specifier.split("#", 1)[0].split("?", 1)[0].strip()


def resolve_local(root: Path, importer: Path, specifier: str) -> Path | None:
    specifier = _strip_suffixes(specifier)
    if not specifier or specifier.startswith(("http://", "https://", "//", "data:", "blob:")):
        return None
    if specifier.startswith("/"):
        candidate = root / specifier.lstrip("/")
    elif specifier.startswith("."):
        candidate = importer.parent / specifier
    else:
        # Bare module/package specifiers are external to this static artifact graph.
        return None
    return candidate.resolve()


def local_dependencies(root: Path, path: Path, text: str) -> Iterable[Path]:
    suffix = path.suffix.lower()
    if suffix == ".css":
        matches = CSS_IMPORT_RE.findall(text)
    elif suffix in {".js", ".mjs"}:
        matches = [*JS_IMPORT_RE.findall(text), *JS_EXPORT_RE.findall(text)]
    else:
        matches = []
    for specifier in matches:
        resolved = resolve_local(root, path, specifier)
        if resolved is not None:
            yield resolved


def collect_graph(root: Path, entrypoints: list[str]) -> tuple[list[Path], list[str]]:
    files: set[Path] = set()
    errors: list[str] = []
    stack: list[Path] = []

    for rel in entrypoints:
        if not isinstance(rel, str) or not rel.strip():
            errors.append("entrypoint invalido: debe ser string no vacio")
            continue
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            errors.append(f"{rel}: entrypoint fuera del repositorio")
            continue
        stack.append(candidate)

    while stack:
        path = stack.pop()
        if path in files:
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            errors.append(f"{path}: dependencia fuera del repositorio")
            continue
        if not path.exists() or not path.is_file():
            errors.append(f"{rel}: fichero/dependencia local no existe")
            continue
        files.add(path)
        if path.suffix.lower() not in {".css", ".js", ".mjs"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for dep in local_dependencies(root, path, text):
            try:
                dep.relative_to(root)
            except ValueError:
                errors.append(f"{rel}: import local escapa del repositorio ({dep})")
                continue
            if dep not in files:
                stack.append(dep)

    return sorted(files), errors


def metric_bucket(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".css":
        return "css_bytes"
    if suffix in {".js", ".mjs"}:
        return "js_bytes"
    if suffix in {".woff", ".woff2", ".ttf", ".otf"}:
        return "font_bytes"
    return "other_bytes"


def metrics_for(files: list[Path]) -> dict[str, int]:
    metrics = {key: 0 for key in METRIC_KEYS}
    for path in files:
        size = path.stat().st_size
        metrics[metric_bucket(path)] += size
        metrics["total_bytes"] += size
    metrics["request_count"] = len(files)
    return metrics


def validate_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("manifest: schema_version debe ser 1")
    if manifest.get("enforcement") not in {"report", "enforce"}:
        errors.append("manifest: enforcement debe ser report o enforce")
    budgets = manifest.get("budgets")
    if not isinstance(budgets, list) or not budgets:
        errors.append("manifest: budgets debe ser una lista no vacia")
        return errors
    seen: set[str] = set()
    for index, budget in enumerate(budgets):
        if not isinstance(budget, dict):
            errors.append(f"manifest: budgets[{index}] debe ser objeto")
            continue
        budget_id = budget.get("id")
        if not isinstance(budget_id, str) or not budget_id:
            errors.append(f"manifest: budgets[{index}].id invalido")
        elif budget_id in seen:
            errors.append(f"manifest: id duplicado {budget_id}")
        else:
            seen.add(budget_id)
        entries = budget.get("entrypoints")
        if not isinstance(entries, list) or not entries:
            errors.append(f"manifest: {budget_id or index}.entrypoints debe ser lista no vacia")
        for field in ("baseline", "limits"):
            values = budget.get(field)
            if values is None:
                continue
            if not isinstance(values, dict):
                errors.append(f"manifest: {budget_id or index}.{field} debe ser objeto")
                continue
            for key, value in values.items():
                if key not in METRIC_KEYS:
                    errors.append(f"manifest: {budget_id or index}.{field}.{key} no es metrica soportada")
                if not isinstance(value, int) or value < 0:
                    errors.append(f"manifest: {budget_id or index}.{field}.{key} debe ser entero >= 0")
    return errors


def evaluate(root: Path, manifest: dict) -> tuple[dict, list[str]]:
    report = {
        "schema_version": 1,
        "enforcement": manifest.get("enforcement"),
        "budgets": [],
    }
    errors = validate_manifest(manifest)
    if errors:
        return report, errors

    enforce = manifest["enforcement"] == "enforce"
    for budget in manifest["budgets"]:
        budget_id = budget["id"]
        files, graph_errors = collect_graph(root, budget["entrypoints"])
        errors.extend(f"{budget_id}: {error}" for error in graph_errors)
        metrics = metrics_for(files)
        baseline = budget.get("baseline") or {}
        limits = budget.get("limits") or {}
        violations: list[str] = []

        if enforce:
            if not limits:
                violations.append("enforcement activo sin limits")
            for key, limit in limits.items():
                actual = metrics[key]
                if actual > limit:
                    violations.append(f"{key}={actual} > limit={limit}")

        file_rows = [
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "kind": metric_bucket(path).removesuffix("_bytes"),
            }
            for path in files
        ]
        report["budgets"].append(
            {
                "id": budget_id,
                "label": budget.get("label", budget_id),
                "entrypoints": budget["entrypoints"],
                "metrics": metrics,
                "baseline": baseline,
                "limits": limits,
                "violations": violations,
                "files": file_rows,
            }
        )
        errors.extend(f"{budget_id}: {violation}" for violation in violations)
    return report, errors


def print_report(report: dict) -> None:
    print(f"Performance budgets — mode={report.get('enforcement')}")
    for budget in report.get("budgets", []):
        metrics = budget["metrics"]
        print(
            f"- {budget['id']}: total={metrics['total_bytes']} B; "
            f"css={metrics['css_bytes']} B; js={metrics['js_bytes']} B; "
            f"fonts={metrics['font_bytes']} B; other={metrics['other_bytes']} B; "
            f"requests={metrics['request_count']}"
        )
        if budget.get("baseline"):
            print(f"  baseline={json.dumps(budget['baseline'], sort_keys=True)}")
        if budget.get("limits"):
            print(f"  limits={json.dumps(budget['limits'], sort_keys=True)}")
        for row in sorted(budget.get("files", []), key=lambda item: item["bytes"], reverse=True)[:8]:
            print(f"    {row['bytes']:>8} B  {row['path']}")
        for violation in budget.get("violations", []):
            print(f"  VIOLATION {violation}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--manifest", default=str(MANIFEST))
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--check", action="store_true", help="falla ante contrato roto y, en mode=enforce, ante limites")
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

    report, errors = evaluate(root, manifest)
    print_report(report)

    if args.json_path:
        out = Path(args.json_path)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nReport JSON: {out.relative_to(root) if out.is_relative_to(root) else out}")

    for error in errors:
        print(f"ERROR {error}")
    print(f"\nPerformance budget check: {len(report.get('budgets', []))} budget(s), {len(errors)} error(es).")
    return 1 if args.check and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
