#!/usr/bin/env python3
"""Regresion: los <link rel="preload" as="style"> que scripts/add_v1_shell_preloads.py
inserta en cada pagina deben apuntar EXACTAMENTE (con el mismo ?v=) a las mismas
URLs que assets/v1-shell.css @importa -- si no coinciden byte a byte, el navegador
no reutiliza el preload y descarga cada fichero dos veces.

Bug real encontrado en produccion: los preloads llevaban ?v=1 (via TRACKED_ASSETS)
pero los 9 @import de v1-shell.css no llevaban ningun ?v=, asi que eran DOS URLs
distintas -- confirmado en vivo con Resource Timing: cada uno de los 8 ficheros con
preload se descargaba dos veces (una por el preload, ignorada; otra por el @import,
la que de verdad se usa) en cada carga de pagina, en todas las paginas del sitio.
El noveno fichero (v1-text-resilience-v8.css) ni siquiera tenia preload.

Uso:
  python tests/test-v1-shell-preload-parity.py
"""
from __future__ import annotations

import importlib.util
import io
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("add_v1_shell_preloads", ROOT / "scripts" / "add_v1_shell_preloads.py")
preloads_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = preloads_mod
_spec.loader.exec_module(preloads_mod)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


print("tests/test-v1-shell-preload-parity")

shell_css = (ROOT / "assets" / "v1-shell.css").read_text(encoding="utf-8")
IMPORT_RE = re.compile(r"@import url\('/assets/([a-zA-Z0-9_.-]+\.css)(?:\?v=([a-zA-Z0-9_.-]+))?'\)")
imports = IMPORT_RE.findall(shell_css)
imported_names = [name for name, _version in imports]

# 1. Todo lo que v1-shell.css @importa debe estar en IMPORTED (la lista que
#    add_v1_shell_preloads.py usa para generar los preloads), y viceversa --
#    ningun fichero @importado se queda sin su preload, ninguno sobra.
check(
    set(imported_names) == set(preloads_mod.IMPORTED),
    "1. el conjunto de @import en v1-shell.css coincide exactamente con IMPORTED",
    f"@import={sorted(imported_names)} IMPORTED={sorted(preloads_mod.IMPORTED)}",
)

# 2. Cada @import debe llevar un ?v= (ninguno debe quedar sin versionar --
#    eso fue exactamente el hueco que dejo v1-text-resilience-v8.css).
missing_version = [name for name, version in imports if not version]
check(not missing_version, "2. todos los @import de v1-shell.css llevan ?v=", str(missing_version))

# 3. El ?v= de cada @import debe coincidir EXACTAMENTE con TRACKED_ASSETS --
#    la version que add_v1_shell_preloads.py usara para el preload de ese
#    mismo fichero. Si difieren, preload y @import son URLs distintas.
mismatched = []
for name, version in imports:
    expected = preloads_mod.TRACKED_ASSETS.get(name)
    if expected is None:
        mismatched.append(f"{name}: no esta en TRACKED_ASSETS")
    elif version != expected:
        mismatched.append(f"{name}: @import tiene ?v={version}, TRACKED_ASSETS espera ?v={expected}")
check(not mismatched, "3. el ?v= de cada @import coincide con TRACKED_ASSETS (preload y @import son la misma URL)", str(mismatched))

# 4. Verificacion end-to-end sobre paginas reales: toma una pagina normal y
#    una generada por builder (con sintaxis de tag distinta: /> vs >), y
#    confirma que el bloque de preload real en disco contiene, para cada
#    fichero importado, un preload con el ?v= correcto -- sin asumir un
#    formato de tag concreto.
SAMPLE_PAGES = ["index.html", "herramientas/index.html", "editoriales/index.html"]
for rel in SAMPLE_PAGES:
    page = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    block_match = re.search(r"v1-shell-preload:start.*?v1-shell-preload:end", page, re.S)
    if not block_match:
        check(False, f"4. {rel}: tiene el bloque de preload v1-shell", "no encontrado")
        continue
    block = block_match.group(0)
    missing_on_page = []
    for name in preloads_mod.IMPORTED:
        # index.html links assets with no leading "/" (root-relative without the
        # slash); every other page uses "/assets/...". Accept either form here --
        # this test cares whether the version matches, not the leading slash.
        expected_href = f"assets/{name}?v={preloads_mod.TRACKED_ASSETS[name]}"
        if expected_href not in block:
            missing_on_page.append(f"/{expected_href}")
    check(not missing_on_page, f"4. {rel}: el bloque de preload incluye los {len(preloads_mod.IMPORTED)} ficheros con el ?v= correcto", str(missing_on_page))

print("tests/test-v1-shell-preload-parity: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
