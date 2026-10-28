"""supervisor: mantiene vivo el servicio de INICIAR (y, opcionalmente, EJECUTAR) y lo relanza si cae. Equivalente reducido de qa_supervisor.py.

PROCEDENCIA: scripts/qa-gpt/qa_supervisor.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0 (blob 13222b998e8bbfb590716b0cfd9621a55dbfdc63): el patron de
"ejecutar el proceso hijo, relanzarlo si cae con REINICIO=75, firma estable de traceback y limite de reparaciones por hora".
NO se copia la reparacion automatica por Claude (modificaba el codigo vivo con fast-forward y abria PR de main en rojo): en el laboratorio una caida
se registra con su traceback en supervisor.log y se relanza con espera creciente; tras `max_caidas_hora` caidas se detiene y lo dice en ESTADO.
Uso: python supervisor.py servicio | ejecutar-actions [--continuo]
"""
import os, re, subprocess, sys, time
from pathlib import Path

import mw


def firma(texto):
    """Firma estable de un traceback: excepcion + ultimo fichero:funcion propio (sin numeros de linea). Literal de qa_supervisor.firma."""
    marcos = re.findall(r'File "([^"]+)", line \d+, in (\w+)', texto)
    propios = [f"{Path(f).name}:{fn}" for f, fn in marcos if "Python3" not in f and "Lib" not in Path(f).parts] or [f"{Path(f).name}:{fn}" for f, fn in marcos[-1:]]
    exc = (re.findall(r"^(\w+(?:Error|Exception|Interrupt)\w*)\b", texto, re.M) or ["?"])[-1]
    return f"{exc}@{propios[-1] if propios else '?'}"


def hijo(modo, resto):
    base = [sys.executable, str(mw.HERE / "mw.py")]
    return base + ({"servicio": ["servicio"], "ejecutar-actions": ["ejecutar-actions", *resto]}[modo])


def supervisar(modo, resto=(), popen=None, sleep=time.sleep, reloj=time.time, maxi_caidas=None):
    """-> codigo final. `popen`/`sleep`/`reloj` inyectables (pruebas)."""
    # servicio: sin consola, a servicio.log. ejecutar-actions: CON la consola del .bat (se ve el panel y la tecla Q llega al hijo): sin CREATE_NO_WINDOW
    segundo_plano = bool(os.environ.get("MEJORAS_WEB_SEGUNDO_PLANO"))
    def _real(args):
        if modo == "servicio" or segundo_plano:  # sin consola: la salida a fichero (con un handle invalido el hijo moria al arrancar)
            log = mw.STATE / ("servicio.log" if modo == "servicio" else "actions/ejecutar_bg.log"); log.parent.mkdir(parents=True, exist_ok=True)
            return subprocess.Popen(args, cwd=str(mw.STATE), stdin=subprocess.DEVNULL, stdout=open(log, "a", encoding="utf-8", buffering=1), stderr=subprocess.STDOUT, creationflags=mw.SIN_VENTANA)
        return subprocess.Popen(args, cwd=str(mw.STATE), creationflags=0)
    popen = popen or _real
    maxi = maxi_caidas or mw.CFG.get("max_caidas_hora", 6)
    caidas, espera = [], 15
    mw.STATE.mkdir(parents=True, exist_ok=True)
    parada = "stop" if modo == "servicio" else "stop_actions"
    with mw.Lock("supervisor" if modo == "servicio" else "supervisor_actions", max_min=10**9):
        while not mw.flag(parada):
            p = popen(hijo(modo, list(resto)))
            while True:
                try: rc = p.wait(); break
                except KeyboardInterrupt: continue  # Ctrl+C llega tambien al hijo, que se detiene solo y guarda estado; el supervisor espera a que termine
            if rc == 0 or mw.flag(parada): return 0
            if rc in (mw.RC_CONFIG, mw.RC_EN_MARCHA): return rc  # configuracion invalida / ya hay otra instancia: reintentar no sirve
            if rc != mw.REINICIO:
                caidas = [t for t in caidas if reloj() - t < 3600] + [reloj()]
                with open(mw.STATE / "supervisor.log", "a", encoding="utf-8") as f: f.write(f"{mw.now()} {modo} termino con codigo {rc} (caida {len(caidas)}/{maxi} en la ultima hora)\n")
                mw.marcar(ultimo_error=f"{mw.now()} el proceso cayo (codigo {rc}); relanzado por el supervisor")
                if len(caidas) >= maxi:
                    mw.marcar(estado="detenido_por_caidas", parado=mw.now())
                    print(f"{maxi} caidas en una hora: el supervisor se detiene. Mira supervisor.log y servicio.log."); return 1
                sleep(espera); espera = min(600, espera * 2)
            else: espera = 15
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("servicio", "ejecutar-actions"): print(__doc__); return 2
    return supervisar(argv[0], argv[1:])


if __name__ == "__main__":
    sys.exit(main())
