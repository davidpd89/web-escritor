#!/usr/bin/env python3
"""Los 9 casos de QA del doc 62 (sección "QA"), verificados contra el motor real.

Doc 62 es explícito sobre el gate: "No publicar /cuaderno/laboratorio-web/
vacío" y exige al menos 2 piezas publicables. data/web-lab-entries.json es
la copia real (ahora en su sitio en /data/, no solo en el borrador de
CODIGO PROPUESTO) de los dos candidatos que el propio documento describe —
ambos siguen en publish:false, tal como el documento los dejó, porque
publicarlos exigiría escribir la narrativa en primera persona de David sobre
su propio proceso, que no es algo que se pueda fabricar.

Uso:
  python tests/test-web-lab.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


vwl = load("vwl", "validate-web-lab-entry.py")
bwl = load("bwl", "build-web-lab-index.py")

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


SECTIONS = {
    "Problema real": "Las herramientas de manuscrito prometían que el texto no salía del navegador, pero cargaban script.js global.",
    "Situación inicial / baseline": "Todas las páginas de herramientas cargaban el mismo script.js que el resto del sitio, con GoatCounter y newsletter.",
    "Qué cambié o comprobé": "Se creó un contrato de CSP estricta con connect-src none y se retiró script.js global de esas páginas.",
    "Cómo lo medí": "audit-private-tools.py escanea cada página en busca de fetch/XHR/localStorage y confirma la CSP declarada.",
    "Resultado observable": "Las páginas de herramientas pasan el preflight sin ninguna conexión saliente detectada en ningún caso.",
    "Lo que NO puedo concluir": "No puedo afirmar que ningún otro vector de fuga exista fuera de lo que el escáner cubre hoy.",
    "Qué haría diferente": "Empezaría con el contrato de privacidad estricto desde la primera herramienta, no como una migración posterior.",
    "Reproducibilidad / recursos": "Ver scripts/audit-private-tools.py y su documentación en el propio repositorio del sitio.",
}


def entry_text(meta_overrides: dict | None = None, section_overrides: dict | None = None) -> str:
    meta = {
        "status": "review",
        "entry_type": "decision",
        "slug": "privacidad-real-manuscrito",
        "title": "Por qué script.js global invalidaba una promesa de privacidad",
        "question": "¿Bastaba con connect-src none para prometer procesamiento local?",
        "started_on": "2026-08-01",
        "ended_on": "2026-08-19",
        "public_url": "https://davidportodiaz.com/cuaderno/privacidad-real-manuscrito/",
        "measurement_source": "audit-private-tools.py, revisión manual de red",
        "has_control_group": "false",
        "contains_private_metrics": "false",
        "publish": "true",
    }
    meta.update(meta_overrides or {})
    sections = dict(SECTIONS)
    sections.update(section_overrides or {})
    fm = "---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n\n"
    body = "".join(f"# {name}\n\n{text}\n\n" for name, text in sections.items())
    return fm + body


def write(tmp: Path, text: str) -> Path:
    p = tmp / "entry.md"
    p.write_text(text, encoding="utf-8")
    return p


print("tests/test-web-lab")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # 1. draft publish:false -> pasa como borrador.
    errs_or_pass = vwl  # se comprueba por código de retorno via main(), no validate() suelto
    sys.argv = ["validate-web-lab-entry.py", str(ROOT / "scripts" / "templates" / "web-lab-entry.template.md")]
    check(vwl.main() == 0, "1. plantilla draft/publish:false -> pasa como borrador")

    # 2. experiment sin has_control_group:true -> falla.
    p = write(root, entry_text({"entry_type": "experiment", "has_control_group": "false"}))
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    try:
        vwl.main()
        check(False, "2. experiment sin has_control_group:true -> falla")
    except ValueError as exc:
        check("has_control_group" in str(exc), "2. experiment sin has_control_group:true -> falla", str(exc))

    # 3. pieza publicable con sección pendiente -> falla.
    p = write(root, entry_text(section_overrides={"Qué haría diferente": "[[pendiente]]"}))
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    try:
        vwl.main()
        check(False, "3. sección con [[pendiente]] -> falla")
    except ValueError as exc:
        check("insuficiente" in str(exc), "3. sección con [[pendiente]] -> falla", str(exc))

    # 4. URL pública fuera del dominio propio -> falla.
    p = write(root, entry_text({"public_url": "https://medium.com/algo"}))
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    try:
        vwl.main()
        check(False, "4. public_url fuera de davidportodiaz.com -> falla")
    except ValueError as exc:
        check("canónica" in str(exc), "4. public_url fuera de davidportodiaz.com -> falla", str(exc))

    # 5. contains_private_metrics:true -> bloquea publicación.
    p = write(root, entry_text({"contains_private_metrics": "true"}))
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    try:
        vwl.main()
        check(False, "5. contains_private_metrics:true -> falla")
    except ValueError as exc:
        check("contains_private_metrics" in str(exc), "5. contains_private_metrics:true -> falla", str(exc))

    # 6. palabras de credenciales -> bloqueo preventivo (con sección lo
    # bastante larga para no fallar antes por longitud insuficiente).
    p = write(
        root,
        entry_text(
            section_overrides={
                "Reproducibilidad / recursos": (
                    "Ver scripts/audit-private-tools.py en el repositorio. Para reproducir esto en tu "
                    "propio entorno necesitas configurar tu api key personal en el fichero de entorno."
                )
            }
        ),
    )
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    try:
        vwl.main()
        check(False, "6. texto con 'api key' -> bloqueo preventivo de credencial")
    except ValueError as exc:
        check("secreto" in str(exc).lower() or "credencial" in str(exc).lower(), "6. texto con 'api key' -> bloqueo preventivo de credencial", str(exc))

    # Caso feliz individual (necesario para aislar los casos anteriores):
    p = write(root, entry_text())
    sys.argv = ["validate-web-lab-entry.py", str(p)]
    check(vwl.main() == 0, "extra: entrada completa y correcta -> pasa")

    # 7. hub con <2 piezas publicables -> falla.
    index_1pub = {
        "updated_on": "2026-08-21",
        "entries": [
            {
                "slug": "caso-uno",
                "title": "Caso uno",
                "entry_type": "decision",
                "summary": "Resumen suficientemente largo del primer caso de prueba para superar la validación de longitud mínima.",
                "date": "2026-08-10",
                "url": "/cuaderno/caso-uno/",
                "publish": True,
            }
        ],
    }
    today = date.fromisoformat("2026-08-21")
    try:
        bwl.validate(index_1pub, today)
        check(False, "7. hub con solo 1 pieza publicable -> falla")
    except ValueError as exc:
        check("al menos 2" in str(exc), "7. hub con solo 1 pieza publicable -> falla", str(exc))

    # 8. 2 piezas válidas -> CollectionPage + ItemList con ambas.
    index_2pub = {
        "updated_on": "2026-08-21",
        "entries": index_1pub["entries"]
        + [
            {
                "slug": "caso-dos",
                "title": "Caso dos",
                "entry_type": "audit",
                "summary": "Resumen suficientemente largo del segundo caso de prueba para superar la validación de longitud mínima.",
                "date": "2026-08-15",
                "url": "/cuaderno/caso-dos/",
                "publish": True,
            }
        ],
    }
    items = bwl.validate(index_2pub, today)
    html_out = bwl.render(items, "2026-08-21")
    ldjson_start = html_out.index('<script type="application/ld+json">') + len('<script type="application/ld+json">')
    ldjson_end = html_out.index("</script>", ldjson_start)
    schema = json.loads(html_out[ldjson_start:ldjson_end])
    check(
        schema["@type"] == "CollectionPage" and schema["mainEntity"]["@type"] == "ItemList" and len(schema["mainEntity"]["itemListElement"]) == 2,
        "8. 2 piezas válidas -> genera CollectionPage + ItemList con ambas",
        str(schema),
    )

    # 9. --check detecta desalineación.
    json_path = root / "index.json"
    out_path = root / "hub.html"
    json_path.write_text(json.dumps(index_2pub), encoding="utf-8")
    sys.argv = ["build-web-lab-index.py", str(json_path), "--output", str(out_path), "--today", "2026-08-21"]
    check(bwl.main() == 0, "9a. generación inicial del hub con 2 piezas -> OK")
    sys.argv = ["build-web-lab-index.py", str(json_path), "--output", str(out_path), "--today", "2026-08-21", "--check"]
    check(bwl.main() == 0, "9b. --check sobre salida recién generada -> PASS")
    index_2pub["entries"][0]["title"] = "Caso uno RENOMBRADO"
    json_path.write_text(json.dumps(index_2pub), encoding="utf-8")
    sys.argv = ["build-web-lab-index.py", str(json_path), "--output", str(out_path), "--today", "2026-08-21", "--check"]
    check(bwl.main() == 1, "9c. --check detecta desalineación tras editar el JSON sin regenerar")

# El manifest real (data/web-lab-entries.json) sigue con publish:false en
# ambos candidatos -- correcto por diseño (doc 62: "no publicar vacío" y los
# dos casos exigen convertirse en artículos reales primero). Si alguna vez se
# flipa a true sin pasar por el validador de la entrada individual, el propio
# builder ya lo rechazaría por sí solo (menos de 2 piezas si solo se activa
# una, o exigiría el contrato editorial completo si se activan ambas).
real_data = json.loads((ROOT / "data" / "web-lab-entries.json").read_text(encoding="utf-8"))
any_published = any(e.get("publish") for e in real_data.get("entries", []))
check(not any_published, "el manifest real (data/web-lab-entries.json) no publica ningún candidato todavía")
check(len(real_data.get("entries", [])) == 2, "el manifest real conserva los 2 candidatos que describe el documento")

print("tests/test-web-lab: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
