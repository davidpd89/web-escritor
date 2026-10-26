"""Modelo de cobertura dinamico de qa-gpt: familias de rutas <-> tests <-> tecnicas, tecnicas descubribles y dedup conductual.

Todo se recalcula desde el repo (git ls-files) y se persiste en SQLite; nada esta fijado a una lista cerrada:
las tecnicas semilla viven en config.json y GPT puede anadir nuevas (tabla `tecnicas`, origen 'descubierta').
"""
import datetime as dt, hashlib, json, os, re, subprocess, sys, unicodedata
from pathlib import Path

NO_FAMILIA = {"tests", "qa", ".github", "node_modules", "pagefind", "docs", "migrations", "video-ios-test", "artifacts", "_reddit", "_tools", "WEB DAVID PORTO nuevas ideas"}
TRAZAS = {  # rasgo de una familia -> extensiones
    "html": {".html"}, "js": {".js", ".mjs"}, "css": {".css"}, "datos": {".json", ".ics", ".xml", ".csv", ".txt"},
    "generador": {".py"}, "media": {".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".mp4", ".pdf"},
}
GLOBAL_RE = re.compile(r"(rglob|glob\(|os\.walk|readdirSync|walk\(|\*\.html|\*\*/\*)")
STOP = set("para como este esta esos esas desde entre sobre cuando donde debe deben tiene tienen pero solo mismo todos todas test tests prueba".split())


# ---------- procesos externos: sin ventana de consola y sin esperas ocultas ----------
SIN_VENTANA = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: el servicio corre sin consola (pythonw) y cada git abria su propia ventana negra
_SIN_PROMPT = {"GIT_TERMINAL_PROMPT": "0", "GH_PROMPT_DISABLED": "1"}  # sin consola nadie vera un prompt de texto: que falle con error en vez de colgarse (el GCM grafico sigue saliendo)
# node_modules del pipeline, fuera de todo repo: con el junction de los worktrees a C:\GIT\web-escritor\node_modules, Claude siguio el enlace y
# edito el repo de trabajo de David (reparacion de main 2026-10-26: el arreglo quedo alli y en el worktree 'sin_cambios'). El de la web, solo de respaldo.
NODE_MODULES = next((p for p in (os.environ.get("QA_NODE_MODULES"), r"C:\GIT\qa-gpt-state\node_modules") if p and Path(p, "playwright").is_dir()),
                    r"C:\GIT\web-escritor\node_modules")
_GIT_QUIETO = ["-c", "gc.auto=0", "-c", "maintenance.auto=false"]  # fetch/merge no lanzan gc/maintenance en segundo plano (otra fuente de ventanas y de carga)


def _preparar(args, kw):
    kw.setdefault("creationflags", SIN_VENTANA)
    if "input" not in kw: kw.setdefault("stdin", subprocess.DEVNULL)
    exe = os.path.basename(str(args[0])).lower().removesuffix(".exe")
    if exe in ("git", "gh"): kw["env"] = {**(kw.get("env") or os.environ), **_SIN_PROMPT}
    if exe == "git" and "gc.auto=0" not in args: args = [args[0], *_GIT_QUIETO, *args[1:]]
    return args, kw


def run(args, **kw):
    """subprocess.run sin ventana; la salida y los errores NO se ocultan (el llamador decide con returncode/stderr)."""
    args, kw = _preparar(args, kw); return subprocess.run(args, **kw)


def popen(args, **kw):
    args, kw = _preparar(args, kw); return subprocess.Popen(args, **kw)


class ServidorEstatico:
    """Servidor estatico en un hilo del propio proceso (sustituye a `python -m http.server` hijo). En Windows un hijo sobrevive a su padre:
    si EJECUTAR moria o se cerraba la ventana, el `finally` no corria y quedaban http.server huerfanos para siempre (4 el 2026-10-25).
    Uso: `with ServidorEstatico(dir, puerto=0) as port:`; puerto 0 = uno libre."""
    def __init__(self, directorio, puerto=0): self.dir, self.puerto = str(directorio), puerto

    def __enter__(self):
        import functools, threading, http.server
        class Silencioso(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
        class Servidor(http.server.ThreadingHTTPServer):
            def handle_error(self, request, client_address):  # el navegador corta descargas al cerrar la pagina (WinError 10053): no es un fallo
                if not isinstance(sys.exc_info()[1], (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)): super().handle_error(request, client_address)
        self.srv = Servidor(("127.0.0.1", self.puerto), functools.partial(Silencioso, directory=self.dir))
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, name="servidor-estatico", daemon=True).start()
        return self.srv.server_address[1]

    def __exit__(self, *a): self.srv.shutdown(); self.srv.server_close()


# Lecturas de historial: se recuerdan por (HEAD, origin/main, dia). `git log/rev-list/ls-files` sobre la misma historia dan lo mismo,
# asi ESTADO y el servicio no relanzan decenas de procesos git por cada familia y modo.
_CACHE_DIR = Path(os.environ.get("QA_GPT_STATE", r"C:\GIT\qa-gpt-state"))
_LEIBLES = {"log", "rev-list", "ls-files"}
_mem, _cabezas = {}, {}


def olvidar_git():
    _mem.clear(); _cabezas.clear()


def _cabeza(root):
    k = str(root)
    if k not in _cabezas:
        r = run(["git", "rev-parse", "HEAD", "origin/main"], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        _cabezas[k] = "|".join(r.stdout.split()) if r.returncode == 0 else None
    return _cabezas[k]


def _git(root, *a):
    """Salida de `git <a>` (vacia si falla). Las lecturas de historial usan la cache en memoria y en disco."""
    cab = _cabeza(root) if a and a[0] in _LEIBLES else None
    if cab:
        vig = f"{dt.date.today()}|{cab}|{root}"; clave = f"{vig}|{a}"
        if clave in _mem: return _mem[clave]
        disco = _leer_disco(root, vig)
        if clave in disco: _mem[clave] = disco[clave]; return disco[clave]
    r = run(["git", *a], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout.strip()
    if cab and r.returncode == 0:
        _mem[clave] = out; _guardar_disco(root, vig)
    return out


def _fichero_cache(root): return _CACHE_DIR / f"gitcache-{hashlib.sha1(str(root).encode()).hexdigest()[:8]}.json"


def _leer_disco(root, vigencia):
    try:
        d = json.loads(_fichero_cache(root).read_text(encoding="utf-8"))
        return d["datos"] if d.get("vigencia") == vigencia else {}
    except Exception: return {}


def _guardar_disco(root, vigencia):
    try:
        datos = {k: v for k, v in _mem.items() if k.startswith(vigencia + "|")}
        f = _fichero_cache(root); tmp = f.with_suffix(f".{os.getpid()}.tmp"); _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps({"vigencia": vigencia, "datos": datos}), encoding="utf-8"); os.replace(tmp, f)
    except Exception: pass


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9_]{4,}", norm(s)) if w not in STOP}


def migrar(c):
    """Esquema ampliado (idempotente). `c` ya tiene las tablas base."""
    def cols(t): return {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
    def add(t, col, ddl):
        if col not in cols(t): c.execute(f"ALTER TABLE {t} ADD COLUMN {col} {ddl}")
    for col, ddl in (("chat_id", "TEXT"), ("fase", "TEXT"), ("respuesta", "TEXT"), ("modo", "TEXT")): add("jobs", col, ddl)
    for col, ddl in (("tecnica", "TEXT"), ("funcionalidad", "TEXT"), ("huella_conductual", "TEXT"), ("fuente_sha", "TEXT"), ("familias", "TEXT"), ("duplica", "INTEGER"), ("siguiente", "TEXT"), ("base_sha", "TEXT"), ("version_test", "TEXT")): add("propuestas", col, ddl)
    for col, ddl in (("base_sha", "TEXT"), ("comandos", "TEXT")): add("ramas", col, ddl)
    for col, ddl in (("chat_id", "TEXT"), ("herramientas", "INTEGER"), ("estado", "TEXT"), ("segundos", "INTEGER")): add("peticiones", col, ddl)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tecnicas(id TEXT PRIMARY KEY, nombre TEXT, kw TEXT, aplica TEXT, origen TEXT, creada TEXT, nota TEXT);
    CREATE TABLE IF NOT EXISTS cobertura(familia TEXT PRIMARY KEY, datos TEXT, head TEXT, actualizado TEXT);
    CREATE TABLE IF NOT EXISTS eventos(fecha TEXT, entidad TEXT, ident INTEGER, estado TEXT, nota TEXT);
    CREATE TABLE IF NOT EXISTS cruces(propuesta INTEGER, familia TEXT, tecnica TEXT, estado TEXT DEFAULT 'pendiente', UNIQUE(propuesta, familia));
    """)
    c.commit()


def sembrar_tecnicas(c, cfg, now):
    """Semilla = tipos + tecnicas_semilla de config; nunca borra las descubiertas."""
    for t in cfg["tipos"]:
        c.execute("INSERT OR IGNORE INTO tecnicas VALUES(?,?,?,?,?,?,?)", (t["id"], t["nombre"], json.dumps(t["kw"]), json.dumps(t.get("aplica", ["html", "js", "datos", "generador"])), "semilla", now, ""))
    for t in cfg.get("tecnicas_semilla", []):
        c.execute("INSERT OR IGNORE INTO tecnicas VALUES(?,?,?,?,?,?,?)", (t["id"], t["nombre"], json.dumps(t["kw"]), json.dumps(t.get("aplica", ["*"])), "semilla", now, ""))
    c.commit()


def registrar_tecnica(c, t, now, propuesta=None):
    """Registra una tecnica descubierta por GPT (id kebab-case). Devuelve True si es nueva."""
    tid = re.sub(r"[^a-z0-9]+", "-", norm(t.get("id") or t.get("nombre") or "")).strip("-")[:48]
    if not tid or c.execute("SELECT 1 FROM tecnicas WHERE id=?", (tid,)).fetchone(): return False
    kw = t.get("palabras_clave") or sorted(tokens(t.get("nombre", "")))[:5]
    c.execute("INSERT INTO tecnicas VALUES(?,?,?,?,?,?,?)", (tid, (t.get("nombre") or tid)[:160], json.dumps(kw), json.dumps(t.get("aplica") or ["*"]), "descubierta", now, f"propuesta {propuesta}" if propuesta else ""))
    c.commit(); return True


def tecnicas(c):
    out = []
    for r in c.execute("SELECT * FROM tecnicas"):
        try: out.append(dict(id=r["id"], nombre=r["nombre"], kw=[k.lower() for k in json.loads(r["kw"])], aplica=json.loads(r["aplica"]), origen=r["origen"]))
        except (ValueError, TypeError, AttributeError): continue  # una tecnica corrupta no impide usar las demas
    return out


def evento(c, entidad, ident, estado, nota, now):
    c.execute("INSERT INTO eventos VALUES(?,?,?,?,?)", (now, entidad, ident, estado, (nota or "")[:300]))


# ---------- inventario ----------
def familias_de(root):
    out = {}
    for p in _git(root, "ls-files").splitlines():
        p = p.strip('"')
        top = p.split("/")[0] if "/" in p else "(raiz)"
        if top in NO_FAMILIA or top.startswith("."): continue
        out.setdefault(top, []).append(p)
    return out


def rasgos(files):
    exts = {Path(f).suffix.lower() for f in files}
    return sorted(r for r, e in TRAZAS.items() if exts & e)


def aplica(t, rs):
    return "*" in t["aplica"] or bool(set(t["aplica"]) & set(rs))


def construir(c, root, cfg, now, forzar=False):
    """Recalcula la matriz si cambio HEAD (o forzar). Devuelve {familia: datos}."""
    head = _git(root, "rev-parse", "--short", "HEAD")
    filas = c.execute("SELECT * FROM cobertura").fetchall()
    if not forzar and filas and all(r["head"] == head for r in filas):  # filas de otro HEAD o corruptas: se reconstruye
        try: return {r["familia"]: json.loads(r["datos"]) for r in filas}
        except (ValueError, TypeError): pass
    fams, tecs = familias_de(root), tecnicas(c)
    pool = [p for p in _git(root, "ls-files", "tests", "qa", ".github/workflows").splitlines() if not p.endswith((".png", ".jpg", ".json.snap"))]
    info = {}
    for p in pool:
        try: txt = (root / p).read_text(encoding="utf-8", errors="replace")[:60000]
        except OSError: continue
        base = norm(Path(p).name + " " + txt[:20000])
        info[p] = (txt, {t["id"] for t in tecs if any(k in base for k in t["kw"])}, bool(GLOBAL_RE.search(txt)))
    areas = {a["id"]: a for a in cfg["areas"]}
    out = {}
    for fam, files in fams.items():
        rs = rasgos(files); pref = fam + "/"
        refs = [p for p, (txt, _, g) in info.items() if (pref in txt) or (fam == "(raiz)" and "index.html" in txt)]
        glob_t = [p for p, (_, _, g) in info.items() if g and p not in refs]
        cubiertas = {tid for p in refs for tid in info[p][1]}
        cub_glob = {tid for p in glob_t for tid in info[p][1]}
        apl = [t["id"] for t in tecs if aplica(t, rs)]
        huecos = [tid for tid in apl if tid not in cubiertas and tid not in cub_glob]
        parcial = [tid for tid in apl if tid not in cubiertas and tid in cub_glob]
        sha = _git(root, "log", "-1", "--format=%h", "--", fam if fam != "(raiz)" else ":(top,glob)*.html") or ""
        com = _git(root, "rev-list", "--count", "--since=14 days ago", "HEAD", "--", fam if fam != "(raiz)" else ":(top,glob)*.html") or "0"
        com = com.strip() if com.strip().isdigit() else "0"  # solo es una metrica: una salida rara no para el planificador
        riesgo = max((a["riesgo"] for a in areas.values() if any(fam in f.split("/")[0] or f.startswith(fam) for f in a["fuentes"])), default=2)
        out[fam] = dict(familia=fam, ficheros=len(files), rasgos=rs, tests_propios=len(refs), tests_globales=len(glob_t), tecnicas_cubiertas=sorted(cubiertas),
                        tecnicas_parcial=parcial, tecnicas_aplicables=apl, huecos=huecos, sha=sha, commits14d=int(com or 0), riesgo=riesgo, ejemplos_tests=refs[:6])
    c.execute("DELETE FROM cobertura")
    for fam, d in out.items(): c.execute("INSERT INTO cobertura VALUES(?,?,?,?)", (fam, json.dumps(d, ensure_ascii=False), head, now))
    c.commit(); return out


# ---------- deduplicacion conductual ----------
def sha_fuentes(root, rutas):
    ex = [r for r in rutas if r and (root / r).exists()]
    return _git(root, "log", "-1", "--format=%h", "--", *ex) if ex else ""


def datos_prop(pr):
    fuentes = sorted({f.get("ruta", "") for f in pr.get("ficheros_fuente", []) if isinstance(f, dict) and f.get("ruta")})
    tec = (pr.get("tecnica") or {}); tec = tec.get("id") if isinstance(tec, dict) else str(tec or "")
    tec = re.sub(r"[^a-z0-9]+", "-", norm(tec)).strip("-") or "sin-tecnica"
    func = pr.get("funcionalidad") or pr.get("comportamiento") or pr.get("titulo", "")
    inv = pr.get("invariante") or pr.get("resultado_esperado") or ""
    toks = tokens(func + " " + inv)
    huella = hashlib.sha1(("|".join(sorted(toks)[:40]) + "#" + tec + "#" + ",".join(fuentes)).encode()).hexdigest()[:16]
    return dict(fuentes=fuentes, tecnica=tec, funcionalidad=func[:300], toks=toks, huella=huella)


def buscar_duplicado(c, root, pr):
    """-> (fila_previa, motivo) o (None, None). Rechazadas/invalidas se reabren SOLO si las fuentes cambiaron desde entonces."""
    d = datos_prop(pr)
    for r in c.execute("SELECT * FROM propuestas WHERE huella_conductual IS NOT NULL ORDER BY id"):
        try: prev = json.loads(r["datos"]); pd = datos_prop(prev)
        except (ValueError, TypeError, AttributeError): continue  # propuesta historica corrupta: no bloquea la deduplicacion
        exacta = r["huella_conductual"] == d["huella"]
        sol = set(pd["fuentes"]) & set(d["fuentes"])
        jac = len(pd["toks"] & d["toks"]) / max(1, len(pd["toks"] | d["toks"]))
        if not (exacta or (pd["tecnica"] == d["tecnica"] and (sol or not d["fuentes"]) and jac >= 0.55)): continue
        if r["estado"] in ("rechazada", "invalida") and r["fuente_sha"] and sha_fuentes(root, pd["fuentes"]) != r["fuente_sha"]:
            continue  # el codigo cambio: se puede volver a mirar
        return r, f"{'huella igual' if exacta else f'similitud {jac:.2f}'} con #{r['id']} [{r['estado']}]"
    return None, None


# ---------- como_ejecutar: de texto libre de GPT a pasos validados ----------
_ENV = re.compile(r"\b([A-Z][A-Z0-9_]{2,40})=(https?://(?:127\.0\.0\.1|localhost):\d{2,5}/?|[\w.:/-]{1,80})(?=\s)")
_TEST_EXT = {".py": "python", ".mjs": "node", ".js": "node"}


def normalizar_comandos(pr):
    """Devuelve la lista de pasos ejecutables de una propuesta y fija `como_ejecutar` en su forma canonica.

    GPT escribe `como_ejecutar` como texto libre (comandos encadenados con `&&`, prosa de preparacion, variables de entorno).
    Nada de ese texto se ejecuta: solo se extrae, por cada fichero de test nuevo, una invocacion `python|node <ruta>` cuya
    ruta DEBE estar declarada en `ficheros_nuevos`, mas variables de entorno de forma estricta (clave en mayusculas, valor
    sin metacaracteres; URLs solo a localhost). Los prechequeos (`py_compile`, `--check`) se descartan: la sintaxis ya
    se verifica sobre los bytes guardados. Si no hay comando reconocible se deriva de la extension del fichero.
    """
    raw = str(pr.get("como_ejecutar") or "")
    tests = [f["ruta"] for f in pr.get("ficheros_nuevos") or [] if isinstance(f, dict) and Path(f.get("ruta", "")).suffix in _TEST_EXT]
    env = {}
    for m in _ENV.finditer(raw + " "):
        env[m.group(1)] = m.group(2)
    pasos = []
    for ruta in tests:
        exe = _TEST_EXT[Path(ruta).suffix]
        # `python -m py_compile ruta`, `node --check ruta` y similares NO cuentan como ejecucion del test
        ejecutado = re.search(rf"(?<![\w-])(?:python3?|node)\s+{re.escape(ruta)}(?=[\s;&|,.]|$)", raw)
        pasos.append({"argv": [exe, ruta], "env": env if ejecutado else {}, "origen": "texto" if ejecutado else "extension"})
    pr["como_ejecutar_original"] = raw
    pr["pasos"] = pasos
    if len(pasos) == 1: pr["como_ejecutar"] = " ".join([f"{k}={v}" for k, v in pasos[0]["env"].items()] + pasos[0]["argv"])
    return pasos
