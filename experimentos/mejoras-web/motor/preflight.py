#!/usr/bin/env python3
"""Verificaciones locales, sin red, sin ejecutores CI ni consultas a IA."""
from __future__ import annotations
import argparse, ast, importlib.util, json, os, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
LAB=HERE.parent
REPO=LAB.parents[1]
sys.path.insert(0,str(HERE))


def verificar(real=False, repo=REPO, lab=LAB):
    resultado={"ok":True,"modo":"real" if real else "offline","controles":[]}
    def comprobar(nombre,valido,detalle):
        resultado["controles"].append({"control":nombre,"ok":bool(valido),"detalle":detalle})
        if not valido: resultado["ok"]=False
    comprobar("python>=3.10",sys.version_info>=(3,10),sys.version.split()[0])
    archivos=sorted([lab/"rotacion.py",lab/"verificar.py",*HERE.glob("*.py"),
                      *lab.glob("test_*.py")])
    errores=[]
    for f in archivos:
        try: ast.parse(f.read_text(encoding="utf-8"),filename=str(f))
        except (SyntaxError,OSError,UnicodeError) as exc: errores.append(str(exc)[:180])
    comprobar("sintaxis_python",not errores,f"{len(archivos)} archivos; {errores[:3]}")
    try:
        git=subprocess.run(["git","-C",str(repo),"branch","--show-current"],
             capture_output=True,text=True,timeout=8)
        rama=git.stdout.strip() if git.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):
        rama=""
    comprobar("rama_laboratorio",rama.startswith(("research/mejoras-","lab/mejoras-","feature/mejoras-")),
              rama or "No se pudo obtener rama Git")
    if real:
        project=os.environ.get("LAB_MEJORAS_PROJECT_ID","").strip()
        comprobar("project_chatgpt",bool(project) and project.startswith("g-p-"),
                  "configurado" if project else "LAB_MEJORAS_PROJECT_ID ausente")
        try: present=importlib.util.find_spec("playwright.sync_api") is not None
        except (ImportError,ModuleNotFoundError): present=False
        comprobar("playwright",present,"playwright.sync_api importable" if present else "instalar playwright")
        comprobar("gh_cli",shutil.which("gh") is not None,"gh en PATH (autenticación pendiente de verificación manual)")
        try:
            import claude_cli
            exe=claude_cli.exe()
        except (OSError,RuntimeError) as exc:
            exe=""
            reason=str(exc)[:250]
        else:
            reason="Ejecutable nativo: "+exe
        comprobar("claude_nativo",bool(exe),reason)
    return resultado


def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group()
    g.add_argument("--real",action="store_true")
    g.add_argument("--offline",action="store_true")
    a=p.parse_args()
    output=verificar(real=a.real)
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if output["ok"] else 2


if __name__=="__main__":
    raise SystemExit(main())
