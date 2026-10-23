"""qa_lote: lote de validacion con UN clic (EJECUTAR-ACTIONS-QA-GPT.bat).

Reutiliza el estado de qa_gpt (tablas propuestas/ramas) y el congelado de lote; anade lote_items (una fila por rama@sha), idempotente y reanudable.
Flujo por item: preparada -> validacion_local -> local_ok | fallo_test | defecto_demostrado | infra | revision_humana
                -> enviado -> actions_pendiente -> actions_ejecutando -> actions_ok | actions_fallida | defecto_demostrado | infra.
Nunca toca main, nunca abre/fusiona PRs: empuja SOLO la rama gpt-qa/* (sha exacto) y lanza el workflow que ejecuta el test (workflow_dispatch).
`q` = modulo qa_gpt (inyectado); `gh` y `runner` se sustituyen en las pruebas.
"""
import datetime as dt, fnmatch, json, os, re, socket, subprocess, sys, time
from pathlib import Path
import qa_cobertura as cob

ESTADOS_FINALES = {"fallo_test", "defecto_demostrado", "actions_ok", "actions_fallida", "revision_humana", "local_ok_sin_actions"}
REINTENTABLES = {"infra"}
INFRA = re.compile(r"ECONNRESET|ETIMEDOUT|ENOTFOUND|EADDRINUSE|rate limit|\b50[234]\b|\b429\b|Could not resolve host|runner.*lost|npm ERR! network|socket hang up|Timeout .*exceeded.*launch|TimeoutExpired", re.I)
SIN_ENTORNO = re.compile(r"Cannot find package '(playwright|@playwright)|Executable doesn't exist|browserType\.launch.*(not found|doesn't exist)", re.I)
ASERCION = re.compile(r"AssertionError|ERR_ASSERTION|^FAIL:|^FAILED \(failures", re.M)


def migrar(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS lotes(id INTEGER PRIMARY KEY, inicio TEXT, fin TEXT, estado TEXT, resumen TEXT);
    CREATE TABLE IF NOT EXISTS lote_items(clave TEXT PRIMARY KEY, lote_id INTEGER, rama TEXT, sha TEXT, area TEXT, propuestas TEXT, estado TEXT,
      detalle TEXT, local_exit INTEGER, local_clase TEXT, local_log TEXT, main_sha TEXT, workflows TEXT, runs TEXT, intentos INTEGER DEFAULT 0, creado TEXT, actualizado TEXT);
    CREATE TABLE IF NOT EXISTS lote_hist(clave TEXT, fecha TEXT, estado TEXT, detalle TEXT);
    """)


class Gh:
    """Fachada de `gh`/git remoto; todo fallo de red/API sale como GhError (transitorio)."""
    def __init__(self, q): self.q = q; self.repo = q.CFG["repo"]
    def _gh(self, *a):
        r = subprocess.run(["gh", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode:
            msg = (r.stderr or r.stdout).strip()[:300]
            raise (GhAuthError if re.search(r"HTTP 40[13]|Bad credentials|auth login|not logged|Resource not accessible|must have admin|requires.*scope", msg, re.I) else GhError)(msg)
        return r.stdout
    def ok(self): self._gh("api", "user", "--jq", ".login"); return True
    def scopes(self):
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        m = re.search(r"Token scopes:\s*(.+)", r.stdout + r.stderr); return set(re.findall(r"[\w:]+", m.group(1))) if m else set()
    def remote_sha(self, rama):
        r = subprocess.run(["git", "ls-remote", "origin", f"refs/heads/{rama}"], cwd=self.q.ROOT, capture_output=True, text=True, timeout=120)
        if r.returncode: raise GhError(r.stderr.strip()[:300])
        return r.stdout.split()[0] if r.stdout.strip() else None
    def push(self, sha, rama):
        r = subprocess.run(["git", "push", "origin", f"{sha}:refs/heads/{rama}"], cwd=self.q.ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode: raise GhError((r.stderr or r.stdout).strip()[:400])
    def runs(self, wf, rama):
        return json.loads(self._gh("run", "list", "-R", self.repo, "--workflow", wf, "--branch", rama, "--limit", "30",
                                   "--json", "databaseId,headSha,status,conclusion,event,createdAt,url") or "[]")
    def run(self, rid):
        return json.loads(self._gh("run", "view", str(rid), "-R", self.repo, "--json", "databaseId,status,conclusion,headSha,url"))
    def dispatch(self, wf, rama): self._gh("workflow", "run", wf, "-R", self.repo, "--ref", rama)
    def log_failed(self, rid):
        try: return self._gh("run", "view", str(rid), "-R", self.repo, "--log-failed")
        except GhError as e: return str(e)


class GhError(RuntimeError): pass
class GhAuthError(GhError): """Token sin sesion o sin permisos: no es transitorio, reintentar no sirve."""


def run_cmd(args, cwd, env=None, timeout=300):
    """Ejecuta un comando local; devuelve (rc, salida)."""
    try:
        r = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        return 124, f"TimeoutExpired tras {timeout}s\n{(e.stdout or '')[-1500:] if isinstance(e.stdout, str) else ''}"


def glob_concreto(patron, ruta):
    """Un glob de un paso `run:` ejecuta `ruta` solo si es especifico: extension literal y algo de literal alrededor del `*`.
    Un `*` suelto (o `*.mjs`) casa con todo y daria por cableado un test que ningun paso ejecuta."""
    m = re.fullmatch(r"([\w./-]*)\*([\w.*-]*)\.(\w+)", patron)
    if not m: return False
    literal = re.sub(r"[*/.]", "", m.group(1) + m.group(2))
    if len(literal) < 3 or Path(ruta).suffix != "." + m.group(3): return False
    return fnmatch.fnmatch(ruta, patron) if "/" in patron else fnmatch.fnmatch(Path(ruta).name, patron)


def workflows_que_ejecutan(rutas, textos, preferidos=()):
    """Workflows (con workflow_dispatch) cuyos pasos `run:` ejecutan TODAS las rutas. Las listas `paths:` y los comentarios no cuentan:
    que un cambio dispare el workflow no significa que el workflow ejecute el test (GitHub devolveria verde sin probarlo)."""
    res = {}
    for nombre, txt in textos.items():
        cuerpo = chr(10).join(l for l in txt.splitlines() if not re.match(r"\s*-\s*['\"]", l) and not l.strip().startswith("#"))
        toks = re.findall(r"[\w./*\-\[\]?]+", cuerpo)
        ejecuta = lambda r: r in cuerpo or any(glob_concreto(t, r) for t in toks if "*" in t)
        if rutas and all(ejecuta(r) for r in rutas) and re.search(r"^\s*workflow_dispatch", txt, re.M): res[nombre] = True
    return sorted(res, key=lambda w: (w not in preferidos, w))[:1]  # un solo workflow por test: el que GPT indico si realmente lo ejecuta


class Lote:
    def __init__(self, q, gh=None, runner=run_cmd, sleep=time.sleep, out=print, cfg=None):
        self.q, self.gh, self.runner, self.sleep, self.out = q, gh or Gh(q), runner, sleep, out
        self.cfg = {"concurrencia": 2, "max_horas": 8, "poll_s": 30, "timeout_test_s": 300, "reintentos_infra": 3, "puerto_estatico": 4173,
                    "node_modules": r"C:\GIT\web-escritor\node_modules", "actions_siempre": False, **q.CFG.get("lote", {}), **(cfg or {})}
        self.dir = q.STATE / "lote"; self.dir.mkdir(parents=True, exist_ok=True)
        self.c = q.db()

    # ---------- persistencia ----------
    def git(self, *a, check=True): return self.q.git(*a, cwd=self.q.ROOT, check=check)  # ROOT en tiempo de llamada (las pruebas lo redirigen)

    @staticmethod
    def slug(clave): return re.sub(r"\W", "_", clave)

    def log(self, msg): self.out(f"[{dt.datetime.now():%H:%M:%S}] {msg}")

    def set(self, clave, estado, detalle=None, **extra):
        cols = {"estado": estado, "actualizado": self.q.now(), **extra}
        if detalle is not None: cols["detalle"] = detalle[:600]
        self.c.execute(f"UPDATE lote_items SET {','.join(k + '=?' for k in cols)} WHERE clave=?", (*cols.values(), clave))
        self.c.execute("INSERT INTO lote_hist VALUES(?,?,?,?)", (clave, self.q.now(), estado, (detalle or "")[:300])); self.c.commit()
        self.log(f"{clave.split('@')[0].replace('gpt-qa/', '')}: {estado}" + (f" - {detalle[:140]}" if detalle else ""))

    def item(self, clave): return self.c.execute("SELECT * FROM lote_items WHERE clave=?", (clave,)).fetchone()
    def items(self, lote_id): return self.c.execute("SELECT * FROM lote_items WHERE lote_id=? ORDER BY rama", (lote_id,)).fetchall()

    # ---------- lote: captura congelada ----------
    def abrir_lote(self):
        """Reanuda un lote abierto (BAT cerrado a medias) o congela uno nuevo con lo preparado AHORA. Lo generado despues queda para el siguiente."""
        c, q = self.c, self.q
        abierto = c.execute("SELECT id FROM lotes WHERE estado='en_curso' ORDER BY id DESC LIMIT 1").fetchone()
        if abierto: lid = abierto[0]; self.log(f"Reanudando lote #{lid} (interrumpido antes)")
        else:
            lid = c.execute("INSERT INTO lotes(inicio,estado) VALUES(?,?)", (q.now(), "en_curso")).lastrowid; c.commit(); self.log(f"Lote #{lid} nuevo")
            self.capturar(lid)
        return lid

    def capturar(self, lid):
        c, q = self.c, self.q; nuevos = dup = 0
        for r in c.execute("SELECT * FROM ramas WHERE estado IN ('preparada','aprobada')").fetchall():
            clave = f"{r['rama']}@{r['sha'][:12]}"
            props = c.execute("SELECT id,datos FROM propuestas WHERE rama=? AND estado IN ('preparada','aprobada')", (r["rama"],)).fetchall()
            if self.item(clave) or not props: dup += 1; continue
            c.execute("INSERT INTO lote_items(clave,lote_id,rama,sha,area,propuestas,estado,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (clave, lid, r["rama"], r["sha"], r["area"], json.dumps([p["id"] for p in props]), "preparada", "{}", q.now(), q.now()))
            for p in props:  # el clic ES la autorizacion: preparada -> aprobada (mismo efecto que `aprobar`)
                if c.execute("SELECT estado FROM propuestas WHERE id=?", (p["id"],)).fetchone()[0] == "preparada": q.estado_prop(c, p["id"], "aprobada", f"aprobada por el clic de EJECUTAR-ACTIONS (lote {lid})")
            c.execute("UPDATE ramas SET estado='aprobada' WHERE rama=? AND estado='preparada'", (r["rama"],)); c.commit(); nuevos += 1
        self.log(f"Capturados {nuevos} tests nuevos ({dup} ya conocidos/omitidos)")

    # ---------- comprobaciones previas ----------
    def propuestas_de(self, it):
        return [self.c.execute("SELECT id,titulo,datos FROM propuestas WHERE id=?", (i,)).fetchone() for i in json.loads(it["propuestas"])]

    def verificar_rama(self, it):
        """Rama y commit validos, y el commit solo toca los ficheros declarados (nada de produccion)."""
        q = self.q
        try:
            self.git("cat-file", "-e", it["sha"] + "^{commit}")
            self.git("merge-base", "--is-ancestor", it["sha"], f"refs/heads/{it['rama']}")
        except RuntimeError as e: return f"rama/commit invalido: {str(e)[-160:]}"
        declarados = set()
        for p in self.c.execute("SELECT datos FROM propuestas WHERE rama=?", (it["rama"],)).fetchall():  # toda la historia de la rama, no solo lo que va en este lote
            d = json.loads(p["datos"]); declarados |= {f["ruta"] for f in d.get("ficheros_nuevos", [])} | {m["ruta"] for m in d.get("ficheros_modificados") or []}
        tocados = set(self.git("diff", "--name-only", self.base_de(it["sha"]), it["sha"]).split())
        if tocados - declarados: return f"el commit toca ficheros no declarados: {sorted(tocados - declarados)[:4]}"
        if not tocados: return "el commit no cambia nada"
        return None

    def base_de(self, sha):
        """Punto de partida de la rama: merge-base con origin/main (todos sus commits cuentan, no solo el ultimo)."""
        return self.git("merge-base", "origin/main", sha, check=False) or sha + "~1"

    def comandos(self, it):
        """(propuesta, ruta, argv, env). Usa los `pasos` validados al ingerir; solo `python|node <fichero declarado>`, nunca un shell."""
        cmds = []
        for p in self.propuestas_de(it):
            d = json.loads(p["datos"])
            pasos = d.get("pasos") or cob.normalizar_comandos(dict(d))
            for s in pasos:
                exe, ruta = s["argv"]
                if exe not in ("python", "node") or ruta not in {f["ruta"] for f in d.get("ficheros_nuevos", [])}: continue
                cmds.append((p["id"], ruta, [sys.executable if exe == "python" else "node", ruta], s.get("env") or {}))
        return cmds

    # ---------- validacion local ----------
    def validar_local(self, it):
        clave, q = it["clave"], self.q
        self.set(clave, "validacion_local", intentos=it["intentos"] + 1)
        if (msg := self.verificar_rama(it)): return self.set(clave, "revision_humana", msg)
        try: self.git("fetch", "-q", "origin", "main"); main = self.git("rev-parse", "origin/main")
        except RuntimeError: main = self.git("rev-parse", "origin/main", check=False) or "?"
        tmp = q.STATE / "lote_wt" / self.slug(clave); self.limpiar_wt(tmp)
        tmp.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.git("worktree", "add", "--detach", str(tmp), it["sha"])
            r = subprocess.run(["git", "-c", "user.name=qa-gpt", "-c", "user.email=qa-gpt@local", "merge", "--no-edit", main], cwd=tmp, capture_output=True, text=True)
            if r.returncode:
                subprocess.run(["git", "merge", "--abort"], cwd=tmp, capture_output=True)
                return self.set(clave, "revision_humana", f"conflicto al fusionar el test con main {main[:8]}", main_sha=main)
            nm = Path(self.cfg["node_modules"])
            if nm.exists() and not (tmp / "node_modules").exists(): subprocess.run(["cmd", "/c", "mklink", "/J", str(tmp / "node_modules"), str(nm)], capture_output=True)
            wfs = self.cableado(tmp, it)
            partes, clases = [], []
            for pid, ruta, cmd, env in self.comandos(it):
                rc, salida = self.ejecutar_test(tmp, ruta, cmd, env)
                cat = json.loads(next(p["datos"] for p in self.propuestas_de(it) if p["id"] == pid)).get("categoria")
                cl = self.clasificar(rc, salida, cat); clases.append(cl)
                partes.append(f"### propuesta #{pid} {' '.join(map(str, cmd[-2:]))} -> exit {rc} [{cl}]\n{salida[-6000:]}")
            logp = self.dir / f"{self.slug(clave)}.log"
            logp.write_text(f"rama {it['rama']}\nsha {it['sha']}\nmain {main}\nfecha {q.now()}\n\n" + "\n".join(partes), encoding="utf-8")
            peor = next((x for x in ("defecto_demostrado", "fallo_test", "infra", "revision_humana") if x in clases), "local_ok")
            upd = dict(local_exit=0 if peor == "local_ok" else 1, local_clase=peor, local_log=str(logp), main_sha=main, workflows=json.dumps(wfs))
            self.set(clave, "local_ok" if peor == "local_ok" else peor, {"local_ok": "tests locales correctos" + (" (parte sin navegador)" if "sin_entorno" in clases else ""),
                     "defecto_demostrado": "el test falla por el defecto descrito: evidencia en el log", "fallo_test": "el test falla y no es el defecto esperado: revisar el test",
                     "infra": "fallo de entorno al ejecutar localmente"}.get(peor, ""), **upd)
        finally: self.limpiar_wt(tmp)

    def ejecutar_test(self, tmp, ruta, cmd, env=None):
        env, srv = dict(env or {}), None
        if "playwright" in (tmp / ruta).read_text(encoding="utf-8", errors="replace"):
            puerto = self.puerto_libre()
            if puerto is None: return 0, "SIN_ENTORNO: ningun puerto libre; se valida en Actions"
            env = {**env, **self.entorno_url(tmp / ruta, puerto)}  # el test apunta a NUESTRO servidor, nunca a uno ajeno que ya escuche en 4173
            srv = subprocess.Popen([sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1", "--directory", str(tmp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
        try: return self.runner(cmd, tmp, env, self.cfg["timeout_test_s"])
        finally:
            if srv: srv.terminate(); srv.wait(10)

    def puerto_libre(self):
        base = self.cfg["puerto_estatico"]
        for puerto in range(base + 20, base + 60):  # lejos de 4173, que los servicios del usuario suelen ocupar
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", puerto)) != 0: return puerto
        return None

    @staticmethod
    def entorno_url(fichero, puerto):
        """Variables `process.env.X` del test que contienen la URL base (X termina en URL/ORIGIN/BASE) apuntadas al puerto propio."""
        txt = fichero.read_text(encoding="utf-8", errors="replace")
        nombres = set(re.findall(r"process\.env\.([A-Z][A-Z0-9_]*(?:URL|ORIGIN|BASE))", txt))
        return {n: f"http://127.0.0.1:{puerto}" for n in nombres}

    def clasificar(self, rc, out, categoria):
        if rc == 0: return "sin_entorno" if out.startswith("SIN_ENTORNO") else "local_ok"
        if SIN_ENTORNO.search(out): return "sin_entorno"
        if ASERCION.search(out): return "defecto_demostrado" if categoria == "descubre_defecto" else "fallo_test"
        if INFRA.search(out): return "infra"
        return "fallo_test"

    def limpiar_wt(self, tmp):
        if tmp.exists():
            j = tmp / "node_modules"
            if j.exists():
                try: os.rmdir(j)  # quita solo el junction, nunca el contenido de C:\GIT\web-escritor\node_modules
                except OSError: subprocess.run(["cmd", "/c", "rmdir", str(j)], capture_output=True)
            self.git("worktree", "remove", "--force", str(tmp), check=False)
        self.git("worktree", "prune", check=False)

    # ---------- cableado: que workflow ejecuta realmente el test ----------
    def cableado(self, tmp, it):
        rutas = [r for _, r, _, _ in self.comandos(it)]
        textos = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in sorted((tmp / ".github" / "workflows").glob("*.yml"))}
        return workflows_que_ejecutan(rutas, textos, {Path(json.loads(p["datos"]).get("workflow") or "").name for p in self.propuestas_de(it)})

    # ---------- GitHub ----------
    def enviar(self, it):
        clave, rama, sha = it["clave"], it["rama"], it["sha"]
        wfs = json.loads(it["workflows"] or "[]")
        if not wfs: return self.set(clave, "revision_humana", "ningun workflow con workflow_dispatch ejecuta este test (no esta cableado): Actions no lo validaria")
        tocado_wf = any(".github/workflows/" in f for f in self.git("diff", "--name-only", self.base_de(sha), sha).split())
        if tocado_wf and "workflow" not in self.gh.scopes():
            return self.set(clave, "revision_humana", "la rama modifica .github/workflows y el token de gh no tiene el scope 'workflow': ejecuta `gh auth refresh -s workflow` y pulsa de nuevo")
        try:
            if self.gh.remote_sha(rama) != sha: self.gh.push(sha, rama)
            runs = json.loads(it["runs"] or "{}")
            for wf in wfs:
                if wf in runs: continue
                prev = [r for r in self.gh.runs(wf, rama) if r["headSha"] == sha]  # no relanzar lo ya lanzado para el mismo SHA
                if not prev:
                    t0 = self.q.now(); self.gh.dispatch(wf, rama)
                    for _ in range(12):
                        self.sleep(5)
                        prev = [r for r in self.gh.runs(wf, rama) if r["headSha"] == sha]
                        if prev: break
                if prev: runs[wf] = {"id": prev[0]["databaseId"], "url": prev[0]["url"]}
                self.set(clave, "enviado" if wf not in runs else "actions_pendiente", f"{wf}: run {runs[wf]['id']}" if wf in runs else f"{wf} lanzado, run por localizar", runs=json.dumps(runs))
        except GhAuthError as e:
            self.set(clave, "revision_humana", f"GitHub rechaza el token/permisos ({str(e)[:120]}): `gh auth refresh -s repo` y pulsa de nuevo")
        except GhError as e:
            self.set(clave, "infra", f"GitHub no responde: {e}")
        except RuntimeError as e:
            self.set(clave, "revision_humana" if "rejected" in str(e) or "non-fast" in str(e) else "infra", f"push/dispatch: {str(e)[:200]}")

    def reconciliar(self, it):
        """Consulta GitHub y avanza el item; tambien recupera `enviado` sin run id (BAT cerrado tras el push)."""
        clave, rama, sha = it["clave"], it["rama"], it["sha"]; runs = json.loads(it["runs"] or "{}"); wfs = json.loads(it["workflows"] or "[]")
        try:
            for wf in wfs:
                if wf not in runs:
                    hit = [r for r in self.gh.runs(wf, rama) if r["headSha"] == sha]
                    if hit: runs[wf] = {"id": hit[0]["databaseId"], "url": hit[0]["url"]}
            if len(runs) < len(wfs): return "falta"
            estados = {wf: self.gh.run(r["id"]) for wf, r in runs.items()}
        except GhError as e: return f"gh:{e}"
        for wf, r in estados.items(): runs[wf].update(status=r["status"], conclusion=r["conclusion"])
        pend = [r for r in estados.values() if r["status"] != "completed"]
        if pend:
            self.set(clave, "actions_ejecutando" if any(r["status"] == "in_progress" for r in pend) else "actions_pendiente", runs=json.dumps(runs)); return "viva"
        malos = {wf: r for wf, r in estados.items() if r["conclusion"] != "success"}
        if not malos: self.set(clave, "actions_ok", f"{len(estados)} workflow(s) correctos para {sha[:8]}", runs=json.dumps(runs)); return "fin"
        wf, r = next(iter(malos.items())); log = self.gh.log_failed(r["databaseId"])
        logp = self.dir / f"{self.slug(clave)}.actions.log"; logp.write_text(f"run {r['databaseId']} {r['url']}\nsha {sha}\n\n{log[-20000:]}", encoding="utf-8")
        cat = json.loads(self.propuestas_de(it)[0]["datos"]).get("categoria")
        if r["conclusion"] in ("cancelled", "timed_out", "startup_failure") or (INFRA.search(log) and not ASERCION.search(log)): est = "infra"
        elif ASERCION.search(log): est = "defecto_demostrado" if cat == "descubre_defecto" else "actions_fallida"
        else: est = "actions_fallida"
        self.set(clave, est, f"{wf}: {r['conclusion']} run {r['databaseId']} (log {logp.name})", runs=json.dumps(runs)); return "fin"

    # ---------- orquestacion ----------
    def cerrar_propuestas(self, it):
        q = self.q
        for pid in json.loads(it["propuestas"]):
            est = self.item(it["clave"])["estado"]
            nota = f"lote {it['lote_id']}: {est} ({it['rama']}@{it['sha'][:8]})"
            actual = self.c.execute("SELECT estado FROM propuestas WHERE id=?", (pid,)).fetchone()[0]
            if est == "defecto_demostrado" and actual in ("aprobada", "publicada", "preparada"): q.estado_prop(self.c, pid, "ejecutada", nota, siguiente="DEFECTO DE PRODUCTO DEMOSTRADO: ver log del lote; corregir el producto en main")
            elif est in ("actions_ok", "actions_fallida", "fallo_test") and actual in ("aprobada", "publicada"): q.estado_prop(self.c, pid, "ejecutada", nota, siguiente=f"resultado {est}")
            elif est in ("enviado", "actions_pendiente", "actions_ejecutando") and actual == "aprobada": q.estado_prop(self.c, pid, "publicada", nota)
        self.c.commit()

    def ejecutar(self):
        q = self.q; t_fin = time.time() + self.cfg["max_horas"] * 3600
        try: self.gh.ok(); gh_ok = True
        except GhAuthError as e: gh_ok = False; self.log(f"GitHub RECHAZA el token ({str(e)[:80]}): ejecuta `gh auth login` (o `gh auth refresh -s repo`). Se valida en local; los envios quedan para el siguiente clic")
        except (GhError, OSError) as e: gh_ok = False; self.log(f"GitHub no disponible ({str(e)[:80]}): se valida en local y se reintenta el envio en el siguiente clic")
        lid = self.abrir_lote()
        for it in self.items(lid):  # reconciliar lo ya enviado en ejecuciones anteriores
            if it["estado"] in ("enviado", "actions_pendiente", "actions_ejecutando") and gh_ok: self.reconciliar(self.item(it["clave"]))
        for it in self.items(lid):
            it = self.item(it["clave"])
            if it["estado"] in ("preparada", "validacion_local") or (it["estado"] in REINTENTABLES and not it["local_log"]): self.validar_local(it)
        activos = {}
        while True:
            its = [self.item(i["clave"]) for i in self.items(lid)]
            if gh_ok:
                for it in its:
                    if it["estado"] == "infra" and it["intentos"] < self.cfg["reintentos_infra"]:
                        if it["local_clase"] == "infra": self.set(it["clave"], "preparada", "reintento local tras fallo de infraestructura"); self.validar_local(self.item(it["clave"]))
                        else: self.set(it["clave"], "local_ok", "reintento de envio tras fallo de infraestructura", intentos=it["intentos"] + 1)
                its = [self.item(i["clave"]) for i in self.items(lid)]
                vivos = [i for i in its if i["estado"] in ("enviado", "actions_pendiente", "actions_ejecutando")]
                for it in [i for i in its if i["estado"] == "local_ok"]:
                    if len(vivos) >= self.cfg["concurrencia"]: break
                    self.enviar(it); vivos.append(it)
                for it in [self.item(i["clave"]) for i in vivos]:
                    r = self.reconciliar(it) if it["estado"] in ("enviado", "actions_pendiente", "actions_ejecutando") else None
                    if r and str(r).startswith("gh:"): self.log(f"GitHub no responde ({r[3:60]}); se reintenta"); gh_ok = False
                its = [self.item(i["clave"]) for i in self.items(lid)]
            pendientes = [i for i in its if i["estado"] in ("enviado", "actions_pendiente", "actions_ejecutando", "local_ok")]
            if not pendientes or not gh_ok or time.time() > t_fin: break
            self.sleep(self.cfg["poll_s"])
        for it in self.items(lid): self.cerrar_propuestas(self.item(it["clave"]))
        its = self.items(lid)
        # local_ok que no llegaron a GitHub (sin conexion) siguen abiertos; el lote se cierra solo cuando todo es final
        cerrado = all(i["estado"] in ESTADOS_FINALES for i in its)
        resumen = {}; [resumen.__setitem__(i["estado"], resumen.get(i["estado"], 0) + 1) for i in its]
        self.c.execute("UPDATE lotes SET estado=?,fin=?,resumen=? WHERE id=?", ("cerrado" if cerrado else "en_curso", q.now() if cerrado else None, json.dumps(resumen), lid)); self.c.commit()
        self.log(f"Lote #{lid}: {resumen}" + ("" if cerrado else "  (quedan trabajos abiertos: vuelve a pulsar el BAT para reanudar)"))
        (self.dir / "ultimo.json").write_text(json.dumps({"lote": lid, "fecha": q.now(), "cerrado": cerrado, "resumen": resumen}), encoding="utf-8")
        return 0


class LoteLock:
    """Un lote a la vez: la doble pulsacion no duplica envios."""
    def __init__(self, q): self.q = q; self.p = q.STATE / "lote.lock"
    def __enter__(self):
        if self.p.exists():
            try: pid = int(self.p.read_text().split()[0])
            except Exception: pid = 0
            if pid and pid != os.getpid() and self.q.pid_alive(pid): raise SystemExit(f"Ya hay un lote en marcha (pid {pid}). No se duplica nada; mira ESTADO-QA-GPT.bat.")
        self.p.parent.mkdir(parents=True, exist_ok=True)
        self.p.write_text(f"{os.getpid()} {self.q.now()}"); return self
    def __exit__(self, *a): self.p.unlink(missing_ok=True)


def main(q, a=None):
    with LoteLock(q): return Lote(q).ejecutar()


def bloque_estado(q, c):
    """Lineas para ESTADO. Todo sale de la FOTO ACTUAL de lote_items/propuestas (un test cuenta una sola vez, en su estado de hoy)."""
    cnt = lambda tabla, *es: c.execute(f"SELECT COUNT(*) FROM {tabla} WHERE estado IN ({','.join('?' * len(es))})", es).fetchone()[0]
    try: c.execute("SELECT 1 FROM lote_items LIMIT 1")
    except Exception: return ["", "Lote Actions: (sin lotes todavia)"]
    li = lambda *es: cnt("lote_items", *es)
    escritos = cnt("propuestas", "preparada", "aprobada")  # tests escritos y aun sin ejecutar
    lines = ["", "Tests (foto actual, cada test cuenta una vez):",
             f"  - Escritos, sin ejecutar: {escritos}  (preparada/aprobada; los capturara el proximo lote)",
             f"  - En un lote, comprobacion local pendiente: {li('preparada', 'validacion_local')}",
             f"  - Validados en local (aptos para Actions): {li('local_ok')}",
             f"  - Defectos de producto demostrados: {li('defecto_demostrado')}  (el test falla por el defecto descrito: es un hallazgo, no un fallo)",
             f"  - Fallo del propio test: {li('fallo_test')}",
             f"  - Enviados a Actions: {li('enviado', 'actions_pendiente', 'actions_ejecutando', 'actions_ok', 'actions_fallida')}  "
             f"(en cola {li('enviado', 'actions_pendiente')}, ejecutandose {li('actions_ejecutando')}, aprobados {li('actions_ok')}, fallidos {li('actions_fallida')})",
             f"  - Errores de infraestructura: {li('infra')}  | requieren revision humana: {li('revision_humana')}"]
    ul = c.execute("SELECT id,inicio,fin,estado,resumen FROM lotes ORDER BY id DESC LIMIT 1").fetchone()
    lines.append(f"Ultimo lote: {('#' + str(ul['id']) + ' ' + ul['inicio'] + ' (' + ul['estado'] + ')') if ul else '(ninguno)'}")
    ue = c.execute("SELECT rama,sha,runs FROM lote_items WHERE runs LIKE '%\"id\"%' ORDER BY actualizado DESC LIMIT 1").fetchone()
    if ue: rid = next(iter(json.loads(ue["runs"]).values()))["id"]; lines.append(f"Ultima ejecucion en Actions: {ue['rama']} / {ue['sha'][:8]} / run {rid}")
    for r in c.execute("SELECT rama,sha,estado,detalle FROM lote_items WHERE estado IN ('defecto_demostrado','revision_humana','infra','fallo_test','actions_fallida') ORDER BY actualizado DESC LIMIT 8"):
        lines.append(f"    {r['estado']:<19} {r['rama'].replace('gpt-qa/', '')}@{r['sha'][:8]}: {(r['detalle'] or '')[:100]}")
    sig = c.execute("SELECT id FROM propuestas WHERE estado IN ('preparada','aprobada') ORDER BY id LIMIT 1").fetchone()
    sig_lote = c.execute("SELECT rama FROM lote_items WHERE estado IN ('preparada','validacion_local','local_ok','infra') ORDER BY rama LIMIT 1").fetchone()
    lines.append(f"Proximo pendiente: {('propuesta #' + str(sig[0])) if sig else (sig_lote['rama'] + ' (ya en lote abierto)' if sig_lote else '(ninguno)')}")
    return lines
