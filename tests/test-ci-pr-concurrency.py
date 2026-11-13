#!/usr/bin/env python3
"""Regression: la CI de una PR cancela la del commit anterior, nunca la de main ni la programada."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
missing, unsafe = [], []
for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    text = path.read_text(encoding="utf-8")
    if not re.search(r"^\s+pull_request(?:_target)?:", text, re.M):
        continue
    block = re.search(r"^concurrency:\n((?:[ \t]+.*\n|[ \t]*#.*\n)+)", text, re.M)
    if not block:
        missing.append(path.name)
        continue
    body = block.group(1)
    cancel = re.search(r"cancel-in-progress:\s*(.+)", body)
    cancel = cancel.group(1).strip() if cancel else "false"
    # Cancelar con un grupo global cortaría runs de otras ramas: debe ir por PR, por rama o por evento.
    scoped = any(k in body for k in ("pull_request", "github.ref", "workflow_run"))
    if cancel != "false" and not scoped:
        unsafe.append(path.name)
assert not missing, f"workflows de PR sin concurrency: {missing}"
assert not unsafe, f"cancel-in-progress sin limitarse a PR: {unsafe}"

atlas = (ROOT / ".github" / "workflows" / "atlas-directory-sync.yml").read_text(encoding="utf-8")
assert re.search(r"cron:\s*'0 0 \* \* 1'", atlas), "el sync del Atlas va a la 01:00 de Madrid"
# Bots y auditorías programadas, de madrugada (00:00-05:59 UTC = 01:00-07:00 en Madrid en invierno)
# para no ocupar runners mientras se trabaja. Excepciones con motivo: el radar cambia de fecha a
# medianoche, los libros publican también de día, Telegram lanza la tanda a las 11:30 de Madrid
# y el monitor vigila producción cada 6 h.
DAYTIME_OK = {"radar-clock-refresh.yml", "reading-catalogue-sync.yml", "reading-telegram-publish.yml", "production-smoke-monitor.yml",
             "npm-supply-chain-watch.yml"}
daytime = []
for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    if path.name in DAYTIME_OK:
        continue
    for hour in re.findall(r"cron:\s*'\S+\s+(\S+)", path.read_text(encoding="utf-8")):
        if not hour.isdigit() or int(hour) > 5:
            daytime.append(f"{path.name}:{hour}")
assert not daytime, f"crons fuera de la madrugada: {daytime}"
print("PASS CI concurrency por PR y crons de madrugada")
