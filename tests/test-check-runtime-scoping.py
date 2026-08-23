#!/usr/bin/env python3
"""Unit fixtures for scripts/check-runtime-scoping.py."""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("crs", ROOT / "scripts" / "check-runtime-scoping.py")
crs = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = crs
_spec.loader.exec_module(crs)
failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def git_init(tmp: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "fixture"], cwd=tmp, check=True)


def write(tmp: Path, rel: str, text: str) -> None:
    path = tmp / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def base_repo(tmp: Path) -> None:
    write(tmp, "script.js", '''function scheduleTask(fn){return Promise.resolve().then(fn)}\n// Back-to-top button\n(function(){const btn=document.createElement("button");btn.addEventListener("click", () => {\n  const reduced=window.matchMedia("(prefers-reduced-motion: reduce)").matches;\n  window.scrollTo({top:0,behavior:reduced?"auto":"smooth"});\n});})();\n''')
    write(tmp, "styles.css", ".ok{display:block}\n")
    write(tmp, "assets/samuel-buy-modal.css", "#buy-dialog{} .buy-dialog-inner{} .buy-option{}\n")
    write(tmp, "assets/samuel-buy-modal.js", '''(function(){const EXPECTED_PATH = "/libros/samuel-entre-mundos/";const pageRoot=document.querySelector('main[data-family="book-samuel"]');const STYLE_HREF = "/assets/samuel-buy-modal.css";if(!pageRoot)return;pageRoot.addEventListener("click",()=>{});})();\n''')
    write(tmp, "assets/newsletter-popup.js", '''(function(){const d=document.createElement("dialog");d.showModal();})();\n''')
    write(tmp, "assets/newsletter-popup.css", "#nl-popup-dialog{}\n")
    write(tmp, "index.html", "<html><body></body></html>")
    write(tmp, "cuaderno/index.html", '<script src="/script.js"></script><link href="/assets/newsletter-popup.css"><script src="/assets/newsletter-popup.js"></script>')
    write(tmp, crs.SAMUEL_PAGE, '<main data-family="book-samuel"><button data-buy-modal></button></main><script src="/assets/samuel-buy-modal.js"></script>')


def all_checks(tmp: Path) -> list[str]:
    pages = crs.tracked_html(tmp)
    return (crs.check_script_js(tmp) + crs.check_buy_modal_scope(tmp, pages) + crs.check_popup_scope(tmp, pages) + crs.check_global_css(tmp) + crs.check_mojibake(tmp))


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp); git_init(tmp)
        check(all_checks(tmp) == [], "repo correctamente scoped pasa", str(all_checks(tmp)))

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "script.js", 'd.id = "buy-dialog";\n')
        git_init(tmp)
        check(any("modal Samuel" in e for e in crs.check_script_js(tmp)), "modal reimplementado en script.js se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "otra.html", '<button data-buy-modal></button><script src="/assets/samuel-buy-modal.js"></script>')
        git_init(tmp)
        check(any("fuera de su única página" in e for e in crs.check_buy_modal_scope(tmp, crs.tracked_html(tmp))), "runtime Samuel fuera de scope se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "styles.css", "#buy-dialog{display:block}\n")
        git_init(tmp)
        check(any("CSS específico" in e for e in crs.check_global_css(tmp)), "CSS Samuel global se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "styles.css", ".x::before{content:'Ã¢â‚¬â€'}\n")
        git_init(tmp)
        check(any("mojibake" in e for e in crs.check_mojibake(tmp)), "mojibake se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "index.html", '<script src="/script.js"></script><link href="/assets/newsletter-popup.css"><script src="/assets/newsletter-popup.js"></script>')
        git_init(tmp)
        check(any("fuera de scope" in e for e in crs.check_popup_scope(tmp, crs.tracked_html(tmp))), "popup fuera de scope se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        text = (tmp / "script.js").read_text(encoding="utf-8").replace('const reduced=window.matchMedia', 'scheduleTask(()=>{});const reduced=window.matchMedia')
        write(tmp, "script.js", text); git_init(tmp)
        check(any("difiere scrollTo" in e for e in crs.check_script_js(tmp)), "back-to-top diferido se detecta")

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d); base_repo(tmp)
        write(tmp, "assets/samuel-buy-modal.js", '(function(){document.addEventListener("keydown",()=>{});})();\n')
        git_init(tmp)
        check(any("focus trap manual" in e for e in crs.check_buy_modal_scope(tmp, crs.tracked_html(tmp))), "focus trap manual Samuel se detecta")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-runtime-scoping: OK")


if __name__ == "__main__":
    run()
