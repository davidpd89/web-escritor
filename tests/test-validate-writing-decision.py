#!/usr/bin/env python3
"""QA del preflight de decisiones de escritura (doc 50 + IDEAS 39/40 absorbidas).

Doc 50 es deliberadamente un artefacto INTERNO, no una pagina publica: la
seccion 7 dice explicitamente "No crear todavia" para el hub, y la seccion 12
llama a la plantilla y al validador "artefactos internos, no publicos". Por
eso no hay pagina que verificar en el sitio -- lo que hay que verificar es
que el preflight aplica de verdad las reglas del documento antes de que
cualquier pieza real llegue a `status: published`.

Uso:
  python tests/test-validate-writing-decision.py
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
_spec = importlib.util.spec_from_file_location("vwd", ROOT / "scripts" / "validate-writing-decision.py")
vwd = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = vwd
_spec.loader.exec_module(vwd)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def frontmatter(**overrides) -> str:
    base = {
        "status": "draft",
        "content_variant": "decision",
        "book_slug": "samuel-entre-mundos",
        "public_slug": "como-resolvi-el-coste-de-la-magia",
        "title": "Cómo resolví el coste de la magia en Samuel entre mundos",
        "spoiler_level": "chapter",
        "source_evidence": "Nota de trabajo del 12/03/2026 y comentario editorial",
        "evidence_private": "true",
        "decision_date": "2026-03-12",
        "last_verified": "2026-08-21",
        "contains_third_party_editorial_text": "false",
        "editorial_permission": "not_applicable",
    }
    base.update(overrides)
    lines = "\n".join(f"{k}: {v}" for k, v in base.items())
    return f"---\n{lines}\n---\n"


FULL_SECTIONS = "\n".join(
    f"## {heading}\nContenido real y sustancial para esta sección, no un marcador vacío.\n"
    for heading in vwd.REQUIRED_SECTIONS
)


def write(tmp: Path, text: str) -> Path:
    p = tmp / "borrador.md"
    p.write_text(text, encoding="utf-8")
    return p


print("tests/test-validate-writing-decision")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # El propio template interno debe pasar como borrador (status: draft no
    # exige secciones completas ni ausencia de [[pendiente]]).
    errs = vwd.validate(ROOT / "scripts" / "templates" / "decision-escritura.template.md")
    check(errs == [], "la plantilla interna pasa como borrador", str(errs))

    # 1. Publicado con [[pendiente]] -> falla.
    p = write(root, frontmatter(status="published") + FULL_SECTIONS + "\n[[pendiente: algo]]\n")
    errs = vwd.validate(p)
    check(any("pendiente" in e.lower() for e in errs), "publicado con [[pendiente]] falla", str(errs))

    # 2. Título genérico "Decisión 1" -> falla, en cualquier estado.
    p = write(root, frontmatter(title="Decisión 1") + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(any("genérico" in e.lower() for e in errs), "título genérico 'Decisión 1' falla", str(errs))
    p = write(root, frontmatter(title="Decisión 12") + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(any("genérico" in e.lower() for e in errs), "título genérico 'Decisión 12' (con número) también falla", str(errs))

    # 3. Falta evidencia (source_evidence vacío) en estado published -> falla.
    p = write(root, frontmatter(status="published", source_evidence="") + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(any("source_evidence" in e for e in errs), "publicado sin source_evidence falla", str(errs))

    # 4. Falta un metadato obligatorio cualquiera -> falla, sea cual sea el status.
    text = frontmatter()
    text = text.replace("spoiler_level: chapter\n", "")  # elimina el campo entero
    p = write(root, text + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(any("spoiler_level" in e for e in errs), "falta un metadato obligatorio (spoiler_level) falla", str(errs))

    # 5. spoiler_level inválido -> falla.
    p = write(root, frontmatter(spoiler_level="medio") + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(any("spoiler_level" in e for e in errs), "spoiler_level fuera de {none,light,chapter,full} falla", str(errs))

    # 6. IDEA 39 absorbida: contenido editorial de terceros sin permiso granted -> falla.
    p = write(
        root,
        frontmatter(contains_third_party_editorial_text="true", editorial_permission="pending") + FULL_SECTIONS,
    )
    errs = vwd.validate(p)
    check(
        any("tercero" in e.lower() for e in errs),
        "texto editorial de tercero con permiso 'pending' (no 'granted') falla",
        str(errs),
    )
    # ...pero con permiso granted, sí pasa esa regla concreta.
    p = write(
        root,
        frontmatter(contains_third_party_editorial_text="true", editorial_permission="granted") + FULL_SECTIONS,
    )
    errs = vwd.validate(p)
    check(
        not any("tercero" in e.lower() for e in errs),
        "texto editorial de tercero con permiso 'granted' no dispara esa regla",
        str(errs),
    )

    # 7. IDEA 40 absorbida: content_variant: discard es un valor válido.
    p = write(root, frontmatter(content_variant="discard", status="draft"))
    errs = vwd.validate(p)
    check(
        not any("content_variant" in e for e in errs),
        "content_variant: discard (IDEA 40) es válido",
        str(errs),
    )
    p = write(root, frontmatter(content_variant="before_after", status="draft"))
    errs = vwd.validate(p)
    check(
        not any("content_variant" in e for e in errs),
        "content_variant: before_after (IDEA 39) es válido",
        str(errs),
    )
    p = write(root, frontmatter(content_variant="inventado", status="draft"))
    errs = vwd.validate(p)
    check(any("content_variant" in e for e in errs), "content_variant desconocido falla", str(errs))

    # 8. Sección obligatoria ausente o vacía en estado published -> falla.
    incomplete = "\n".join(
        f"## {h}\nContenido real.\n" for h in vwd.REQUIRED_SECTIONS if h != "Qué perdí o qué coste tuvo"
    )
    p = write(root, frontmatter(status="published") + incomplete)
    errs = vwd.validate(p)
    check(
        any("Qué perdí o qué coste tuvo" in e for e in errs),
        "publicado sin la sección de coste/trade-off falla (doc 50 §5, pregunta 5)",
        str(errs),
    )

    # 9. Caso feliz: published, completo, sin pendientes -> pasa limpio.
    p = write(root, frontmatter(status="published") + FULL_SECTIONS)
    errs = vwd.validate(p)
    check(errs == [], "una pieza published completa y sin [[pendiente]] pasa limpia", str(errs))

    # 10. Sin publicar (draft/review), las secciones y la evidencia NO son
    # obligatorias todavía -- el gate solo se activa al pasar a published.
    # (doc 50 no pide bloquear el trabajo en curso, solo la publicación.)
    p = write(root, frontmatter(status="review", source_evidence=""))
    errs = vwd.validate(p)
    check(
        not any("source_evidence" in e for e in errs),
        "status=review no exige aún evidencia completa (solo published la exige)",
        str(errs),
    )

# 11. No existe todavía ningún hub ni artículo público de decisiones de
# escritura -- confirma que doc 50 §7 ("No crear todavía") se está respetando
# de verdad, no que simplemente nadie lo ha comprobado.
no_hub = not (ROOT / "cuaderno" / "decisiones-de-escritura").exists()
check(no_hub, "no existe /cuaderno/decisiones-de-escritura/ todavía (doc 50 §7: correcto, no es un gap)")

print("tests/test-validate-writing-decision: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
