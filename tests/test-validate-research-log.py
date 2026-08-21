#!/usr/bin/env python3
"""Los 4 casos de QA del doc 52 (seccion 14), verificados contra el motor real.

Mismo patron que 50/53: tooling interno (research-log.template.md +
validate-research-log.py) que ya existia, mas un componente publico opcional
(assets/research-notes.css) que todavia no usa ninguna pagina real -- el
propio documento lo describe como opcional, "cuando aporte valor" (S8), asi
que no tener ningun articulo usandolo todavia no es un hueco.

Uso:
  python tests/test-validate-research-log.py
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
_spec = importlib.util.spec_from_file_location("vrl", ROOT / "scripts" / "validate-research-log.py")
vrl = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vrl
_spec.loader.exec_module(vrl)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def log(status: str, claim: str, **extra) -> str:
    meta = {
        "status": status,
        "research_id": "RL-2026-999",
        "topic": "tema de prueba",
        "started": "2026-08-01",
        "last_verified": "2026-08-21",
        "public_method_note": "false",
    }
    lines = "\n".join(f"{k}: {v}" for k, v in meta.items())
    return f"---\n{lines}\n---\n\n# Research log\n\n## Afirmaciones\n\n{claim}\n"


def write(tmp: Path, text: str) -> Path:
    p = tmp / "log.md"
    p.write_text(text, encoding="utf-8")
    return p


print("tests/test-validate-research-log")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # 1. plantilla draft -> pasa
    errs = vrl.validate(ROOT / "scripts" / "templates" / "research-log.template.md")
    check(errs == [], "1. plantilla draft -> pasa", str(errs))

    # 2. verified sin fuente -> falla
    claim = (
        "### C01 — Afirmación de prueba\n"
        "status: verified\nsource: n/a\nbasis: n/a\nchecked: 2026-08-21\n"
        "attempts: n/a\nnotes: sin fuente\npublic: false\n"
    )
    p = write(root, log("review", claim))
    errs = vrl.validate(p)
    check(any("verified sin source" in e for e in errs), "2. verified sin fuente -> falla", str(errs))

    # 3. unconfirmed sin registro de intentos -> falla
    claim = (
        "### C01 — Afirmación de prueba\n"
        "status: unconfirmed\nsource: n/a\nbasis: n/a\nchecked: 2026-08-21\n"
        "attempts: n/a\nnotes: sin intentos registrados\npublic: false\n"
    )
    p = write(root, log("review", claim))
    errs = vrl.validate(p)
    check(any("unconfirmed sin attempts" in e for e in errs), "3. unconfirmed sin attempts -> falla", str(errs))

    # 4. log publicable completo -> pasa
    claim = (
        "### C01 — Afirmación verificada de prueba\n"
        "status: verified\nsource: nota de trabajo del 12/03/2025\nbasis: n/a\n"
        "checked: 2026-08-21\nattempts: n/a\nnotes: confirmado\npublic: true\n"
    )
    p = write(root, log("published", claim))
    errs = vrl.validate(p)
    check(errs == [], "4. log publicable completo -> pasa", str(errs))

    # Extra: inference exige source O basis (al menos una de las dos).
    claim = (
        "### C01 — Afirmación por inferencia\n"
        "status: inference\nsource: n/a\nbasis: n/a\nchecked: 2026-08-21\n"
        "attempts: n/a\nnotes: sin ninguna base\npublic: false\n"
    )
    p = write(root, log("review", claim))
    errs = vrl.validate(p)
    check(any("inference sin fuentes base" in e for e in errs), "extra: inference sin source ni basis -> falla", str(errs))

    claim_ok = (
        "### C01 — Afirmación por inferencia\n"
        "status: inference\nsource: n/a\nbasis: dos fuentes secundarias contrastadas\n"
        "checked: 2026-08-21\nattempts: n/a\nnotes: inferencia razonable\npublic: false\n"
    )
    p = write(root, log("review", claim_ok))
    errs = vrl.validate(p)
    check(
        not any("inference sin fuentes base" in e for e in errs),
        "extra: inference con solo basis (sin source) es suficiente",
        str(errs),
    )

    # Extra: regla crítica del doc 52 §5 — "discarded" es un estado válido por
    # sí mismo, sin exigir source/attempts (una hipótesis descartada no
    # necesita las mismas pruebas que una verificada).
    claim = (
        "### C01 — Hipótesis descartada\n"
        "status: discarded\nsource: n/a\nbasis: n/a\nchecked: 2026-08-21\n"
        "attempts: n/a\nnotes: contradice fuente primaria\npublic: false\n"
    )
    p = write(root, log("review", claim))
    errs = vrl.validate(p)
    check(errs == [], "extra: discarded no exige source ni attempts", str(errs))

    # Extra: published sin ninguna afirmación registrada -> falla.
    p = write(root, log("published", ""))
    errs = vrl.validate(p)
    check(any("sin afirmaciones registradas" in e for e in errs), "extra: published sin afirmaciones -> falla", str(errs))

# El componente público es semántico y sin JS (doc 52 §14: "no introduce
# JavaScript", "usa <details>/<summary>").
css = (ROOT / "assets" / "research-notes.css").read_text(encoding="utf-8")
check("<script" not in css.lower() and "function(" not in css, "el CSS del componente no contiene JavaScript")
check("details" in css and "summary" in css, "el CSS del componente usa selectores details/summary")
check("@media print" in css, "el CSS del componente tiene reglas de impresión")

print("tests/test-validate-research-log: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
