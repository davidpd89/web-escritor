"""ci_grupo: ejecuta en el runner los tests de un grupo QA GPT y escribe resultados.json (lo usa .github/workflows/qa-gpt-grupo.yml).

Uso: python ci_grupo.py <salida.json> <modo: regresion|exploratorio> <exe:ruta> [<exe:ruta> ...]
Los tests pueden pasarse como un unico argumento "exe:ruta exe:ruta" (asi los envia el workflow, sin expansion del shell).
Exit: 0 si todo dio un resultado fiable (en exploratorio, los hallazgos NO fallan el job);
      1 si algun test es invalido/infra/sin_entorno (un test que no pudo ejecutarse NUNCA cuenta como aprobado), o (modo regresion) algun test falla;
      2 si los argumentos no son validos (no se ejecuta nada). Los resultados se escriben SIEMPRE.
"""
import json, os, re, signal, socket, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_clases import clasificar_salida

TIMEOUT = int(os.environ.get("QA_TEST_TIMEOUT", "300"))
EXES = {"node", "python"}
RUTA_OK = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*\.(mjs|js|py)$")
POSIX = os.name == "posix"


def validar(t):
    """'exe:ruta' -> (exe, ruta) o None. Solo ejecutores admitidos y rutas relativas del repo (sin .., sin absolutas, sin simbolos del shell)."""
    exe, _, ruta = t.partition(":")
    if exe not in EXES or not RUTA_OK.match(ruta) or ".." in Path(ruta).parts: return None
    return exe, ruta


def matar(proc):
    """Termina el proceso y su grupo (Chromium y otros hijos); en Windows, el arbol con taskkill."""
    if proc.poll() is None:
        try:
            if POSIX: os.killpg(proc.pid, signal.SIGKILL)
            else: subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        except (ProcessLookupError, PermissionError, OSError): proc.kill()
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired: pass


def esperar_puerto(puerto, segundos=15):
    t0 = time.time()
    while time.time() - t0 < segundos:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", puerto)) == 0: return True
        time.sleep(0.2)
    return False


def puerto_libre(base=4273):
    for p in range(base, base + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0: return p


def entorno_url(texto, puerto):
    return {n: f"http://127.0.0.1:{puerto}" for n in set(re.findall(r"process\.env\.([A-Z][A-Z0-9_]*(?:URL|ORIGIN|BASE))", texto))}


def correr(exe, ruta):
    if not Path(ruta).is_file(): return 127, "can't open file " + ruta
    texto = Path(ruta).read_text(encoding="utf-8", errors="replace")
    env, srv, urls = dict(os.environ), None, entorno_url(texto, 0)
    # Servidor local si el test usa playwright o lee una URL base del entorno; las variables URL/ORIGIN/BASE se apuntan a ese servidor
    # (un test con URL fija la sirve el mismo servidor en la raiz del repo si coincide el puerto; si no, su propio resultado lo delata).
    if exe == "node" and ("playwright" in texto or urls):
        puerto = puerto_libre()
        if puerto is None: return 1, "EADDRINUSE: sin puerto libre para el servidor local"
        env.update(entorno_url(texto, puerto))
        srv = subprocess.Popen([sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=POSIX)
        if not esperar_puerto(puerto):
            matar(srv); return 1, "ETIMEDOUT: el servidor local no arranco; el test no se ejecuto"
    proc = None
    try:
        proc = subprocess.Popen(["node" if exe == "node" else sys.executable, ruta], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env, start_new_session=POSIX)
        try: out, _ = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            matar(proc); return 124, f"TimeoutExpired tras {TIMEOUT}s"
        return proc.returncode, out or ""
    finally:
        if proc: matar(proc)
        if srv: matar(srv)


def main(argv):
    salida, modo = Path(argv[1]), argv[2]
    tests = [x for a in argv[3:] for x in a.split()]
    pares = [validar(t) for t in tests]
    if modo not in ("regresion", "exploratorio") or not tests or None in pares:
        print("ARGUMENTOS_INVALIDOS", modo, [t for t, p in zip(tests, pares) if p is None], file=sys.stderr)
        salida.write_text(json.dumps({"modo": modo, "resumen": {"argumentos_invalidos": 1}, "tests": []}, ensure_ascii=False), encoding="utf-8")
        return 2
    res = []
    for exe, ruta in pares:
        t0 = time.time(); rc, out = correr(exe, ruta)
        res.append({"ruta": ruta, "exe": exe, "rc": rc, "clase": clasificar_salida(rc, out), "segundos": round(time.time() - t0, 1), "salida": out[-4000:]})
        print(f"{res[-1]['clase']:<10} rc={rc} {ruta} ({res[-1]['segundos']}s)", flush=True)
    resumen = {c: sum(1 for r in res if r["clase"] == c) for c in {r["clase"] for r in res}}
    salida.write_text(json.dumps({"modo": modo, "resumen": resumen, "tests": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("RESUMEN", json.dumps(resumen), flush=True)
    malo = resumen.get("invalido", 0) + resumen.get("infra", 0) + resumen.get("sin_entorno", 0) + (resumen.get("hallazgo", 0) if modo == "regresion" else 0)
    return 1 if malo else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
