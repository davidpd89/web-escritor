#!/usr/bin/env python3
"""Los 8 casos de QA del doc 63 (seccion "QA"), verificados contra el motor real.

Doc 63 es explicito: NO crear el repositorio publico todavia, y NO decidir
licencia sin autorizacion expresa del usuario ("El usuario debe autorizar
expresamente la licencia elegida porque concede derechos a terceros"). Este
test no publica nada ni toca ningun repositorio real -- solo ejerce
scripts/build-open-source-export.py contra un fixture temporal, para
confirmar que sus protecciones (allowlist, confinamiento de rutas, bloqueo
de secretos, gate de licencia) funcionan de verdad antes de que alguien
pulse el gatillo real.

Uso:
  python tests/test-build-open-source-export.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("bose", ROOT / "scripts" / "build-open-source-export.py")
bose = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bose
_spec.loader.exec_module(bose)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


BASE_MANIFEST = {
    "repository_name": "herramientas-escritores-es",
    "repository_description": "Microherramientas de escritura en español, código abierto.",
    "license": None,
    "topics": ["writing-tools", "writers", "spanish"],
    "tools": [
        {
            "slug": "tool-a",
            "name": "Tool A",
            "description": "Herramienta de prueba A con descripción suficientemente larga para pasar la validación.",
            "demo_url": "https://davidportodiaz.com/herramientas/tool-a/",
            "export": True,
            "files": ["assets/tool-a-engine.js"],
            "third_party": [],
        },
        {
            "slug": "tool-b",
            "name": "Tool B",
            "description": "Herramienta de prueba B con descripción suficientemente larga para pasar la validación.",
            "demo_url": "https://davidportodiaz.com/herramientas/tool-b/",
            "export": True,
            "files": ["assets/tool-b-engine.js"],
            "third_party": ["silabajs 2.1.0 (MIT)"],
        },
    ],
}


def setup_source(root: Path) -> Path:
    source = root / "source"
    (source / "assets").mkdir(parents=True)
    (source / "assets" / "tool-a-engine.js").write_text("export function add(a,b){return a+b;}", encoding="utf-8")
    (source / "assets" / "tool-b-engine.js").write_text("export function double(a){return a*2;}", encoding="utf-8")
    (source / "assets" / "tool-b-secret.js").write_text('const API_KEY = "sk-abc123";', encoding="utf-8")
    return source


def write_manifest(root: Path, data: dict, name: str = "manifest.json") -> Path:
    p = root / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


print("tests/test-build-open-source-export")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = setup_source(root)
    out = root / "out"

    # 1. export explícito de dos herramientas -> genera staging con ambas.
    manifest = write_manifest(root, BASE_MANIFEST)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    tools = bose.validate(data, source)
    check(len(tools) == 2, "1. export explícito de 2 herramientas -> valida ambas", str(len(tools)))

    # Generar realmente el staging (temporal, nunca sale de tempfile) para
    # los casos 2-5.
    sys.argv = ["build-open-source-export.py", str(manifest), "--source", str(source), "--output", str(out)]
    bose.main()

    # 2. license:null -> LICENSE-REQUIRED.txt, staging no publicable.
    license_file = out / "LICENSE-REQUIRED.txt"
    check(license_file.exists(), "2. license:null genera LICENSE-REQUIRED.txt", str(out.iterdir()))

    # 3. generación de THIRD_PARTY_NOTICES.md con el aviso declarado.
    notices = (out / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    check("silabajs" in notices, "3. THIRD_PARTY_NOTICES.md incluye el aviso declarado", notices)

    # 4. EXPORT-MANIFEST.json con hashes SHA-256 de 64 caracteres hex.
    manifest_out = json.loads((out / "EXPORT-MANIFEST.json").read_text(encoding="utf-8"))
    hashes_ok = all(len(f["sha256"]) == 64 and all(c in "0123456789abcdef" for c in f["sha256"]) for f in manifest_out["files"])
    check(hashes_ok and len(manifest_out["files"]) == 2, "4. EXPORT-MANIFEST.json tiene hashes SHA-256 válidos de los 2 archivos", str(manifest_out))

    # 5. --check de integridad: pasa en staging intacto, falla tras alterar
    # un archivo exportado.
    sys.argv = ["build-open-source-export.py", str(manifest), "--source", str(source), "--output", str(out), "--check"]
    check(bose.main() == 0, "5a. --check pasa sobre un staging intacto")
    tampered = out / "tools" / "tool-a" / "tool-a-engine.js"
    tampered.write_text(tampered.read_text(encoding="utf-8") + "\n// alterado", encoding="utf-8")
    check(bose.main() == 1, "5b. --check detecta un archivo exportado alterado (deriva)")

    # 6. archivo sensible no allowlisted -> rechazado por patrón de secreto.
    bad = json.loads(json.dumps(BASE_MANIFEST))
    bad["tools"][1]["files"] = ["assets/tool-b-engine.js", "assets/tool-b-secret.js"]
    try:
        bose.validate(bad, source)
        check(False, "6. archivo con posible secreto debe rechazar el export")
    except ValueError as exc:
        check("secreto" in str(exc).lower() or "privado" in str(exc).lower(), "6. archivo con posible secreto se rechaza", str(exc))

    # 7. path traversal rechazado, incluso con extensión permitida.
    outside = root / "outside.js"
    outside.write_text("// fuera del source", encoding="utf-8")
    bad = json.loads(json.dumps(BASE_MANIFEST))
    bad["tools"][0]["files"] = ["../outside.js"]
    try:
        bose.validate(bad, source)
        check(False, "7. path traversal (con extensión .js válida) debe rechazarse")
    except ValueError as exc:
        check("source" in str(exc).lower(), "7. path traversal se rechaza por confinamiento de ruta", str(exc))

    # 8. herramienta sin archivos -> rechazada.
    bad = json.loads(json.dumps(BASE_MANIFEST))
    bad["tools"][0]["files"] = []
    try:
        bose.validate(bad, source)
        check(False, "8. herramienta export=true sin archivos debe rechazarse")
    except ValueError as exc:
        check("sin archivos" in str(exc), "8. herramienta sin archivos se rechaza", str(exc))

    # Extra: tools con export=false se ignoran silenciosamente (no cuentan
    # como error ni se incluyen) -- así es como el manifest real del repo
    # (data/open-source-tools.json) puede tener export:false en todo sin que
    # el validador se queje de "no hay herramientas", siempre que exista AL
    # MENOS una con export:true en el fixture.
    only_disabled = json.loads(json.dumps(BASE_MANIFEST))
    for t in only_disabled["tools"]:
        t["export"] = False
    try:
        bose.validate(only_disabled, source)
        check(False, "extra: manifest sin ninguna herramienta export=true debe rechazarse")
    except ValueError as exc:
        check("no hay herramientas" in str(exc).lower(), "extra: cero herramientas export=true se rechaza", str(exc))

# El manifest REAL del repositorio (data/open-source-tools.json) debe seguir
# teniendo export:false en todo -- doc 63: "no autorizar ninguna exportación
# por accidente". Si algún día cambia a true sin querer, este test debe
# avisar en vez de dejarlo pasar en silencio.
real_manifest = json.loads((ROOT / "data" / "open-source-tools.json").read_text(encoding="utf-8"))
any_enabled = any(t.get("export") for t in real_manifest.get("tools", []))
check(
    not any_enabled,
    "el manifest real (data/open-source-tools.json) no tiene ninguna herramienta export:true todavía",
)

print("tests/test-build-open-source-export: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
