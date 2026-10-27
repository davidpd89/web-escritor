#!/usr/bin/env python3
"""Lanza (o reutiliza) el Edge dedicado del laboratorio de mejoras web: CDP solo en 127.0.0.1:9331, perfil propio y persistente fuera del repo.

PROCEDENCIA: scripts/qa-gpt/edge_launcher.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0 (rama automation/qa-gpt), blob 8bdc21f28c0d475156819233c45f49237eb8ee4d.
CAMBIOS: puerto 9230 -> 9331; perfil %LOCALAPPDATA%\\web-escritor-mejoras-web\\edge-perfil (no el del QA, que vive en C:\\Temp\\web-escritor-qa-gpt-edge);
URL del Project configurable; se REHUSA arrancar con el puerto o el perfil del QA original. Mismo lanzador con banderas y sondeo del original.
No toca los puertos 9230/9224/9225 ni procesos de otros Edge.
Uso: python edge_launcher.py [--check]
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

PORT = 9331
PUERTOS_QA = (9230, 9224, 9225)
PERFIL_QA = r"C:\Temp\web-escritor-qa-gpt-edge"
EDGE = os.environ.get("MEJORAS_WEB_EDGE", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def perfil():
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "state")
    # Perfil COMPARTIDO con el QA (ya con sesion de ChatGPT): QA y laboratorio nunca corren a la vez.
    return os.environ.get("MEJORAS_WEB_PERFIL", PERFIL_QA)


def project_url():
    import gpt_browser
    return gpt_browser.PROJECT_URL or "https://chatgpt.com/"


def comprobar_aislamiento(port=None, prof=None):
    port, prof = port or PORT, prof or perfil()
    if port in PUERTOS_QA: raise SystemExit(f"puerto CDP {port} reservado al QA original")
    if os.path.normcase(os.path.abspath(prof)) == os.path.normcase(os.path.abspath(PERFIL_QA)) and _qa_vivo():
        raise SystemExit("el Edge del QA (9230) sigue abierto con este perfil: cierra el QA antes de iniciar el laboratorio")


def _qa_vivo():
    import urllib.request
    try: urllib.request.urlopen("http://127.0.0.1:9230/json/version", timeout=1); return True
    except Exception: return False


def flags(port=None, prof=None):
    return [
        f"--remote-debugging-port={port or PORT}", "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={prof or perfil()}", "--edge-skip-compat-layer-relaunch",
        "--disable-extensions", "--disable-background-networking", "--disable-sync",
        "--disable-component-update", "--disable-default-apps", "--no-first-run",
        "--no-default-browser-check", "--disable-features=msEdgeSidebar,msShoppingAssistant,msEdgeCollections,msWebCapture",
        "--disable-background-timer-throttling=false", "--disk-cache-size=52428800",
    ]


def cdp(path, timeout=2):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
        return json.load(r)


def alive():
    try:
        return cdp("/json/version")
    except Exception:
        return None


def pages():
    return [t for t in cdp("/json/list") if t.get("type") == "page"]


def main():
    comprobar_aislamiento()
    if alive() is None:
        if "--check" in sys.argv:
            print(f"CDP {PORT}: no responde"); return 1
        os.makedirs(perfil(), exist_ok=True)
        subprocess.Popen([EDGE, *flags(), project_url()], close_fds=True)
        for _ in range(30):
            time.sleep(1)
            if alive(): break
        else:
            print(f"CDP {PORT}: no arranco"); return 1
    v = alive()
    ps = pages()
    print(f"CDP {PORT} OK:", v.get("Browser"))
    for t in ps:
        print(" -", t["url"].split("?")[0], "|", t.get("title", "")[:60])
    return 0


if __name__ == "__main__":
    sys.exit(main())
