"""ci_grupo: ejecuta en el runner los tests de un grupo QA GPT y escribe resultados.json (lo usa .github/workflows/qa-gpt-grupo.yml).

Uso: python ci_grupo.py <salida.json> <modo: regresion|exploratorio> <exe:ruta> [<exe:ruta> ...]
Exit: 0 si todo dio un resultado fiable (en exploratorio, los hallazgos NO fallan el job);
      1 si algun test es invalido/infra, o (modo regresion) algun test falla. Los resultados se escriben SIEMPRE.
"""
import json, os, re, socket, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_clases import clasificar_salida

TIMEOUT = int(os.environ.get("QA_TEST_TIMEOUT", "300"))


def puerto_libre(base=4273):
    for p in range(base, base + 40):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0: return p


def entorno_url(texto, puerto):
    return {n: f"http://127.0.0.1:{puerto}" for n in set(re.findall(r"process\.env\.([A-Z][A-Z0-9_]*(?:URL|ORIGIN|BASE))", texto))}


def correr(exe, ruta):
    if not Path(ruta).exists(): return 127, "can't open file " + ruta
    texto = Path(ruta).read_text(encoding="utf-8", errors="replace")
    env, srv = dict(os.environ), None
    if exe == "node" and "playwright" in texto:
        puerto = puerto_libre(); env.update(entorno_url(texto, puerto))
        srv = subprocess.Popen([sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.5)
    try:
        r = subprocess.run(["node" if exe == "node" else sys.executable, ruta], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, env=env)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired: return 124, f"TimeoutExpired tras {TIMEOUT}s"
    finally:
        if srv: srv.terminate()


def main(argv):
    salida, modo, tests = Path(argv[1]), argv[2], argv[3:]
    res = []
    for t in tests:
        exe, _, ruta = t.partition(":"); t0 = time.time(); rc, out = correr(exe, ruta)
        res.append({"ruta": ruta, "exe": exe, "rc": rc, "clase": clasificar_salida(rc, out), "segundos": round(time.time() - t0, 1), "salida": out[-4000:]})
        print(f"{res[-1]['clase']:<10} rc={rc} {ruta} ({res[-1]['segundos']}s)", flush=True)
    resumen = {c: sum(1 for r in res if r["clase"] == c) for c in {r["clase"] for r in res}}
    salida.write_text(json.dumps({"modo": modo, "resumen": resumen, "tests": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("RESUMEN", json.dumps(resumen), flush=True)
    malo = resumen.get("invalido", 0) + resumen.get("infra", 0) + (resumen.get("hallazgo", 0) if modo == "regresion" else 0)
    return 1 if malo else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
