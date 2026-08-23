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

# P.2 (2026-08-23): cierre de dependencias locales + adaptaciones de
# terceros no declaradas. Caso real que motivó esto: legibilidad-engine.js
# importa silabajs-lite-2.1.0.js (adaptación MIT de terceros) y el manifest
# no lo declaraba ni en 'files' ni en 'third_party'.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = root / "assets"
    source.mkdir(parents=True)
    (source / "engine.js").write_text("import { helper } from './helper.js';\nexport function run(){return helper();}", encoding="utf-8")
    (source / "helper.js").write_text(
        "/* Adaptación mínima a partir de upstream-lib 1.0.0. Upstream: https://example.com/upstream-lib. Licencia upstream: MIT. */\nexport function helper(){return 1;}",
        encoding="utf-8",
    )

    # 9. import local transitivo no declarado en 'files' -> se rechaza.
    manifest_missing_file = {
        "repository_name": "r", "repository_description": "d", "license": None, "topics": [],
        "tools": [{
            "slug": "tool-c", "name": "Tool C",
            "description": "Herramienta de prueba C con descripción suficientemente larga para pasar la validación.",
            "demo_url": "https://davidportodiaz.com/herramientas/tool-c/",
            "export": True, "files": ["engine.js"], "third_party": [],
        }],
    }
    try:
        bose.validate(manifest_missing_file, source)
        check(False, "9. import local no declarado en 'files' debe rechazarse")
    except ValueError as exc:
        check("helper.js" in str(exc) and "faltan en 'files'" in str(exc), "9. import local no declarado en 'files' se rechaza", str(exc))

    # 10. con el import declarado pero sin third_party -> se rechaza por adaptación no declarada.
    manifest_missing_notice = json.loads(json.dumps(manifest_missing_file))
    manifest_missing_notice["tools"][0]["files"] = ["engine.js", "helper.js"]
    try:
        bose.validate(manifest_missing_notice, source)
        check(False, "10. adaptación de terceros sin declarar en third_party debe rechazarse")
    except ValueError as exc:
        check("helper.js" in str(exc) and "third_party" in str(exc), "10. adaptación no declarada en third_party se rechaza", str(exc))

    # 11. con 'files' y 'third_party' completos -> valida sin error.
    manifest_complete = json.loads(json.dumps(manifest_missing_notice))
    manifest_complete["tools"][0]["third_party"] = ["helper.js: adaptación de upstream-lib 1.0.0, licencia MIT"]
    try:
        tools_ok = bose.validate(manifest_complete, source)
        check(len(tools_ok) == 1 and len(tools_ok[0][1]) == 2, "11. cierre + third_party completos validan sin error")
    except ValueError as exc:
        check(False, "11. cierre + third_party completos validan sin error", str(exc))

# 12. --check detecta drift entre el manifest actual y el staging ya generado
# (además de la integridad de hashes ya cubierta en 5a/5b).
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = setup_source(root)
    out = root / "out"
    manifest = write_manifest(root, BASE_MANIFEST)
    sys.argv = ["build-open-source-export.py", str(manifest), "--source", str(source), "--output", str(out)]
    bose.main()
    only_tool_a = json.loads(json.dumps(BASE_MANIFEST))
    only_tool_a["tools"][1]["export"] = False
    manifest2 = write_manifest(root, only_tool_a, name="manifest2.json")
    sys.argv = ["build-open-source-export.py", str(manifest2), "--source", str(source), "--output", str(out), "--check"]
    check(bose.main() == 1, "12. --check detecta que el manifest actual (1 tool) ya no corresponde al staging (2 tools)")

# 13. Grafo REAL de legibilidad: confirma que, con el manifest real (tal como
# está en el repo, solo activando export:true en memoria para esta prueba,
# SIN escribirlo nunca a disco), el cierre resuelve exactamente
# legibilidad-engine.js + silabajs-lite-2.1.0.js y no falla.
real_source = ROOT / "assets"
real_legibilidad = json.loads(json.dumps(real_manifest))
for t in real_legibilidad["tools"]:
    t["export"] = (t["slug"] == "legibilidad")
try:
    tools_real = bose.validate(real_legibilidad, real_source, ROOT / "tests")
    real_files = {str(f.relative_to(real_source)) for _, files, _ in tools_real for _, f in files}
    check(
        real_files == {"legibilidad-engine.js", "silabajs-lite-2.1.0.js"},
        "13. el grafo real de legibilidad resuelve engine + silabajs-lite exactamente",
        str(real_files),
    )
except ValueError as exc:
    check(False, "13. el grafo real de legibilidad resuelve sin error", str(exc))

# 63-C (requisito anadido a P.2 por #74/Q.1): empaquetar y poder ejecutar los
# tests reproducibles de una herramienta exportada, de forma aislada del
# repo completo (imports reescritos a rutas planas dentro del propio paquete).
import subprocess

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    source = setup_source(root)
    tests_source = root / "tests"
    tests_source.mkdir()
    (tests_source / "test-tool-a.mjs").write_text(
        "import assert from 'node:assert/strict';\n"
        "import { add } from '../source/assets/tool-a-engine.js';\n"
        "assert.equal(add(2,3), 5);\n"
        "console.log('test-tool-a: OK');\n",
        encoding="utf-8",
    )
    manifest_with_tests = json.loads(json.dumps(BASE_MANIFEST))
    manifest_with_tests["tools"][0]["tests"] = ["test-tool-a.mjs"]
    manifest_path = write_manifest(root, manifest_with_tests, name="manifest_tests.json")

    # 14. test declarado cuyo import SI esta en 'files' -> valida sin error.
    try:
        tools_t = bose.validate(manifest_with_tests, source, tests_source)
        tool_a_tests = next(tf for t, _, tf in tools_t if t["slug"] == "tool-a")
        check(len(tool_a_tests) == 1, "14. test declarado con dependencia exportada valida sin error", str(tool_a_tests))
    except ValueError as exc:
        check(False, "14. test declarado con dependencia exportada valida sin error", str(exc))

    # 15. test cuya dependencia NO esta en 'files' -> se rechaza explicitamente.
    manifest_bad_test = json.loads(json.dumps(manifest_with_tests))
    (tests_source / "test-tool-a-bad.mjs").write_text(
        "import { helper } from '../source/assets/does-not-exist.js';\n", encoding="utf-8",
    )
    manifest_bad_test["tools"][0]["tests"] = ["test-tool-a-bad.mjs"]
    try:
        bose.validate(manifest_bad_test, source, tests_source)
        check(False, "15. test que depende de un fichero no exportado debe rechazarse")
    except ValueError as exc:
        check("does-not-exist.js" in str(exc), "15. test con dependencia no exportada se rechaza", str(exc))

    # 16. generar el staging real con --tests-source y ejecutar de verdad el
    # test empaquetado (node real, proceso aparte) para demostrar que el
    # import reescrito funciona sin el repo completo, no solo que el texto
    # contenga la cadena esperada.
    out = root / "out-tests"
    sys.argv = [
        "build-open-source-export.py", str(manifest_path),
        "--source", str(source), "--tests-source", str(tests_source),
        "--output", str(out),
    ]
    bose.main()
    staged_test = out / "tools" / "tool-a" / "tests" / "test-tool-a.mjs"
    check(staged_test.exists(), "16a. el test empaquetado existe en el staging", str(list((out/'tools'/'tool-a').rglob('*'))))
    rewritten_text = staged_test.read_text(encoding="utf-8")
    check("../tool-a-engine.js" in rewritten_text, "16b. el import se reescribe a ruta plana dentro del paquete", rewritten_text)
    proc = subprocess.run(["node", str(staged_test)], capture_output=True, text=True, cwd=str(staged_test.parent))
    check(proc.returncode == 0 and "OK" in proc.stdout, "16c. el test empaquetado se ejecuta de verdad y pasa de forma aislada", f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")

# 17. Grafo + test REALES de legibilidad: exporta de verdad (a un directorio
# temporal, nunca al repo) declarando su test real, y ejecuta ese test ya
# reescrito con node para demostrar que el paquete generado es reproducible
# fuera del repositorio, tal y como exige 63-C punto 5.
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "out-legibilidad"
    real_legibilidad_tests = json.loads(json.dumps(real_manifest))
    for t in real_legibilidad_tests["tools"]:
        t["export"] = (t["slug"] == "legibilidad")
        if t["slug"] == "legibilidad":
            t["tests"] = ["test-legibilidad.mjs"]
    manifest_path = write_manifest(Path(tmp), real_legibilidad_tests, name="manifest_legibilidad.json")
    sys.argv = [
        "build-open-source-export.py", str(manifest_path),
        "--source", str(ROOT / "assets"), "--tests-source", str(ROOT / "tests"),
        "--output", str(out),
    ]
    try:
        rc = bose.main()
        staged_test = out / "tools" / "legibilidad" / "tests" / "test-legibilidad.mjs"
        proc = subprocess.run(["node", str(staged_test)], capture_output=True, text=True, cwd=str(staged_test.parent))
        check(
            rc == 0 and proc.returncode == 0 and "OK" in proc.stdout,
            "17. el test REAL de legibilidad se ejecuta de verdad desde el staging aislado y pasa",
            f"build_rc={rc} test_rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
    except ValueError as exc:
        check(False, "17. el test real de legibilidad se empaqueta y ejecuta sin error", str(exc))

# 18. Generaliza el caso 17 a TODAS las herramientas del manifest real que
# declaran 'tests', una por una (export:true solo en memoria, nunca en
# disco), para detectar cualquier declaracion rota antes de que alguien
# active export:true de verdad.
tools_with_tests = [t["slug"] for t in real_manifest.get("tools", []) if t.get("tests")]
check(len(tools_with_tests) >= 5, "18. hay al menos 5 herramientas reales con tests declarados", str(tools_with_tests))
for slug in tools_with_tests:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        one_tool_manifest = json.loads(json.dumps(real_manifest))
        for t in one_tool_manifest["tools"]:
            t["export"] = (t["slug"] == slug)
        manifest_path = write_manifest(Path(tmp), one_tool_manifest, name="manifest.json")
        sys.argv = [
            "build-open-source-export.py", str(manifest_path),
            "--source", str(ROOT / "assets"), "--tests-source", str(ROOT / "tests"),
            "--output", str(out),
        ]
        try:
            rc = bose.main()
            test_name = next(t for t in real_manifest["tools"] if t["slug"] == slug)["tests"][0]
            staged_test = out / "tools" / slug / "tests" / test_name
            proc = subprocess.run(["node", str(staged_test)], capture_output=True, text=True, cwd=str(staged_test.parent))
            check(
                rc == 0 and proc.returncode == 0,
                f"18. {slug}: su test real se empaqueta y ejecuta aislado sin error",
                f"build_rc={rc} test_rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}",
            )
        except ValueError as exc:
            check(False, f"18. {slug}: su test real se empaqueta y ejecuta aislado sin error", str(exc))

print("tests/test-build-open-source-export: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
