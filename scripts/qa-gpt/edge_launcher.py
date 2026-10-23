#!/usr/bin/env python3
"""Lanza (o reutiliza) el Edge dedicado de QA-GPT: CDP solo en 127.0.0.1:9230.

Perfil propio y persistente fuera del repo. No toca los puertos 9224/9225 ni otros Edge.
Uso: python scripts/qa-gpt/edge_launcher.py [--check]
"""
import json, os, subprocess, sys, time, urllib.request

PORT = 9230
PROFILE = os.environ.get("QA_GPT_PROFILE", r"C:\Temp\web-escritor-qa-gpt-edge")
PROJECT_URL = "https://chatgpt.com/g/g-p-6adb128351e481919fef7901e111d1ac/project"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FLAGS = [
    f"--remote-debugging-port={PORT}", "--remote-debugging-address=127.0.0.1",
    f"--user-data-dir={PROFILE}", "--edge-skip-compat-layer-relaunch",
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
    if alive() is None:
        if "--check" in sys.argv:
            print("CDP 9230: no responde"); return 1
        os.makedirs(PROFILE, exist_ok=True)
        subprocess.Popen([EDGE, *FLAGS, PROJECT_URL], close_fds=True)
        for _ in range(30):
            time.sleep(1)
            if alive(): break
        else:
            print("CDP 9230: no arranco"); return 1
    v = alive()
    ps = pages()
    if not any("g-p-6adb128351e481919fef7901e111d1ac" in t["url"] for t in ps) and "--check" not in sys.argv:
        urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/json/new?{PROJECT_URL}", method="PUT"), timeout=5)
        ps = pages()
    print("CDP 9230 OK:", v.get("Browser"))
    for t in ps:
        u = t["url"].split("?")[0]
        print(" -", u, "|", t.get("title", "")[:60])
    return 0

if __name__ == "__main__":
    sys.exit(main())
