#!/usr/bin/env python3
"""Gate de taxonomia analitica (I.1, 2026-08-23): falla si aparece un
nombre de evento GoatCounter que no este registrado en
data/analytics-events.json, la autoridad unica de nombres.

Nacio de una auditoria real: script.js emitia mas de 10 familias de
eventos con convenciones heterogeneas (accion, proveedor, libro mezclados
sin criterio), sin ningun registro ni checker que impidiera que una
refactorizacion futura anadiera una convencion mas. Este script escanea
tres fuentes de nombres literales:

1. `_gcEvent("literal", ...)` en script.js (y cualquier otro .js).
2. `data-gc="literal"` (atributo HTML embebido en plantillas JS).
3. Los "nombres crudos" (antes del prefijo `article-`) que cada
   herramienta del Cuaderno dispara via el bridge `dp:analytics`
   (`emit(...)`, `analytics(...)`, `dispatchShareEvent(...)`, o
   `dispatchEvent(new CustomEvent('dp:analytics', {detail:{event:'...'}}))`
   inline) -- comparados contra `article_bridge.names_by_module` en el
   registro, no contra la lista plana de `events` (tienen su propio
   contrato: prefijo automatico, ver el propio JSON).

Python standard library only.

Usage:
    python scripts/check-analytics-taxonomy.py
    python scripts/check-analytics-taxonomy.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "data" / "analytics-events.json"

GC_EVENT_RE = re.compile(r'_gcEvent\(\s*[`"\']([^`"\'${]*)[`"\']')
DATA_GC_RE = re.compile(r'data-gc="([^"]+)"')
EMIT_CALL_RE = re.compile(r'\b(?:emit|analytics|dispatchShareEvent)\(\s*[\'"`]([a-zA-Z0-9_-]+)[\'"`]')
INLINE_EVENT_RE = re.compile(r'event:\s*[\'"]([a-zA-Z0-9_-]+)[\'"]')

# _gcEvent(path, ...) donde path se construye dinamicamente
# ("newsletter-" + sourceLabel, `article-${name}`) no puede resolverse por
# regex sin ejecutar el JS. Se listan aqui, explicitamente, los prefijos
# dinamicos conocidos y ya cubiertos por otra via del registro (para no
# generar falsos positivos "nombre no registrado: newsletter-" ni
# "article-").
KNOWN_DYNAMIC_PREFIXES = {"newsletter-", "article-"}


def tracked_js(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.js"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel]


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_gc_events(files: list[Path], root: Path, registered: set[str]) -> list[str]:
    errors = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        for m in GC_EVENT_RE.finditer(text):
            name = m.group(1)
            if not name or any(name.startswith(p) for p in KNOWN_DYNAMIC_PREFIXES):
                continue
            if name not in registered:
                line = text.count("\n", 0, m.start()) + 1
                errors.append(f"{rel}:{line}: evento GoatCounter no registrado: '{name}' -- anadelo a data/analytics-events.json")
        for m in DATA_GC_RE.finditer(text):
            name = m.group(1)
            if name not in registered:
                line = text.count("\n", 0, m.start()) + 1
                errors.append(f"{rel}:{line}: data-gc no registrado: '{name}' -- anadelo a data/analytics-events.json")
    return errors


def check_article_bridge(files: list[Path], root: Path, names_by_module: dict[str, list[str]]) -> list[str]:
    errors = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel not in names_by_module and rel != "script.js":
            # Solo auditamos ficheros que ya sabemos que disparan
            # dp:analytics (estan como clave en el registro); un fichero
            # nuevo que empiece a hacerlo debe anadirse al registro primero.
            text = path.read_text(encoding="utf-8", errors="replace")
            if "dp:analytics" not in text:
                continue
            errors.append(f"{rel}: dispara 'dp:analytics' pero no aparece en article_bridge.names_by_module de data/analytics-events.json")
            continue
        if rel == "script.js":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        found = set()
        for m in EMIT_CALL_RE.finditer(text):
            found.add(m.group(1))
        for m in INLINE_EVENT_RE.finditer(text):
            found.add(m.group(1))
        registered = set(names_by_module.get(rel, []))
        unregistered = found - registered
        for name in sorted(unregistered):
            errors.append(f"{rel}: nombre dp:analytics no registrado: '{name}' -- anadelo a article_bridge.names_by_module en data/analytics-events.json")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    registry = load_registry(root / "data" / "analytics-events.json")
    registered_names = {e["name"] for e in registry["events"]}
    names_by_module = registry.get("article_bridge", {}).get("names_by_module", {})

    files = tracked_js(root)
    errors: list[str] = []
    errors += check_gc_events(files, root, registered_names)
    errors += check_article_bridge(files, root, names_by_module)

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nAnalytics taxonomy check: {len(files)} ficheros JS revisados, {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
