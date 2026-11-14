"""Vigilante local de Telegram/Discord: red de seguridad independiente de los crons de GitHub.

GitHub programa los crons «a mejor esfuerzo» (el 12/11 el de las 11:30 arrancó a las 19:29).
Este script lo lanza el Programador de tareas de Windows a las 11:25 y a las 11:50 (hora local de
Madrid). Si el ciclo del día no está en marcha ni terminado con éxito tras las 11:30, lo lanza con
`gh workflow run`. Es seguro repetirlo: el ciclo espera a las 11:30 y el estado durable evita reenvíos.
No imprime secretos ni identificadores de chats.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, time as dtime

WORKFLOW = "reading-telegram-publish.yml"
REPO = "davidpd89/web-escritor"
SEND_AT = dtime(11, 30)
START_AFTER = dtime(11, 20)


def local(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone()


def cycle_done_or_running(runs: list[dict], now: datetime) -> bool:
    for run in runs:
        if run.get("status") in ("queued", "in_progress", "waiting", "pending"):
            if local(run["createdAt"]).date() == now.date():
                return True
        elif run.get("conclusion") == "success":
            end = local(run["updatedAt"])
            if end.date() == now.date() and end.time() >= SEND_AT:
                return True
    return False


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, timeout=45).stdout


def main() -> int:
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] inicio", flush=True)
    try:
        return run()
    except Exception as exc:  # el log debe decir por qué falló (14/11: terminó sin escribir nada)
        print(f"[{stamp}] ERROR: {type(exc).__name__}: {exc}", flush=True)
        return 1


def run() -> int:
    now = datetime.now().astimezone()
    if now.time() < START_AFTER:
        print("demasiado pronto")
        return 0
    runs = json.loads(gh("run", "list", "-R", REPO, "--workflow", WORKFLOW, "-L", "20", "--json", "status,conclusion,createdAt,updatedAt"))
    if cycle_done_or_running(runs, now):
        print("ok: ciclo de hoy en marcha o terminado")
        return 0
    gh("workflow", "run", "-R", REPO, WORKFLOW, "--ref", "main")
    print("lanzado: no había ciclo de hoy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
