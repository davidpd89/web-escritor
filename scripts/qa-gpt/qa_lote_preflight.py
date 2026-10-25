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
        if code != 0:
            return False, f"test acumulado {path} fallo ({code}): {output[-500:]}"
    return True, f"{len(tests)} tests acumulados pasan sobre el lote integrado"
