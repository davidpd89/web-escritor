#!/usr/bin/env python3
"""Contrato de la vía rápida de contenido: misma política que el publicador, fail-closed y red semanal."""
import importlib.util
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lane", ROOT / "scripts" / "ci_content_lane.py")
lane = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lane)

EXCLUDED = (
    "analytics-taxonomy-qa", "cross-engine-smoke", "csp-public-shell-qa", "navigation-roundtrip-audit",
    "public-time-semantics-qa", "runtime-scoping-qa", "sitewide-console-errors-qa", "small-ui-audit",
)
fallos = 0


def falla(msg):
    global fallos
    fallos += 1
    print("FALLA", msg)


def glob_regex(pattern):
    """Glob de GitHub Actions: ** cruza carpetas, * y ? no (igual que scripts/local-ci.py)."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


GLOBS = [glob_regex(g) for g in lane.CONTENT_GLOBS]

# 1. Clasificación.
CASOS = [
    (["recomendaciones/libros/x/index.html", "data/reading-catalogue.json", "pagefind/pagefind-entry.json"], True),
    (["assets/reading-covers/isbn-9788498382372.webp"], True),
    (["assets/reading-covers/coraline.webp"], False),
    ([], False),
    (["assets/reading-catalogue.css"], False),
    (["recomendaciones/libros/x/index.html", "scripts/build-reading-pages.py"], False),
    ([".github/workflows/pa11y-baseline.yml"], False),
    (["index.html"], False),
]
for files, esperado in CASOS:
    if lane.is_content(files) != esperado:
        falla(f"is_content({files}) != {esperado}")

# 2. Muestra: índices primero, luego más pesadas, sin borradas, con tope.
sizes = {"recomendaciones/libros/a/index.html": 10, "recomendaciones/libros/b/index.html": 30,
         "recomendaciones/autores/c/index.html": 20}


def size(f):
    if f not in sizes:
        raise FileNotFoundError(f)
    return sizes[f]


got = lane.sample_routes([*sizes, "recomendaciones/libros/borrada/index.html", "recomendaciones/index.html",
                          "data/reading-catalogue.json"], size=size)
esperado = [*lane.HUBS, "/recomendaciones/libros/b/", "/recomendaciones/autores/c/", "/recomendaciones/libros/a/"]
if got != esperado:
    falla(f"sample_routes {got} != {esperado}")
muchas = [f"recomendaciones/libros/l{i}/index.html" for i in range(40)]
if len(lane.sample_routes(muchas, size=lambda f: 1)) != lane.MAX_SAMPLE:
    falla("la muestra debe tener tope MAX_SAMPLE")

# 3. Fail-closed.
if lane.decide("push", "", "", "main")[0] != "full":
    falla("push debe ser full")
if lane.decide("workflow_dispatch", "", "", "main")[0] != "full":
    falla("dispatch en main debe ser full")
if lane.decide("pull_request", "0" * 40, "HEAD", "x")[0] != "full":
    falla("diff imposible debe ser full")
# Sin git real: el runner de python-tests no tiene origin/main (los workflows de la vía sí, con fetch-depth 0).
real_git, lane.git = lane.git, lambda *args: "base\n"
try:
    if lane.diff_range("workflow_dispatch", "", "", "automation/reading-catalogue-textos-2026-11-03-1") != ("base", "HEAD"):
        falla("dispatch en rama del bot debe calcular diff")
finally:
    lane.git = real_git

# 4. Los globs equivalen a la política, sobre todos los ficheros del repo.
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
for f in tracked:
    permitido, cubierto = lane.allowed_path(f), any(rx.match(f) for rx in GLOBS)
    if permitido and not cubierto:
        falla(f"{f} es contenido para el publicador pero ningún glob lo excluye")
    if cubierto and not permitido:
        falla(f"{f} lo excluye un glob pero el publicador no lo admite")

# 5. Cada workflow excluido usa exactamente CONTENT_GLOBS y la auditoría nocturna lo relanza.
weekly = (ROOT / ".github/workflows/weekly-full-audit.yml").read_text(encoding="utf-8")
for name in EXCLUDED:
    text = (ROOT / f".github/workflows/{name}.yml").read_text(encoding="utf-8")
    m = re.search(r"^  pull_request:[ \t]*\n((?:    .*\n|\s*\n)*)", text, re.M)
    if not m:
        falla(f"{name}: sin pull_request")
        continue
    block = m.group(1)
    if "paths-ignore:" in block:
        lista = re.findall(r"^      - '([^'!][^']*)'", block, re.M)
    else:
        lista = re.findall(r"^      - '!([^']*)'", block, re.M)
    if lista != list(lane.CONTENT_GLOBS):
        falla(f"{name}: la exclusión no coincide con CONTENT_GLOBS")
    if f"{name}.yml" not in weekly:
        falla(f"{name}: no está en weekly-full-audit.yml")
if not re.search(r"cron: '\d+ \d+ \* \* \*'", weekly):
    falla("weekly-full-audit.yml: la auditoría completa debe ser diaria (de madrugada)")
for name in ("lighthouse-ci", "pa11y-baseline", "sitewide-reflow-qa"):
    text = (ROOT / f".github/workflows/{name}.yml").read_text(encoding="utf-8")
    # Sin cron diario propio, lo relanza completo la auditoría nocturna.
    if f"{name}.yml" not in weekly and not re.search(r"cron: '\d+ \d+ \* \* \*'", text):
        falla(f"{name}: ni la auditoría nocturna ni un cron propio lo lanzan completo cada día")
    if "scripts/ci_content_lane.py" not in text:
        falla(f"{name}: no consulta la vía rápida")

if fallos:
    raise SystemExit(1)
print(f"ok: {len(CASOS)} casos, {len(tracked)} ficheros contra la política, {len(EXCLUDED)} workflows")
