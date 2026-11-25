#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=json.loads((ROOT/"convocatorias-escritores"/"opportunities.json").read_text(encoding="utf-8"))
CHECKER=ROOT/"scripts"/"check-radar-clock-current.py"
generated_for=date.fromisoformat(PUBLIC["generated_for"])

current=subprocess.run([sys.executable,str(CHECKER),"--today",generated_for.isoformat()],cwd=ROOT,text=True,capture_output=True)
assert current.returncode==0,current.stdout+current.stderr

deadlines=sorted(date.fromisoformat(item["deadline"]) for item in PUBLIC.get("items",[]) if item.get("deadline"))
if not deadlines:
    # Radar vacio (todo caducado o sin reverificar): no hay plazo que pueda caducar,
    # asi que no hay deriva que provocar. El vacio es contenido, no un fallo de reloj.
    print(f"SKIP radar clock-current regression: no active items on {generated_for}")
    sys.exit(0)
probe=deadlines[0]+timedelta(days=1)
future=subprocess.run([sys.executable,str(CHECKER),"--today",probe.isoformat()],cwd=ROOT,text=True,capture_output=True)
assert future.returncode==1,(
    "clock checker failed to detect expiration after earliest committed deadline "
    f"{deadlines[0]} on {probe}:\n{future.stdout}{future.stderr}"
)
assert "REFRESH REQUIRED" in (future.stdout+future.stderr)
print(f"PASS radar clock-current regression: committed clock {generated_for}; {probe} requires refresh")

# Gracia de PR (16/11, 24/11): sin --today, datos generados hasta GRACIA_DIAS días atrás siguen siendo válidos
# (un plazo que vence a medianoche tumbó dos cargas nocturnas el 24/11); con RELOJ_ESTRICTO=1 exige solo hoy.
import importlib.util, os
spec=importlib.util.spec_from_file_location("checker",CHECKER)
checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
def run(today, estricto):
    checker.clock_window=lambda now=None: [today] if estricto else [today-timedelta(days=n) for n in range(3)]
    sys.argv=["check"]
    return checker.main()
sys.stdout=sys.stderr=open(os.devnull,"w")
try:
    aviso=run(probe,False)       # probe = día tras el primer plazo: los datos de generated_for aún valen por gracia
    estricto=run(probe,True)
    lejos=run(probe+timedelta(days=5),False)
finally:
    sys.stdout,sys.stderr=sys.__stdout__,sys.__stderr__
assert aviso==0 or generated_for<probe-timedelta(days=2),"la gracia debe aceptar datos de hasta 2 días"
assert estricto==1,"con reloj estricto, un plazo vencido exige refresco"
assert lejos==1,"pasada la gracia exige refresco"
print("PASS radar clock-current grace window")

# De extremo a extremo (CATALOGO_HOY fija el día del sitio): lo generado hoy sigue sirviendo a la puerta de las PR los
# dos días siguientes (un plazo que vence a medianoche no tumba cargas) y deja de servir al tercero.
def en_dia(dia, estricto=False):
    env={**os.environ,"CATALOGO_HOY":dia.isoformat(),"RELOJ_ESTRICTO":"1" if estricto else "0"}
    return subprocess.run([sys.executable,str(CHECKER)],cwd=ROOT,text=True,capture_output=True,env=env).returncode
# La puerta compara por contenido: lo generado vale en cualquier día D cuya ventana (D, D-1, D-2) contenga un día con el
# mismo radar activo. Lo generado hoy sirve los dos días siguientes siempre; deja de servir al tercero solo si el
# radar cambia al día siguiente de generarse, es decir, si un plazo vence justo ese día (deadline == generated_for).
# Con el primer plazo más lejos (el 25/11 era el 27/11) el contenido no cambia y sigue valiendo: no es un fallo.
assert en_dia(generated_for)==0
assert en_dia(generated_for+timedelta(days=1))==0 and en_dia(generated_for+timedelta(days=2))==0,"la gracia de 2 días debe valer en la puerta"
if deadlines[0]<=generated_for:
    assert en_dia(generated_for+timedelta(days=3))==1,"pasada la gracia exige refresco"
print("PASS radar clock-current grace end to end")
