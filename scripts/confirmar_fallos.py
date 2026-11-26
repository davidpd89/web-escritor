#!/usr/bin/env python3
"""Repite una vez, sobre la misma revisión, los ficheros de contratos que fallaron en la puerta.

`FALLA: tests/...` es lo que lee publish-radar-refresh.py (fallo_determinista) para no reintentar la puerta entera y
lo que anota el libro de la noche para no repetir la carga con el mismo código. Bastaba un fallo suelto (un timeout,
un runner lento, una carrera entre los 4 procesos en paralelo) para marcar como determinista lo que no lo era y
parar la carga sin reintento (caso 12 de la revisión GPT, 25/11). Ahora solo es FALLA lo que falla dos veces seguidas
sobre la misma revisión; lo que pasa a la segunda sale como INESTABLE (aviso de Actions) y no tumba el paso.

  python scripts/confirmar_fallos.py --modo script   LISTA   # python tests/test-x.py
  python scripts/confirmar_fallos.py --modo unittest LISTA   # python -m unittest discover -s tests -p test_x.py
  python scripts/confirmar_fallos.py --modo node     LISTA   # node tests/x.mjs

LISTA es un fichero con un test por línea (el `$logs/failed` del paso). Sale 1 si alguno falla dos veces.
"""
import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

TIEMPO_S = 900  # un fichero colgado no se come el job: cuenta como fallo repetido


def orden(modo, fichero):
    if modo == 'script':
        return [sys.executable, fichero]
    if modo == 'unittest':
        return [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', Path(fichero).name]
    if modo == 'node':
        return ['node', fichero]
    raise ValueError(modo)


def pasa(modo, rc):
    # rc 5 = NO TESTS RAN (Python >= 3.12): contratos que se ejecutan al importar, igual que en la puerta.
    return rc == 0 or (modo == 'unittest' and rc == 5)


def matar_arbol(pid):
    """El proceso y sus descendientes (servidores, navegadores que lanzó el contrato), como night-autorepair.py."""
    if os.name == 'nt':
        taskkill = str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'taskkill.exe')
        subprocess.run([taskkill, '/T', '/F', '/PID', str(pid)], capture_output=True, check=False)
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass   # el grupo ya terminó


def ejecutar(cmd):
    # subprocess.run(timeout=) mata solo al hijo directo: un contrato colgado dejaba vivos a sus nietos (un servidor
    # en un puerto, un navegador) para los contratos siguientes del mismo job (R3-10 GPT, 25/11). En su propio
    # grupo de procesos, al vencer el plazo cae el árbol entero.
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True,
                         encoding='utf-8', errors='replace', start_new_session=os.name != 'nt')
    try:
        salida, _ = p.communicate(timeout=TIEMPO_S)
        return p.returncode, salida
    except subprocess.TimeoutExpired as exc:
        matar_arbol(p.pid)
        try:
            resto, _ = p.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            resto = ''   # un nieto fuera del grupo sigue con la tubería: se abandona, no se espera
        return 124, f'sin terminar en {TIEMPO_S}s\n{resto or exc.output or ""}'


def confirmar(modo, ficheros, ejecutar=ejecutar, imprimir=print):
    """Devuelve (fallan, inestables). Imprime `FALLA: f` solo para los que fallan también a la segunda."""
    fallan, inestables = [], []
    for f in dict.fromkeys(x.strip() for x in ficheros if x.strip()):
        rc, salida = ejecutar(orden(modo, f))
        if pasa(modo, rc):
            inestables.append(f)
            imprimir(f'::warning title=Contrato inestable::{f} falló y pasó al repetirlo sobre la misma revisión')
            imprimir(f'INESTABLE: {f}')
        else:
            fallan.append(f)
            imprimir(f'::group::{f} (repetido)\n{salida}\n::endgroup::')
    for f in fallan:
        imprimir(f'FALLA: {f}')
    return fallan, inestables


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--modo', choices=('script', 'unittest', 'node'), required=True)
    ap.add_argument('lista', type=Path)
    args = ap.parse_args(argv)
    if not args.lista.exists():
        return 0
    fallan, _ = confirmar(args.modo, args.lista.read_text(encoding='utf-8').splitlines())
    return 1 if fallan else 0


if __name__ == '__main__':
    sys.exit(main())
