#!/usr/bin/env python3
"""La pagina de metodologia no puede cambiar solo porque hoy sea otro dia.

El contrato del directorio de editoriales dice que una comprobacion no debe
aparentar una actualizacion editorial. El builder usaba `today.isoformat()`
como `dateModified`, asi que bastaba volver a ejecutarlo para que la pagina
declarase haber cambiado hoy sin que hubiera cambiado ni una palabra. Un
consumidor de schema.org — Google incluido — lee eso como contenido fresco.

Estos tests fijan las tres cosas que se corrigieron:
  1. dos builds con `--today` distinto producen el MISMO HTML;
  2. el recuento de fichas se pluraliza ("1 ficha" / "3 fichas"), no "3 ficha(s)";
  3. el texto publicado lleva tildes.

Uso:
  python tests/test-editoriales-metodologia.py
"""
from __future__ import annotations

import copy
import importlib.util
import io
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "editoriales.json"

# El builder lleva guiones en el nombre, asi que no se puede importar con
# `import`; se carga por ruta.
_spec = importlib.util.spec_from_file_location(
    "build_editoriales", ROOT / "scripts" / "build-editoriales.py"
)
be = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(be)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def build_to(tmp: Path, today: str) -> str:
    be.build(DATA, tmp, date.fromisoformat(today), False)
    return (tmp / be.METHODOLOGY_SLUG / "index.html").read_text(encoding="utf-8")


print("tests/test-editoriales-metodologia")

# 1. Determinismo frente a la fecha de ejecucion.
with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
    html_a = build_to(Path(a), "2026-08-20")
    html_b = build_to(Path(b), "2029-01-02")

date_a = re.search(r'"dateModified":"([^"]+)"', html_a)
date_b = re.search(r'"dateModified":"([^"]+)"', html_b)
check(date_a is not None and date_b is not None, "la pagina declara dateModified")
if date_a and date_b:
    check(
        date_a.group(1) == date_b.group(1),
        "dateModified no depende de la fecha de ejecucion",
        f"{date_a.group(1)} != {date_b.group(1)}",
    )
    check(
        date_a.group(1) != date.today().isoformat() or be.METHODOLOGY_REVISED == date.today().isoformat(),
        "dateModified no es simplemente hoy",
        date_a.group(1),
    )

# El HTML entero debe coincidir: si algo mas dependiera de `today`, saldria aqui
# aunque el dateModified estuviera bien.
check(html_a == html_b, "el HTML completo de metodologia es identico en ambos builds")

# El valor tiene que salir del contenido: revision del texto o ultima
# actualizacion real de una ficha, lo que sea mas reciente.
records = json.loads(DATA.read_text(encoding="utf-8"))["publishers"]
published = [r for r in records if r.get("publish") is True]
expected = max([be.METHODOLOGY_REVISED] + [r["page_updated_at"] for r in published])
check(
    be.methodology_date_modified(published) == expected,
    "dateModified = max(revision del texto, page_updated_at de las fichas)",
    f"{be.methodology_date_modified(published)} != {expected}",
)

# Si una ficha se actualiza de verdad, la fecha SI debe moverse: el objetivo era
# quitar el falso positivo, no congelar la pagina.
moved = copy.deepcopy(published)
moved[0]["page_updated_at"] = "2030-05-05"
check(
    be.methodology_date_modified(moved) == "2030-05-05",
    "un cambio real en una ficha si mueve dateModified",
)

# 2. Pluralizacion.
check(be.plural_fichas(1) == "1 ficha", "plural_fichas(1) == '1 ficha'", be.plural_fichas(1))
check(be.plural_fichas(2) == "2 fichas", "plural_fichas(2) == '2 fichas'", be.plural_fichas(2))
check(be.plural_fichas(3) == "3 fichas", "plural_fichas(3) == '3 fichas'", be.plural_fichas(3))
check("ficha(s)" not in html_a, "el HTML publicado no contiene 'ficha(s)'")

# 3. Tildes en el texto visible (no en el JSON-LD ni en atributos).
visible = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>", "", html_a, flags=re.S))
sin_tilde = sorted(set(re.findall(
    r"\b(Metodologia|metodologia|Como|informacion|recepcion|pagina|paginas|Diaz|"
    r"dias|envios|envio|segun|via|traves|asi|aqui|historico|revision|"
    r"actualizacion|comprobacion|representacion|garantia|publico)\b",
    visible,
)))
check(not sin_tilde, "el texto visible lleva tildes", ", ".join(sin_tilde))

# 4. La pagina PUBLICADA sigue reflejando el dataset.
# Todo lo anterior comprueba el builder contra un directorio temporal. La
# pagina servida se migro a V1 por separado (0ed1303) y ya no coincide con la
# plantilla del builder, asi que un dato obsoleto ahi no lo detecta nadie: el
# recuento de fichas es texto fijo dentro del HTML publicado.
publicada = (ROOT / be.METHODOLOGY_SLUG / "index.html").read_text(encoding="utf-8")
esperado = be.plural_fichas(len(published))
check(
    esperado in publicada,
    f"la pagina publicada declara el recuento real de fichas ({esperado})",
    "el dataset y el texto publicado no coinciden",
)
check(
    "ficha(s)" not in publicada,
    "la pagina publicada no contiene 'ficha(s)'",
)

print("tests/test-editoriales-metodologia: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
