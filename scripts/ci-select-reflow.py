#!/usr/bin/env python3
"""Decide si una PR necesita la auditoria Sitewide Reflow (~60 min).

Regla (conservadora, determinista): la auditoria solo se omite si TODOS los
archivos cambiados pertenecen a un conjunto que no puede alterar los bytes que
sirve el sitio ni el propio QA. Cualquier archivo desconocido => se ejecuta.
Los eventos que no son pull_request (push a main, schedule, dispatch) siempre
ejecutan la auditoria completa.

Salida: `run=true|false` y `reason=...` en $GITHUB_OUTPUT, y un resumen
legible en $GITHUB_STEP_SUMMARY. El job requerido sigue existiendo y termina
en verde con la razon visible; no queda ningun check pendiente.
"""
from __future__ import annotations

import fnmatch
import os
import subprocess
import sys

# Generadores y shell compartido: se mantienen como relevantes (igual que el
# filtro paths historico de push) aunque su salida ya viaje en el diff.
ALWAYS_RELEVANT = (
    "scripts/build-*.py",
    "scripts/site_shell.py",
    ".github/workflows/sitewide-reflow-qa.yml",
    "scripts/ci-select-reflow.py",
    "tests/test-ci-select-reflow.py",
)

# Rutas que no alteran lo que sirve el sitio ni la auditoria de reflow.
SAFE_IGNORE = (
    "*.md",
    ".ci/*",
    "docs/*",
    "tests/*",
    "scripts/*",
    ".github/workflows/*",
    ".github/*.md",
    ".gitignore",
    ".gitattributes",
)


def classify(files: list[str]) -> tuple[bool, str]:
    if not files:
        return True, "sin lista de archivos: se ejecuta por seguridad"
    relevant = []
    for f in files:
        f = f.replace("\\", "/")
        if any(fnmatch.fnmatchcase(f, p) for p in ALWAYS_RELEVANT):
            relevant.append(f)
        elif not any(fnmatch.fnmatchcase(f, p) for p in SAFE_IGNORE):
            relevant.append(f)
    if relevant:
        return True, "afectan al sitio o al QA: " + ", ".join(relevant[:8]) + (" ..." if len(relevant) > 8 else "")
    return False, f"{len(files)} archivo(s) fuera del sitio servido y del QA de reflow (scripts, tests, docs, workflows ajenos)"


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", base, head], capture_output=True, text=True, check=True).stdout
    return [x for x in out.splitlines() if x.strip()]


def main() -> int:
    event = os.environ.get("EVENT_NAME", "")
    base = os.environ.get("BASE_SHA", "")
    head = os.environ.get("HEAD_SHA", "HEAD")
    if event != "pull_request":
        run, reason = True, f"evento {event or 'desconocido'}: auditoria completa"
    elif not base:
        run, reason = True, "sin SHA base: se ejecuta por seguridad"
    else:
        try:
            run, reason = classify(changed_files(base, head))
        except subprocess.CalledProcessError as exc:
            run, reason = True, f"no se pudo calcular el diff ({exc.returncode}): se ejecuta por seguridad"
    line = f"run={'true' if run else 'false'}"
    print(line, "|", reason)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(f"### Sitewide Reflow: {'EJECUTADO' if run else 'OMITIDO (no aplicable)'}\n{reason}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
