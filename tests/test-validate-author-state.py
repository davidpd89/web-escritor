#!/usr/bin/env python3
"""Los 4 casos de QA del doc 51 (seccion 11), verificados contra el motor real.

Doc 51 sigue el mismo patron que 50/53: artefactos internos
(estado-david-porto-anual.template.md + validate-author-state.py) que no
generan ninguna pagina publica por si solos -- solo impiden que un borrador
del cierre anual llegue a `status: published` sin fuente para lo que afirma.

A diferencia de 50/53, aqui NO existia ningun artefacto: se han construido
ambos (plantilla + validador) para esta sesion, siguiendo al pie de la letra
las reglas de las secciones 5 y 10-11 del documento.

Uso:
  python tests/test-validate-author-state.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("vas", ROOT / "scripts" / "validate-author-state.py")
vas = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vas
_spec.loader.exec_module(vas)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


HEAD = (
    "---\nyear: \"2026\"\nstatus: published\nverified_at: \"2026-08-21\"\n"
    "title: \"Estado de David Porto 2026\"\npublic_slug: estado-david-porto-2026\n"
    "published_url: \"https://davidportodiaz.com/cuaderno/estado-david-porto-2026/\"\n---\n\n"
    "# Estado de David Porto 2026\n\n"
)


def write(tmp: Path, body: str) -> Path:
    p = tmp / "cierre.md"
    p.write_text(HEAD + body, encoding="utf-8")
    return p


print("tests/test-validate-author-state")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # 1. plantilla en draft -> pasa
    errs = vas.validate(ROOT / "scripts" / "templates" / "estado-david-porto-anual.template.md")
    check(errs == [], "1. plantilla en draft -> pasa", str(errs))

    # 2. fixture published con [[pendiente]] -> falla
    p = write(
        root,
        "## Resumen del año\n[[pendiente: falta el resumen]]\n\n"
        "## Hitos verificados del año\n- [verified] Hito — fuente: /libros/x/\n\n"
        "## Previsiones\n- [target] Algo futuro\n",
    )
    errs = vas.validate(p)
    check(any("pendiente" in e.lower() for e in errs), "2. published con [[pendiente]] -> falla", str(errs))

    # 3. fixture con previsión futura 'confirmed' sin fuente -> falla
    p = write(
        root,
        "## Resumen del año\nResumen real.\n\n"
        "## Hitos verificados del año\n- [verified] Hito — fuente: /libros/x/\n\n"
        "## Previsiones\n- [confirmed] Publicación confirmada en fecha X\n",
    )
    errs = vas.validate(p)
    check(
        any("confirmed" in e.lower() and "fuente" in e.lower() for e in errs),
        "3. previsión 'confirmed' sin fuente -> falla",
        str(errs),
    )

    # 4. fixture completo -> pasa
    p = write(
        root,
        "## Resumen del año\nResumen real y completo.\n\n"
        "## Hitos verificados del año\n"
        "- [verified] Publicación de Samuel entre mundos — fuente: /libros/samuel-entre-mundos/\n\n"
        "## Previsiones\n"
        "- [confirmed] Las manecillas del recuerdo se publica el 3 de septiembre de 2026 — fuente: contrato editorial\n"
        "- [target] Tercer libro en 2027\n"
        "- [aspiration] Traducción a otros idiomas\n",
    )
    errs = vas.validate(p)
    check(errs == [], "4. fixture completo -> pasa", str(errs))

    # Extra: un hito marcado unverified no puede publicarse (doc 51 exige
    # fuente para "hitos declarados como verificados" — uno que se declara
    # explícitamente SIN verificar tampoco debería colarse).
    p = write(
        root,
        "## Resumen del año\nResumen real.\n\n"
        "## Hitos verificados del año\n- [unverified] Rumor sin confirmar\n\n"
        "## Previsiones\n- [target] Algo\n",
    )
    errs = vas.validate(p)
    check(any("sin verificar" in e.lower() for e in errs), "extra: hito unverified bloquea publicación", str(errs))

    # Extra: previsión sin ninguna etiqueta de certeza reconocida -> falla
    # (doc 51 "obliga a clasificar previsiones").
    p = write(
        root,
        "## Resumen del año\nResumen real.\n\n"
        "## Hitos verificados del año\n- [verified] Hito — fuente: /x/\n\n"
        "## Previsiones\n- [probable] Algo sin clasificar correctamente\n",
    )
    errs = vas.validate(p)
    check(any("sin clasificar" in e.lower() for e in errs), "extra: previsión sin clasificar correctamente falla", str(errs))

    # Extra: target/aspiration NO exigen fuente (a diferencia de confirmed).
    p = write(
        root,
        "## Resumen del año\nResumen real.\n\n"
        "## Hitos verificados del año\n- [verified] Hito — fuente: /x/\n\n"
        "## Previsiones\n- [target] Algo sin fuente, y está bien así\n- [aspiration] Otro deseo sin fuente\n",
    )
    errs = vas.validate(p)
    check(errs == [], "extra: target/aspiration no exigen fuente", str(errs))

print("tests/test-validate-author-state: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
