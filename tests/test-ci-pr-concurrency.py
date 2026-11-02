#!/usr/bin/env python3
"""Regression: la CI de una PR cancela la del commit anterior, nunca la de main ni la programada."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
missing, unsafe = [], []
for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    triggers = data.get("on", data.get(True)) or {}
    if "pull_request" not in triggers:
        continue
    concurrency = data.get("concurrency")
    if not concurrency:
        missing.append(path.name)
        continue
    cancel = str(concurrency.get("cancel-in-progress", False)) if isinstance(concurrency, dict) else "False"
    group = concurrency.get("group", "") if isinstance(concurrency, dict) else str(concurrency)
    # Cancelar con un grupo global cortaría runs de otras ramas: debe ir por PR, por rama o por evento.
    scoped = any(k in cancel + group for k in ("pull_request", "github.ref", "workflow_run"))
    if cancel not in ("False", "false") and not scoped:
        unsafe.append(path.name)
assert not missing, f"workflows de PR sin concurrency: {missing}"
assert not unsafe, f"cancel-in-progress sin limitarse a PR: {unsafe}"

atlas = (ROOT / ".github" / "workflows" / "atlas-directory-sync.yml").read_text(encoding="utf-8")
assert re.search(r"cron:\s*'0 0 \* \* 1'", atlas), "el sync del Atlas va a la 01:00 de Madrid"
print("PASS CI concurrency por PR y sync nocturno del Atlas")
