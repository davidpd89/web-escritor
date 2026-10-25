"""Preflight del lote ya combinado, antes de abrir PR/consumir CI.

Se ejecutan en el worktree del lote todos los tests de las correcciones incluidas,
no solo los de la ultima correccion. Reutiliza Pr._test para navegadores y servidor
local aislado, y no ejecuta comandos propuestos libremente por un modelo.
"""
import json
from pathlib import Path


def validate_combined(pr, db, worktree, rows):
    """-> (passed: bool, detail: str); falla cerrado si falta un test."""
    tests = set()
    for row in rows:
        ids = json.loads(row["propuestas"] or "[]")
        tests.update(pr._rutas_tests(db, ids))
    if not tests:
        return False, "sin tests asociados al lote"
    root = Path(worktree)
    for path in sorted(tests):
        if not pr.comando_test(path) or not (root / path).is_file():
            return False, f"test acumulado ausente/no ejecutable: {path}"
        code, output = pr._test(worktree, path)
        if code == 125:
            return None, f"entorno no disponible en {path}: {output[-350:]}"
        if code != 0:
            return False, f"test acumulado {path} fallo ({code}): {output[-500:]}"
    # Tests vecinos: los tests Python ya existentes que nombran un fichero de produccion tocado. El CI los ejecuta y un lote que los rompia
    # se descubria tras 20 min de CI (#844: tests/test-build-pagefind-index.py). Solo cuenta como regresion lo que en main pasa.
    vec = vecinos(root, cambiados(pr, worktree), tests)
    rotos = []
    for path in vec:
        code, output = pr._test(worktree, path)
        if code not in (0, 125): rotos.append((path, code, output))
    if rotos:
        nuevos = [x for x in rotos if pasa_en_main(pr, x[0])]
        if nuevos:
            path, code, output = nuevos[0]
            return False, f"test vecino {path} pasa en main y falla con el lote ({code}): {output[-500:]}"
    return True, f"{len(tests)} tests acumulados y {len(vec)} vecinos pasan sobre el lote integrado" + (f" ({len(rotos)} vecinos ya fallaban en main)" if rotos else "")


def cambiados(pr, worktree):
    if not hasattr(pr, "git"): return []
    rc, out = pr.git("diff", "--name-only", "origin/main...HEAD", cwd=worktree)
    return out.split() if rc == 0 else []


def vecinos(root, ficheros, ya, maxi=25):
    """tests/test*.py que citan el nombre (sin extension) de un fichero de produccion tocado. Nombres cortos o genericos (script.js) se ignoran:
    casarian con medio repo."""
    nombres = {Path(f).stem for f in ficheros if not f.startswith(("tests/", "qa/", "pagefind/")) and f.endswith((".py", ".mjs", ".js")) and len(Path(f).stem) >= 8}
    if not nombres: return []
    out = []
    for t in sorted((Path(root) / "tests").glob("test*.py")):
        rel = "tests/" + t.name
        if rel in ya: continue
        try: s = t.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        if any(n in s for n in nombres): out.append(rel)
    return out[:maxi]


def pasa_en_main(pr, path):
    """Ejecuta el test en un worktree limpio de origin/main: si alli tambien falla, el fallo no es del lote. Ante la duda (sin git/entorno), si."""
    if not hasattr(pr, "git") or not hasattr(pr, "q"): return True
    wt = Path(pr.q.STATE) / "pr" / "preflight-main"
    try:
        if wt.exists(): pr.limpiar(wt, None)
        if pr.git("worktree", "add", "--detach", str(wt), "origin/main")[0]: return True
        code, _ = pr._test(wt, path)
        return code == 0
    finally:
        pr.limpiar(wt, None)
