#!/usr/bin/env python3
"""Preflight del laboratorio: comprueba el entorno ANTES de reservar o enviar nada. Sin red, sin modelos, sin Actions.

  python preflight.py --offline   sintaxis de los .py, version de Python, git, configuracion y aislamiento frente al QA
  python preflight.py --real      ademas: Project de ChatGPT, playwright, Edge, Claude CLI, gh y node (solo comprueba que existen)

PROCEDENCIA: motor/preflight.py de la PR #819 @ e216858c18551cc51f25fa29f809f760c46e6004 (estructura de controles y salida JSON), ampliado con el
aislamiento del QA, el estado fuera de Git y la deteccion de Python/Edge/Claude para los lanzadores .bat.
"""
import argparse, ast, importlib.util, json, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def verificar(real=False):
    import mw
    r = {"ok": True, "modo": "real" if real else "offline", "controles": []}

    def comprobar(nombre, valido, detalle, critico=True):
        """Un control no critico (node, gh) que falta es un AVISO: no impide INICIAR (solo hacen falta en EJECUTAR / tests .mjs)."""
        r["controles"].append({"control": nombre, "ok": bool(valido) or not critico, "detalle": detalle if valido or critico else "AVISO: " + detalle})
        if not valido and critico: r["ok"] = False
    comprobar("python>=3.10", sys.version_info >= (3, 10), sys.version.split()[0])
    archivos = sorted([*HERE.glob("*.py"), *(HERE.parent / "tests").glob("*.py")]); errores = []
    for f in archivos:
        try: ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except (SyntaxError, OSError, UnicodeError) as exc: errores.append(f"{f.name}: {str(exc)[:120]}")
    comprobar("sintaxis_python", not errores, f"{len(archivos)} archivos; {errores[:3]}")
    comprobar("git", shutil.which("git") is not None, shutil.which("git") or "git no esta en el PATH")
    comprobar("aislamiento_qa", not mw.verificar_aislamiento(), "; ".join(mw.verificar_aislamiento()) or f"estado en {mw.STATE}")
    try: mw.STATE.mkdir(parents=True, exist_ok=True); (mw.STATE / ".escribible").write_text("1"); (mw.STATE / ".escribible").unlink(); ok = True
    except OSError as e: ok = False; comprobar("estado_escribible", False, str(e)[:120])
    if ok: comprobar("estado_escribible", True, str(mw.STATE))
    for f in ("investigar.txt", "desarrollar.txt", "contrastar.txt", "revisar.txt"): comprobar("prompt_" + f, (mw.LAB / "prompts" / f).is_file(), f)
    if real:
        pid = mw.CFG["gpt"].get("project_id", "")
        comprobar("project_chatgpt", pid.startswith("g-p-") and pid != "g-p-6adb128351e481919fef7901e111d1ac", "configurado" if pid else "FALTA gpt.project_id en config.json (o MEJORAS_WEB_PROJECT_ID)")
        try: pw = importlib.util.find_spec("playwright.sync_api") is not None
        except (ImportError, ModuleNotFoundError): pw = False
        comprobar("playwright", pw, "playwright importable" if pw else "pip install playwright")
        import edge_launcher
        comprobar("edge", Path(edge_launcher.EDGE).is_file(), edge_launcher.EDGE)
        comprobar("node", shutil.which("node") is not None, shutil.which("node") or "node no esta en el PATH (solo hace falta para tests .mjs)", critico=False)
        comprobar("gh_cli", shutil.which("gh") is not None, shutil.which("gh") or "gh no esta en el PATH (lo necesita EJECUTAR; autenticacion sin verificar)", critico=False)
        try:
            import claude_cli; exe = claude_cli.exe(); comprobar("claude_cli", True, exe)
        except Exception as exc: comprobar("claude_cli", False, str(exc)[:200])
    return r


def main():
    p = argparse.ArgumentParser(); g = p.add_mutually_exclusive_group()
    g.add_argument("--real", action="store_true"); g.add_argument("--offline", action="store_true")
    a = p.parse_args(); out = verificar(real=a.real)
    for c in out["controles"]: print(f"[{'OK' if c['ok'] else 'FALLA'}] {c['control']}: {c['detalle']}")
    print("PREFLIGHT " + ("OK" if out["ok"] else "CON PROBLEMAS (arregla los marcados FALLA)"))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
