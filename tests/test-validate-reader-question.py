#!/usr/bin/env python3
"""Los 7 casos de QA que el propio documento 53 (seccion 11) dice que el
validador debe cubrir, verificados contra el motor real -- no asumidos.

Igual que doc 50, doc 53 es deliberadamente tooling interno: no hay pagina
publica que auditar todavia (la matriz de destino en si existe para decidir
SI algo llega a convertirse en pagina, y la mayoria de destinos ni siquiera
crean una URL nueva).

Uso:
  python tests/test-validate-reader-question.py
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
_spec = importlib.util.spec_from_file_location("vrq", ROOT / "scripts" / "validate-reader-question.py")
vrq = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vrq
_spec.loader.exec_module(vrq)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def frontmatter(**overrides) -> str:
    base = {
        "question_id": "Q-2026-001",
        "status": "captured",
        "captured_at": "2026-08-10",
        "source_kind": "email",
        "source_ref": "correo del 10/08/2026",
        "attribution": "anonymous",
        "permission_ref": "n/a",
        "book_or_topic": "samuel-entre-mundos",
        "already_answered_url": "n/a",
        "destination": "hold",
        "first_hand_value": "n/a",
        "answer_evidence": "n/a",
        "spoiler_level": "none",
        "published_url": "n/a",
    }
    base.update(overrides)
    lines = "\n".join(f"{k}: {v}" for k, v in base.items())
    return f"---\n{lines}\n---\n\n[[pendiente: cuerpo]]\n"


def write(tmp: Path, text: str) -> Path:
    p = tmp / "pregunta.md"
    p.write_text(text, encoding="utf-8")
    return p


print("tests/test-validate-reader-question")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # 1. plantilla captured incompleta -> PASS
    errs = vrq.validate(ROOT / "scripts" / "templates" / "reader-question.template.md")
    check(errs == [], "1. plantilla captured incompleta -> PASS", str(errs))

    # 2. ready sin source_ref -> FAIL
    p = write(root, frontmatter(status="ready", source_ref="", destination="hold"))
    errs = vrq.validate(p)
    check(any("source_ref" in e for e in errs), "2. ready sin source_ref -> FAIL", str(errs))

    # 3. ready con atribución privada y sin permiso -> FAIL
    # ("atribución privada" = pública sin el permiso que la respalda:
    # permission_granted/public_handle exigen permission_ref.)
    p = write(
        root,
        frontmatter(
            status="ready", destination="hold", attribution="permission_granted", permission_ref=""
        ),
    )
    errs = vrq.validate(p)
    check(
        any("permission_ref" in e for e in errs),
        "3. ready con atribución que exige permiso y sin permission_ref -> FAIL",
        str(errs),
    )

    # 4. ready a cuaderno_article sin first_hand_value -> FAIL
    p = write(root, frontmatter(status="ready", destination="cuaderno_article", first_hand_value=""))
    errs = vrq.validate(p)
    check(
        any("first_hand_value" in e for e in errs),
        "4. ready con destination=cuaderno_article sin first_hand_value -> FAIL",
        str(errs),
    )

    # 5. triaged como existing_page sin URL existente -> FAIL
    # (bug real encontrado y corregido: el validador solo miraba esta regla
    # en ready/published, no en triaged, así que este caso exacto del propio
    # documento pasaba en verde antes del fix.)
    p = write(root, frontmatter(status="triaged", destination="existing_page", already_answered_url=""))
    errs = vrq.validate(p)
    check(
        any("already_answered_url" in e for e in errs),
        "5. triaged con destination=existing_page sin already_answered_url -> FAIL",
        str(errs),
    )

    # 6. published sin published_url -> FAIL
    p = write(
        root,
        frontmatter(
            status="published",
            destination="short_answer_block",
            already_answered_url="n/a",
            published_url="",
        ).replace("[[pendiente: cuerpo]]", "Cuerpo real sin pendientes."),
    )
    errs = vrq.validate(p)
    check(any("published_url" in e for e in errs), "6. published sin published_url -> FAIL", str(errs))

    # 7. fixture completo -> PASS
    p = write(
        root,
        frontmatter(
            status="published",
            destination="short_answer_block",
            published_url="https://davidportodiaz.com/libros/samuel-entre-mundos/",
        ).replace("[[pendiente: cuerpo]]", "Cuerpo real, completo, sin marcadores de pendiente."),
    )
    errs = vrq.validate(p)
    check(errs == [], "7. fixture completo (published, sin pendientes) -> PASS", str(errs))

    # Extra: el mismo caso 5, pero en estado ready (no solo triaged), sigue
    # exigiendo already_answered_url -- el fix no debe haber estrechado el
    # gate en ready/published, solo haberlo adelantado a triaged.
    p = write(root, frontmatter(status="ready", destination="existing_page", already_answered_url=""))
    errs = vrq.validate(p)
    check(
        any("already_answered_url" in e for e in errs),
        "extra: ready con existing_page sin URL sigue fallando tras el fix",
        str(errs),
    )

    # Extra: hold con destination=existing_page y sin URL SÍ puede quedarse
    # así -- "hold" significa expresamente que todavía no se puede resolver,
    # así que no se le exige la misma URL que a un triaged/ready/published.
    p = write(root, frontmatter(status="hold", destination="existing_page", already_answered_url=""))
    errs = vrq.validate(p)
    check(
        not any("already_answered_url" in e for e in errs),
        "extra: hold con existing_page sin URL no dispara esa regla (aún sin resolver, por diseño)",
        str(errs),
    )

print("tests/test-validate-reader-question: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
