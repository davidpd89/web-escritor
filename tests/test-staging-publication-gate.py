#!/usr/bin/env python3
"""Gate de publicación staging/gated vs. `noindex` (audit-nuevas-ideas:
staging-publication-gate, 2026-08-23).

Hallazgo auditado: `noindex` es una señal de INDEXACIÓN, no de PUBLICACIÓN.
`scripts/build-public-dist.py` no consultaba el estado editorial de
`data/content-registry.json` para decidir qué entra al árbol público; usaba
solo una lista corta y manual de directorios (`EXCLUDE_DIR_PREFIXES`).
`scripts/check-global-discoverability.py` clasificaba rutas "GATED" con OTRA
lista manual (`GATED_PREFIXES = ("donde-empieza-la-jaula/",)`), separada de
la primera. Ninguna de las dos consultaba `content-registry.json`.

Caso real: si `donde-empieza-la-jaula/index.html` (registrado con
`status: "noindex"`) se añadiera al repo con un `<meta name="robots"
content="noindex">`, el `noindex` habría evitado su indexación en buscadores
y su entrada en el sitemap, pero NO habría evitado que
`build-public-dist.py` lo copiara al árbol público -- quedaría accesible por
URL directa en cuanto se desplegara.

Este test demuestra con un repositorio git temporal (nunca el repo real)
que, tras el fix, una ruta con `status != "public"` en el registry:
1. no se copia al dist público al construirlo;
2. si se cuela de todos modos (fixture que simula una regresión futura),
   `check_contents()` la detecta y falla explícitamente;
3. una ruta legítimamente pública-pero-`noindex` (`status: "public"`, como
   `/privacidad.html` en el repo real) SÍ se publica -- demostrando que la
   diferencia no es el meta robots, es el estado editorial.

También confirma, contra el repositorio real (sin escribir nada), que
`donde-empieza-la-jaula/` queda excluida del dist real de verdad.

Uso:
  python tests/test-staging-publication-gate.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("bpd", ROOT / "scripts" / "build-public-dist.py")
bpd = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bpd
_spec.loader.exec_module(bpd)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def make_fixture_repo(root: Path) -> None:
    git(["init", "-q"], root)
    git(["-c", "user.email=t@t.com", "-c", "user.name=t", "config", "user.email", "t@t.com"], root)

    (root / "index.html").write_text(
        '<!DOCTYPE html><html><head><title>Home</title></head><body>Home</body></html>',
        encoding="utf-8",
    )

    # Ruta legitimamente publica pero no indexada (igual que /privacidad.html
    # en el repo real): status "public" en el registry, noindex en el HTML.
    (root / "privacidad.html").write_text(
        '<!DOCTYPE html><html><head><title>Privacidad</title>'
        '<meta name="robots" content="noindex"></head><body>Privacidad</body></html>',
        encoding="utf-8",
    )

    # Ruta staging/gated: noindex en el HTML, pero eso NO es lo que la
    # excluye -- lo que la excluye es status != "public" en el registry.
    (root / "donde-empieza-la-jaula").mkdir()
    (root / "donde-empieza-la-jaula" / "index.html").write_text(
        '<!DOCTYPE html><html><head><title>Jaula (staging)</title>'
        '<meta name="robots" content="noindex"></head><body>Staging, no publicar aun</body></html>',
        encoding="utf-8",
    )
    (root / "donde-empieza-la-jaula" / "cover.webp").write_bytes(b"fake-image-bytes")

    (root / "data").mkdir()
    registry = {
        "schema_version": 1,
        "defaults": {"status": "public", "searchIndex": True, "sitemap": True},
        "entries": [
            {"id": "home", "url": "/", "status": "public", "sourceFile": "index.html"},
            {"id": "privacy", "url": "/privacidad.html", "status": "public", "searchIndex": False, "sitemap": False, "sourceFile": "privacidad.html"},
            {"id": "jaula-staging", "url": "/donde-empieza-la-jaula/", "status": "noindex", "searchIndex": False, "sitemap": False, "sourceFile": "donde-empieza-la-jaula/index.html"},
        ],
    }
    (root / "data" / "content-registry.json").write_text(json.dumps(registry), encoding="utf-8")

    git(["add", "-A"], root)


print("tests/test-staging-publication-gate")

with tempfile.TemporaryDirectory() as tmp:
    fixture_root = Path(tmp) / "fixture-repo"
    fixture_root.mkdir()
    make_fixture_repo(fixture_root)
    out_dir = fixture_root / "_dist"

    # 1. gated_prefixes_from_registry deriva exactamente la ruta staging,
    # ninguna otra -- ni siquiera privacidad.html, que tambien es noindex.
    prefixes = bpd.gated_prefixes_from_registry(fixture_root)
    check(prefixes == ("donde-empieza-la-jaula/",), "1. gated_prefixes_from_registry deriva solo la ruta con status != public", str(prefixes))

    # 2. build() no copia la ruta staging al dist.
    included, excluded = bpd.build(out_dir, fixture_root)
    check(not (out_dir / "donde-empieza-la-jaula").exists(), "2a. build() no copia el directorio staging al dist público")
    check(not (out_dir / "donde-empieza-la-jaula" / "cover.webp").exists(), "2b. build() tampoco copia assets hermanos no registrados individualmente")

    # 3. la ruta legitimamente publica-pero-noindex SI se publica: la
    # diferencia no es el meta robots, es el estado editorial.
    check((out_dir / "privacidad.html").exists(), "3. una ruta noindex pero status=public SI se incluye en el dist (noindex no es control de acceso)")
    check((out_dir / "index.html").exists(), "3b. la home normal se incluye")

    # 4. Este fixture modela solo la frontera de publicación, no el shell/PWA
    # completo; por eso desactiva exclusivamente la comprobación de runtime.
    check(bpd.check_contents(out_dir, fixture_root, require_runtime=False) == 0, "4. check_contents() pasa sobre un dist ya filtrado correctamente")

    # 5. REGRESIÓN: si la ruta staging se cuela en el dist de todos modos --
    # simulando un bug futuro en build() o una copia manual --, el checker
    # debe detectarla y fallar aunque su HTML declare noindex.
    leaked = out_dir / "donde-empieza-la-jaula"
    leaked.mkdir()
    (leaked / "index.html").write_text((fixture_root / "donde-empieza-la-jaula" / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
    check(bpd.check_contents(out_dir, fixture_root, require_runtime=False) == 1, "5. check_contents() detecta y falla si la ruta staging se cuela en el dist (aunque tenga noindex)")

# 6. Contra el repositorio REAL (sin escribir nada en él): confirmar que
# donde-empieza-la-jaula/ ya está en la autoridad derivada del registry real.
real_prefixes = bpd.gated_prefixes_from_registry(ROOT)
check("donde-empieza-la-jaula/" in real_prefixes, "6. el registry REAL del repo ya declara donde-empieza-la-jaula/ como gated", str(real_prefixes))

# 7. Construir el dist REAL a un directorio temporal (nunca en el repo) y
# confirmar que la ruta gated queda fuera y el gate estricto pasa.
with tempfile.TemporaryDirectory() as tmp:
    real_out = Path(tmp) / "real-dist"
    bpd.build(real_out, ROOT)
    check(not (real_out / "donde-empieza-la-jaula").exists(), "7a. el dist REAL no contiene donde-empieza-la-jaula/")
    check(bpd.check_contents(real_out, ROOT) == 0, "7b. check_contents() pasa sobre el dist REAL")

print("tests/test-staging-publication-gate: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
