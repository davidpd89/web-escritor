"""qa_lote: lote de validacion con UN clic (EJECUTAR-ACTIONS-QA-GPT.bat).

Reutiliza el estado de qa_gpt (tablas propuestas/ramas) y el congelado de lote; anade lote_items (una fila por rama@sha), idempotente y reanudable.
Flujo por item: preparada -> validacion_local -> local_ok | fallo_test | defecto_demostrado | infra | revision_humana
                -> enviado -> actions_pendiente -> actions_ejecutando -> actions_ok | actions_fallida | defecto_demostrado | infra.
Nunca toca main, nunca abre/fusiona PRs: empuja SOLO la rama gpt-qa/* (sha exacto) y lanza el workflow que ejecuta el test (workflow_dispatch).
`q` = modulo qa_gpt (inyectado); `gh` y `runner` se sustituyen en las pruebas.
"""
import sqlite3, datetime as dt, fnmatch, json, os, re, socket, subprocess, sys, time
from pathlib import Path
import qa_cobertura as cob
import qa_clases
from qa_clases import clasificar_salida

GRUPO_WF = "qa-gpt-grupo.yml"  # workflow dedicado: ejecuta tests exploratorios/regresion y conserva resultados.json; no es un check obligatorio
ENVIABLES = ("local_ok", "local_hallazgo")  # listos para Actions (local_hallazgo = test valido cuya asercion falla: se envia igualmente para conservar la evidencia remota)
ESTADOS_FINALES = {"a_triar", "fallo_test", "defecto_demostrado", "actions_ok", "actions_fallida", "revision_humana", "local_ok_sin_actions"}
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
    CREATE TABLE IF NOT EXISTS lote_tests(clave TEXT, fuente TEXT, ruta TEXT, categoria TEXT, clase TEXT, rc INTEGER, run_id INTEGER, fecha TEXT, PRIMARY KEY(clave, fuente, ruta));
    """)


class Gh:
    """Fachada de `gh`/git remoto; todo fallo de red/API sale como GhError (transitorio)."""
    def __init__(self, q): self.q = q; self.repo = q.CFG["repo"]
    def _gh(self, *a):
        r = cob.run(["gh", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode:
            msg = (r.stderr or r.stdout).strip()[:300]
            raise (GhAuthError if re.search(r"HTTP 40[13]|Bad credentials|auth login|not logged|Resource not accessible|must have admin|requires.*scope", msg, re.I) else GhError)(msg)
        return r.stdout
    def ok(self): self._gh("api", "user", "--jq", ".login"); return True
    def scopes(self):
        if getattr(self, "_scopes", None) is None:  # los permisos del token no cambian durante un lote
            r = cob.run(["gh", "auth", "status"], capture_output=True, text=True, encoding="utf-8", errors="replace")
            m = re.search(r"Token scopes:\s*(.+)", r.stdout + r.stderr); self._scopes = set(re.findall(r"[\w:]+", m.group(1))) if m else set()
        return self._scopes
    def remotos(self):
        """Todas las ramas gpt-qa/* del remoto en UNA consulta (antes, una `ls-remote` por rama)."""
        if getattr(self, "_remotos", None) is None:
            r = cob.run(["git", "ls-remote", "origin", "refs/heads/gpt-qa/*"], cwd=self.q.ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if r.returncode: raise GhError(r.stderr.strip()[:300])
            self._remotos = {ref.removeprefix("refs/heads/"): sha for sha, ref in (ln.split() for ln in r.stdout.splitlines() if ln.strip())}
        return self._remotos
    def remote_sha(self, rama): return self.remotos().get(rama)
    def push(self, sha, rama):
        if not rama.startswith(("gpt-qa/", "qa-fix/")): raise GhAuthError(f"push bloqueado: solo ramas gpt-qa/* o qa-fix/* (no {rama})")
        r = cob.run(["git", "push", "origin", f"{sha}:refs/heads/{rama}"], cwd=self.q.ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode: raise GhError((r.stderr or r.stdout).strip()[:400])
        self.remotos()[rama] = sha
    def runs(self, wf, rama):
        return json.loads(self._gh("run", "list", "-R", self.repo, "--workflow", wf, "--branch", rama, "--limit", "30",
                                   "--json", "databaseId,headSha,status,conclusion,event,createdAt,url") or "[]")
    def run(self, rid):
        return json.loads(self._gh("run", "view", str(rid), "-R", self.repo, "--json", "databaseId,status,conclusion,headSha,url"))
    def pr_crear(self, rama, titulo, cuerpo, borrador=True):
        """PR hacia main SIN merge ni auto-merge; borrador por defecto."""
        a = ["pr", "create", "-R", self.repo, "--base", "main", "--head", rama, "--title", titulo, "--body", cuerpo]
        return self._gh(*(a + (["--draft"] if borrador else []))).strip().splitlines()[-1]
    def pr_de_rama(self, rama):
        r = json.loads(self._gh("pr", "list", "-R", self.repo, "--state", "open", "--head", rama, "--json", "number,url,headRefOid") or "[]")
        return r[0] if r else None
    def prs_abiertas(self):
        return json.loads(self._gh("pr", "list", "-R", self.repo, "--state", "open", "--limit", "200", "--json", "number,headRefName,isDraft,url,title,createdAt,files") or "[]")
    def pr_ver(self, n):
        return json.loads(self._gh("pr", "view", str(n), "-R", self.repo, "--json", "state,isDraft,mergeable,mergeStateStatus,headRefOid,statusCheckRollup,url,files"))
    def pr_diff(self, n): return self._gh("pr", "diff", str(n), "-R", self.repo)
    def pr_merge(self, n, sha):
        """Merge por el mecanismo de GitHub (squash) atado al commit revisado; sin --admin: las protecciones de la rama se respetan."""
        self._gh("pr", "merge", str(n), "-R", self.repo, "--squash", "--match-head-commit", sha)
    def pr_actualizar(self, n): self._gh("pr", "update-branch", str(n), "-R", self.repo)
    def main_desde(self, sha):
        """-> (commits de main que `sha` no tiene, rutas que cambiaron en main desde la base comun). La API corta en 300 ficheros."""
        d = json.loads(self._gh("api", f"repos/{self.repo}/compare/{sha}...main", "--jq", "{n: .ahead_by, f: [.files[]?.filename]}"))
        return d["n"], d["f"]
    def pr_cerrar(self, url, comentario=""):
        self._gh("pr", "close", url, "-R", self.repo, "--delete-branch", *(["--comment", comentario] if comentario else []))
    def dispatch(self, wf, rama, ref=None, campos=None):
        """Sin `ref`, el workflow corre sobre la propia rama (workflows ya existentes). Con `ref`, el workflow vive en `ref` y recibe `campos` como inputs."""
        self._gh("workflow", "run", wf, "-R", self.repo, "--ref", ref or rama, *[a for k, v in (campos or {}).items() for a in ("-f", f"{k}={v}")])
    def workflow_ref(self):
        """Rama donde vive qa-gpt-grupo.yml: main si ya esta fusionado; si no, la rama de trabajo (cfg lote.workflow_ref)."""
        if getattr(self, "_wfref", None) is None:
            try: self._gh("api", f"repos/{self.repo}/contents/.github/workflows/{GRUPO_WF}?ref=main", "--silent"); self._wfref = "main"
            except GhError: self._wfref = self.q.CFG.get("lote", {}).get("workflow_ref", "automation/qa-gpt")
        return self._wfref
    def runs_grupo(self, sha):
        """Runs del workflow dedicado para ESTE commit (el run-name lleva el sha; headSha es el del workflow, no el del test)."""
        rs = json.loads(self._gh("run", "list", "-R", self.repo, "--workflow", GRUPO_WF, "--limit", "100", "--json", "databaseId,headSha,status,conclusion,event,createdAt,url,displayTitle") or "[]")
        return [r for r in rs if sha in (r.get("displayTitle") or "")]
    def resultados(self, rid):
        """resultados.json del artefacto qa-gpt-resultados; None si el run no lo subio (fallo previo al driver). Un error de red se propaga."""
        import shutil, tempfile
        d = Path(tempfile.mkdtemp(prefix="qa-res-", dir=self.q.STATE))
        try:
            try: self._gh("run", "download", str(rid), "-R", self.repo, "-n", "qa-gpt-resultados", "-D", str(d))
            except GhAuthError: raise
            except GhError as e:
                if re.search(r"no valid artifacts|not found|no artifact", str(e), re.I): return None
                raise
            f = next(d.rglob("resultados.json"), None)
            return json.loads(f.read_text(encoding="utf-8")) if f else None
        finally: shutil.rmtree(d, ignore_errors=True)
    def log_failed(self, rid):
        try: return self._gh("run", "view", str(rid), "-R", self.repo, "--log-failed")
        except GhError as e: return str(e)


class GhError(RuntimeError): pass
class GhAuthError(GhError): """Token sin sesion o sin permisos: no es transitorio, reintentar no sirve."""


ABORTAR = None  # callable -> True cuando hay que soltar el test en curso (Q / Ctrl+C / cierre de ventana)
RC_ABORTADO = 130


def matar_arbol(p):
    """El test y todo lo que lanzo (node, servidores, navegadores): ninguno queda huerfano."""
    try: cob.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, timeout=30)
    except Exception: p.kill()


def run_cmd(args, cwd, env=None, timeout=300):
    """Ejecuta un comando local; devuelve (rc, salida). Se interrumpe en ~1 s si ABORTAR() pide parar (rc 130)."""
    # UTF-8 como en CI (Linux): en Windows open() sin encoding usa cp1252 y los tests fallaban con 'charmap' sin que el parche tuviera culpa
    p = cob.popen(args, cwd=cwd, env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    fin = time.monotonic() + timeout
    while True:
        try:
            out, _ = p.communicate(timeout=1); return p.returncode, out or ""
        except subprocess.TimeoutExpired:
            if ABORTAR and ABORTAR():
                matar_arbol(p); p.communicate(); return RC_ABORTADO, "ABORTADO: parada solicitada durante la ejecucion"
            if time.monotonic() > fin:
                matar_arbol(p); out, _ = p.communicate()
                return 124, f"TimeoutExpired tras {timeout}s\n{(out or '')[-1500:]}"


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
        self.cfg = {"concurrencia": 3, "max_horas": 8, "poll_s": 30, "timeout_test_s": 300, "reintentos_infra": 3, "puerto_estatico": 4173,
                    "node_modules": r"C:\GIT\web-escritor\node_modules", "actions_siempre": False, "concurrencia_local": 1, "espera_ociosa_s": 60, "tam_lote": 40, "continuo": False, **q.CFG.get("lote", {}), **(cfg or {})}
        self.dir = q.STATE / "lote"; self.dir.mkdir(parents=True, exist_ok=True)
        self.c = q.db(); self.c.execute("PRAGMA busy_timeout=180000")
        global ABORTAR
        ABORTAR = lambda: bool(self.parando)
        self.parando = None; self.interactivo = False; self._ultimo_sondeo = 0; self._refs = self._main = None; self._tocados, self._bases, self._podado = {}, {}, False  # lo que git ya contesto en este lote no se vuelve a preguntar

    # ---------- persistencia ----------
    def git(self, *a, check=True): return self.q.git(*a, cwd=self.q.ROOT, check=check)  # ROOT en tiempo de llamada (las pruebas lo redirigen)

    def refs(self):
        """Cabeza de cada rama gpt-qa/* local, en una sola consulta."""
        if self._refs is None:
            self._refs = {}
            for ln in self.git("for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads/gpt-qa/", check=False).splitlines():
                n, _, h = ln.rpartition(" "); self._refs[n] = h
        return self._refs

    def main_sha(self):
        """origin/main una sola vez por lote (un fetch, no uno por rama): todas las ramas se validan contra la misma base."""
        if self._main is None:
            try: self.git("fetch", "-q", "origin", "main")
            except RuntimeError: pass
            self._main = self.git("rev-parse", "origin/main", check=False) or "?"
        return self._main

    def tocados(self, sha):
        if sha not in self._tocados:  # `origin/main...sha` = diff desde el merge-base, en un solo proceso
            self._tocados[sha] = set(self.git("diff", "--name-only", f"origin/main...{sha}", check=False).split()) or set(self.git("diff", "--name-only", sha + "~1", sha).split())
        return self._tocados[sha]

    @staticmethod
    def slug(clave): return re.sub(r"\W", "_", clave)

    def log(self, msg): self.out(f"[{dt.datetime.now():%H:%M:%S}] {msg}")

    def set(self, clave, estado, detalle=None, **extra):
        cols = {"estado": estado, "actualizado": self.q.now(), **extra}
        if detalle is not None: cols["detalle"] = detalle[:600]
        for intento in range(6):  # el worker escribe en la misma base: un bloqueo transitorio no debe tumbar el lote
            try:
                self.c.execute(f"UPDATE lote_items SET {','.join(k + '=?' for k in cols)} WHERE clave=?", (*cols.values(), clave))
                self.c.execute("INSERT INTO lote_hist VALUES(?,?,?,?)", (clave, self.q.now(), estado, (detalle or "")[:300])); self.c.commit(); break
            except sqlite3.OperationalError:
                self.c.rollback()
                if intento == 5: raise
                self.sleep(5)
        self.log(f"{clave.split('@')[0].replace('gpt-qa/', '')}: {estado}" + (f" - {detalle[:140]}" if detalle else ""))

    def item(self, clave): return self.c.execute("SELECT * FROM lote_items WHERE clave=?", (clave,)).fetchone()
    def items(self, lote_id): return self.c.execute("SELECT * FROM lote_items WHERE lote_id=? ORDER BY rama", (lote_id,)).fetchall()

    # ---------- lote: captura congelada ----------
    def abrir_lote(self):
        """Reanuda un lote abierto (BAT cerrado a medias) o congela uno nuevo con lo preparado AHORA. Lo generado despues queda para el siguiente."""
        c, q = self.c, self.q
        abierto = c.execute("SELECT id FROM lotes WHERE estado='en_curso' ORDER BY id DESC LIMIT 1").fetchone()
        if abierto:
            lid = abierto[0]
            if lid != getattr(self, "_lote_reanudado", None): self.log(f"Reanudando lote #{lid} (interrumpido antes)")
            self._lote_reanudado = lid
            self.capturar(lid)  # lo preparado despues entra en el lote abierto (si no, hay_nuevo seguia verdadero y el bucle giraba sin parar)
        else:
            lid = c.execute("INSERT INTO lotes(inicio,estado) VALUES(?,?)", (q.now(), "en_curso")).lastrowid; c.commit(); self.log(f"Lote #{lid} nuevo")
            self.capturar(lid)
        return lid

    def capturar(self, lid):
        c, q = self.c, self.q; nuevos = dup = 0
        try: q.reparar_perdidas(c)  # una `preparada` sin sus ficheros en la rama no es ejecutable: vuelve a `aceptada` en vez de entrar al lote y fallar
        except Exception as e: self.log(f"Reparacion de preparadas omitida ({str(e)[:100]})")
        ramas = c.execute("SELECT * FROM ramas WHERE estado IN ('preparada','aprobada')").fetchall()
        tope = int(self.cfg.get("limite") or self.cfg["tam_lote"])  # un lote acotado: el resto queda preparado para el siguiente
        if self.cfg.get("limite"):  # prueba acotada: primero las ramas de regresion (las que Actions puede dar por buenas)
            reg = lambda r: not c.execute("SELECT 1 FROM propuestas WHERE rama=? AND json_extract(datos,'$.categoria')<>'regresion' LIMIT 1", (r["rama"],)).fetchone()
            ramas = sorted(ramas, key=lambda r: not reg(r))
        for r in ramas:
            clave = f"{r['rama']}@{r['sha'][:12]}"
            props = c.execute("SELECT id,datos FROM propuestas WHERE rama=? AND estado IN ('preparada','aprobada')", (r["rama"],)).fetchall()
            if self.item(clave) or not props: dup += 1; continue
            if nuevos >= tope: continue
            c.execute("INSERT INTO lote_items(clave,lote_id,rama,sha,area,propuestas,estado,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?)",
                      (clave, lid, r["rama"], r["sha"], r["area"], json.dumps([p["id"] for p in props]), "preparada", "{}", q.now(), q.now()))
            for p in props:  # el clic ES la autorizacion: preparada -> aprobada (mismo efecto que `aprobar`)
                if c.execute("SELECT estado FROM propuestas WHERE id=?", (p["id"],)).fetchone()[0] == "preparada": q.estado_prop(c, p["id"], "aprobada", f"aprobada por el clic de EJECUTAR-ACTIONS (lote {lid})")
            c.execute("UPDATE ramas SET estado='aprobada' WHERE rama=? AND estado='preparada'", (r["rama"],)); c.commit(); nuevos += 1
        self.log(f"Capturados {nuevos} tests nuevos ({dup} ya conocidos/omitidos)")

    def hay_nuevo(self):
        """Hay ramas preparadas que todavia no son item de ningun lote (el worker sigue generando)."""
        for r in self.c.execute("SELECT rama,sha FROM ramas WHERE estado IN ('preparada','aprobada')").fetchall():
            if not self.item(f"{r['rama']}@{r['sha'][:12]}") and self.c.execute("SELECT 1 FROM propuestas WHERE rama=? AND estado IN ('preparada','aprobada') LIMIT 1", (r["rama"],)).fetchone(): return True
        return False

    # ---------- comprobaciones previas ----------
    def propuestas_de(self, it):
        return [self.c.execute("SELECT id,titulo,datos FROM propuestas WHERE id=?", (i,)).fetchone() for i in json.loads(it["propuestas"])]

    def verificar_rama(self, it):
        """Rama y commit validos, y el commit solo toca los ficheros declarados (nada de produccion)."""
        q = self.q
        try:
            if self.refs().get(it["rama"]) != it["sha"]:  # la rama avanzo o cambio: hay que probar que el commit sigue siendo suyo
                self.git("cat-file", "-e", it["sha"] + "^{commit}")
                self.git("merge-base", "--is-ancestor", it["sha"], f"refs/heads/{it['rama']}")
        except RuntimeError as e: return f"rama/commit invalido: {str(e)[-160:]}"
        declarados = set()
        for p in self.c.execute("SELECT datos FROM propuestas WHERE rama=?", (it["rama"],)).fetchall():  # toda la historia de la rama, no solo lo que va en este lote
            d = json.loads(p["datos"]); declarados |= {f["ruta"] for f in d.get("ficheros_nuevos", [])} | {m["ruta"] for m in d.get("ficheros_modificados") or []}
        tocados = self.tocados(it["sha"])
        if tocados - declarados: return f"el commit toca ficheros no declarados: {sorted(tocados - declarados)[:4]}"
        if not tocados: return "el commit no cambia nada"
        return None

    def base_de(self, sha):
        """Punto de partida de la rama: merge-base con origin/main (todos sus commits cuentan, no solo el ultimo)."""
        if sha not in self._bases: self._bases[sha] = self.git("merge-base", "origin/main", sha, check=False) or sha + "~1"
        return self._bases[sha]

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
        main = self.main_sha()
        if (msg := self.verificar_rama(it)): return self.set(clave, "revision_humana", msg)
        tmp = q.STATE / "lote_wt" / self.slug(clave); self.limpiar_wt(tmp)
        tmp.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.git("worktree", "add", "--detach", str(tmp), it["sha"])
            r = cob.run(["git", "-c", "user.name=qa-gpt", "-c", "user.email=qa-gpt@local", "merge", "--no-edit", main], cwd=tmp, capture_output=True, text=True)
            if r.returncode:
                cob.run(["git", "merge", "--abort"], cwd=tmp, capture_output=True)
                return self.set(clave, "revision_humana", f"conflicto al fusionar el test con main {main[:8]}", main_sha=main)
            nm = Path(self.cfg["node_modules"])
            if nm.exists() and not (tmp / "node_modules").exists(): self.junction(tmp / "node_modules", nm)
            wfs = self.cableado(tmp, it)
            partes, clases = [], []
            for pid, ruta, cmd, env in self.comandos(it):
                cat = json.loads(next(p["datos"] for p in self.propuestas_de(it) if p["id"] == pid)).get("categoria")
                rc, salida = self.precheck(tmp, ruta, cmd)  # un test que ni parsea no es un hallazgo: se rechaza sin gastar ejecucion ni Actions
                if rc == 0: rc, salida = self.ejecutar_test(tmp, ruta, cmd, env)
                if rc == RC_ABORTADO and self.parando:  # no es un fallo del test: se suelta y se revalida en la proxima apertura
                    return self.set(clave, "preparada", f"validacion interrumpida ({self.parando}); se reanuda al reabrir", intentos=max(0, it["intentos"]))
                cl = clasificar_salida(rc, salida); clases.append((cl, cat)); self.registrar_test(clave, "local", ruta, cat, cl, rc)
                partes.append(f"### propuesta #{pid} {' '.join(map(str, cmd[-2:]))} -> exit {rc} [{cl}]\n{salida[-6000:]}")
            logp = self.dir / f"{self.slug(clave)}.log"
            logp.write_text(f"rama {it['rama']}\nsha {it['sha']}\nmain {main}\nfecha {q.now()}\n\n" + "\n".join(partes), encoding="utf-8")
            est = [qa_clases.estado_por_categoria(cl, cat) for cl, cat in clases]
            peor = next((x for x in ("fallo_test", "infra") if x in est), None)
            if not peor and ("defecto_demostrado" in est or "a_triar" in est): peor = "local_hallazgo"
            peor = peor or "local_ok"
            clase_local = "defecto_demostrado" if "defecto_demostrado" in est else "a_triar" if "a_triar" in est else peor
            upd = dict(local_exit=0 if peor == "local_ok" else 1, local_clase=clase_local if peor == "local_hallazgo" else peor, local_log=str(logp), main_sha=main, workflows=json.dumps(wfs))
            sin_nav = " (parte sin navegador)" if any(c == "sin_entorno" for c, _ in clases) else ""
            self.set(clave, peor, {"local_ok": "tests locales correctos" + sin_nav, "local_hallazgo": f"asercion fallida en local ({clase_local}): se envia a Actions para conservar la evidencia remota",
                     "fallo_test": "test invalido o regresion rota: no se envia (revisar el test)", "infra": "fallo de entorno al ejecutar localmente"}[peor], **upd)
        finally: self.limpiar_wt(tmp)

    def precheck(self, tmp, ruta, cmd):
        """Sintaxis sin ejecutar el test: `compile` para Python, `node --check` para JS. (0, '') si parsea."""
        try:
            if ruta.endswith(".py"): compile((tmp / ruta).read_text(encoding="utf-8"), ruta, "exec"); return 0, ""
            if ruta.endswith((".mjs", ".js", ".cjs")): return (lambda r: (0, "") if r[0] == 0 else r)(self.runner(["node", "--check", ruta], tmp, {}, 60))
        except SyntaxError as e: return 1, f"SyntaxError: {e}"
        return 0, ""

    def registrar_test(self, clave, fuente, ruta, categoria, clase, rc, run_id=None):
        self.c.execute("INSERT OR REPLACE INTO lote_tests VALUES(?,?,?,?,?,?,?,?)", (clave, fuente, ruta, categoria, clase, rc, run_id, self.q.now())); self.c.commit()

    def ejecutar_test(self, tmp, ruta, cmd, env=None):
        env, srv = dict(env or {}), None
        if "playwright" in (tmp / ruta).read_text(encoding="utf-8", errors="replace"):
            puerto = self.puerto_libre()
            if puerto is None: return 0, "SIN_ENTORNO: ningun puerto libre; se valida en Actions"
            env = {**env, **self.entorno_url(tmp / ruta, puerto)}  # el test apunta a NUESTRO servidor, nunca a uno ajeno que ya escuche en 4173
            srv = cob.popen([sys.executable, "-m", "http.server", str(puerto), "--bind", "127.0.0.1", "--directory", str(tmp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        """Estado de un test suelto segun su intencion (compat: devuelve local_ok/sin_entorno/a_triar/defecto_demostrado/fallo_test/infra)."""
        return qa_clases.estado_por_categoria(clasificar_salida(rc, out), categoria)

    @staticmethod
    def junction(destino, origen):
        """Junction sin lanzar `cmd /c mklink` (un proceso y una ventana por rama)."""
        try:
            import _winapi; _winapi.CreateJunction(str(origen), str(destino))
        except Exception: cob.run(["cmd", "/c", "mklink", "/J", str(destino), str(origen)], capture_output=True)

    def limpiar_wt(self, tmp):
        if tmp.exists():
            j = tmp / "node_modules"
            if j.exists():
                try: os.rmdir(j)  # quita solo el junction, nunca el contenido de C:\GIT\web-escritor\node_modules
                except OSError: cob.run(["cmd", "/c", "rmdir", str(j)], capture_output=True)
            self.git("worktree", "remove", "--force", str(tmp), check=False)
        if not self._podado: self.git("worktree", "prune", check=False); self._podado = True  # registros huerfanos: una vez por lote, no tres por rama

    # ---------- cableado: que workflow ejecuta realmente el test ----------
    def cableado(self, tmp, it):
        """Workflow que ejecutara el grupo. Exploratorias y descubre_defecto van SIEMPRE al dedicado (resultados separados de los checks
        obligatorios); un grupo solo de regresion usa el workflow existente que de verdad ejecuta el test y, si no hay, el dedicado."""
        cats = {json.loads(p["datos"]).get("categoria") for p in self.propuestas_de(it)}
        if cats - {"regresion"}: return [GRUPO_WF]
        rutas = [r for _, r, _, _ in self.comandos(it)]
        textos = {f.name: f.read_text(encoding="utf-8", errors="replace") for f in sorted((tmp / ".github" / "workflows").glob("*.yml"))}
        return workflows_que_ejecutan(rutas, textos, {Path(json.loads(p["datos"]).get("workflow") or "").name for p in self.propuestas_de(it)}) or [GRUPO_WF]

    def modo_de(self, it):
        return "regresion" if all(json.loads(p["datos"]).get("categoria") == "regresion" for p in self.propuestas_de(it)) else "exploratorio"

    def hallar_run(self, wf, rama, sha):
        return [r for r in (self.gh.runs_grupo(sha) if wf == GRUPO_WF else self.gh.runs(wf, rama)) if wf == GRUPO_WF or r["headSha"] == sha]

    # ---------- GitHub ----------
    def enviar(self, it):
        clave, rama, sha = it["clave"], it["rama"], it["sha"]
        wfs = json.loads(it["workflows"] or "[]")
        if not wfs: return self.set(clave, "revision_humana", "ningun workflow ejecuta este test: Actions no lo validaria")
        tocado_wf = any(".github/workflows/" in f for f in self.tocados(sha))
        if tocado_wf and "workflow" not in self.gh.scopes():
            return self.set(clave, "revision_humana", "la rama modifica .github/workflows y el token de gh no tiene el scope 'workflow': ejecuta `gh auth refresh -s workflow` y pulsa de nuevo")
        try:
            if self.gh.remote_sha(rama) != sha: self.gh.push(sha, rama)
            runs = json.loads(it["runs"] or "{}")
            for wf in wfs:
                if wf in runs: continue
                prev = self.hallar_run(wf, rama, sha)  # no relanzar lo ya lanzado para el mismo SHA
                if not prev:
                    if wf == GRUPO_WF:
                        tests = " ".join(f"{cmd[0] if cmd[0] == 'node' else 'python'}:{ruta}" for _, ruta, cmd, _ in self.comandos(it))
                        self.gh.dispatch(wf, rama, ref=self.gh.workflow_ref(), campos={"sha": sha, "modo": self.modo_de(it), "tests": tests})
                    else: self.gh.dispatch(wf, rama)
                    for _ in range(12):
                        self.sleep(5)
                        prev = self.hallar_run(wf, rama, sha)
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
                    hit = self.hallar_run(wf, rama, sha)
                    if hit: runs[wf] = {"id": hit[0]["databaseId"], "url": hit[0]["url"]}
            if len(runs) < len(wfs): return "falta"
            estados = {wf: self.gh.run(r["id"]) for wf, r in runs.items()}
        except GhError as e: return f"gh:{e}"
        for wf, r in estados.items(): runs[wf].update(status=r["status"], conclusion=r["conclusion"])
        pend = [r for r in estados.values() if r["status"] != "completed"]
        if pend:
            self.set(clave, "actions_ejecutando" if any(r["status"] == "in_progress" for r in pend) else "actions_pendiente", runs=json.dumps(runs)); return "viva"
        if GRUPO_WF in estados:  # el artefacto manda: un job verde o rojo solo dice si el driver termino, no que encontro
            try: res = self.gh.resultados(estados[GRUPO_WF]["databaseId"])
            except GhError as e: return f"gh:{e}"
            if res is not None:
                est, det = self.veredicto_remoto(it, res, estados[GRUPO_WF]["databaseId"])
                (self.dir / f"{self.slug(clave)}.actions.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
                self.set(clave, est, f"{GRUPO_WF}: run {estados[GRUPO_WF]['databaseId']}: {det}", runs=json.dumps(runs)); return "fin"
        malos = {wf: r for wf, r in estados.items() if r["conclusion"] != "success"}
        if not malos: self.set(clave, "actions_ok", f"{len(estados)} workflow(s) correctos para {sha[:8]}", runs=json.dumps(runs)); return "fin"
        wf, r = next(iter(malos.items())); log = self.gh.log_failed(r["databaseId"])
        logp = self.dir / f"{self.slug(clave)}.actions.log"; logp.write_text(f"run {r['databaseId']} {r['url']}\nsha {sha}\n\n{log[-20000:]}", encoding="utf-8")
        cat = json.loads(self.propuestas_de(it)[0]["datos"]).get("categoria")
        if r["conclusion"] in ("cancelled", "timed_out", "startup_failure") or (INFRA.search(log) and not ASERCION.search(log)): est = "infra"
        elif ASERCION.search(log): est = "defecto_demostrado" if cat == "descubre_defecto" else "a_triar" if cat == "exploratoria" else "actions_fallida"
        else: est = "actions_fallida"
        self.set(clave, est, f"{wf}: {r['conclusion']} run {r['databaseId']} (log {logp.name})", runs=json.dumps(runs)); return "fin"

    def veredicto_remoto(self, it, res, run_id):
        """Estado final de un grupo a partir de resultados.json del runner: invalido > infra > regresion rota > defecto > hallazgo > ok."""
        cats = {}
        for p in self.propuestas_de(it):
            d = json.loads(p["datos"])
            for s_ in d.get("pasos") or cob.normalizar_comandos(dict(d)): cats[s_["argv"][1]] = d.get("categoria")
        est = []
        for t in res["tests"]:
            cat = cats.get(t["ruta"]); self.registrar_test(it["clave"], "actions", t["ruta"], cat, t["clase"], t["rc"], run_id)
            est.append(qa_clases.estado_por_categoria(t["clase"], cat))
        resumen = ", ".join(f"{n} {k}" for k, n in sorted(res.get("resumen", {}).items()))
        if "fallo_test" in est: return ("actions_fallida" if any(t["clase"] == "hallazgo" for t in res["tests"]) and not any(t["clase"] == "invalido" for t in res["tests"]) else "fallo_test"), resumen
        for e in ("infra", "defecto_demostrado", "a_triar"):
            if e in est: return e, resumen
        return "actions_ok", resumen

    # ---------- orquestacion ----------
    def cerrar_propuestas(self, it):
        q = self.q
        for pid in json.loads(it["propuestas"]):
            est = self.item(it["clave"])["estado"]
            nota = f"lote {it['lote_id']}: {est} ({it['rama']}@{it['sha'][:8]})"
            actual = self.c.execute("SELECT estado FROM propuestas WHERE id=?", (pid,)).fetchone()[0]
            if est == "a_triar" and actual in ("aprobada", "publicada", "preparada"): q.estado_prop(self.c, pid, "ejecutada", nota, siguiente="POSIBLE DEFECTO A TRIAR: ver log; confirmar defecto o falso positivo")
            elif est == "defecto_demostrado" and actual in ("aprobada", "publicada", "preparada"): q.estado_prop(self.c, pid, "ejecutada", nota, siguiente="DEFECTO DE PRODUCTO DEMOSTRADO: ver log del lote; corregir el producto en main")
            elif est in ("actions_ok", "actions_fallida", "fallo_test") and actual in ("aprobada", "publicada"): q.estado_prop(self.c, pid, "ejecutada", nota, siguiente=f"resultado {est}")
            elif est in ("enviado", "actions_pendiente", "actions_ejecutando") and actual == "aprobada": q.estado_prop(self.c, pid, "publicada", nota)
        self.c.commit()

    # ---------- ejecutor progresivo (max 3 grupos remotos) ----------
    VIVOS = ("enviado", "actions_pendiente", "actions_ejecutando")
    MAX_GRUPOS = 3

    def pedir_parada(self, motivo="parada solicitada"):
        """Q, Ctrl+C o cerrar la consola: deja de LANZAR grupos nuevos. Los runs ya enviados a GitHub NO se cancelan."""
        if not self.parando:
            self.parando = motivo
            try: print(f"[{dt.datetime.now():%H:%M:%S}] PARADA solicitada: {motivo}", flush=True)
            except Exception: pass

    def tecla(self):
        if not self.interactivo: return
        try:
            import msvcrt
            while msvcrt.kbhit():
                if msvcrt.getwch().lower() == "q": self.pedir_parada("tecla Q")
        except ImportError: pass

    def esperar(self, s):
        if not self.interactivo: return self.sleep(s)
        fin = time.time() + s
        while time.time() < fin and not self.parando: self.tecla(); self.sleep(min(1, max(0, fin - time.time())))

    def conteo(self, lid):
        its = [self.item(i["clave"]) for i in self.items(lid)]
        n = lambda *es: sum(1 for i in its if i["estado"] in es)
        return {"lote": lid, "total": len(its), "esperando": n("preparada"), "validando": n("validacion_local"), "local_ok": n("local_ok", "local_hallazgo"),
                "enviados": n("enviado", "actions_pendiente"), "ejecutando": n("actions_ejecutando"),
                "terminados": n("actions_ok", "actions_fallida", "defecto_demostrado", "a_triar", "fallo_test", "revision_humana", "infra"),
                "aprobados": n("actions_ok"), "fallos_producto": n("defecto_demostrado", "a_triar"), "fallos_test": n("fallo_test", "actions_fallida"),
                "infra": n("infra"), "revision": n("revision_humana"), "grupos_remotos": n(*self.VIVOS), "limite": self.MAX_GRUPOS,
                "parando": self.parando, "fecha": self.q.now()}

    def panel(self, lid):
        k = self.conteo(lid)
        try:
            import qa_triaje; k["analisis_pendiente"] = len(qa_triaje.pendientes(self.c, self.dir))
        except Exception: k["analisis_pendiente"] = 0
        try: (self.dir / "ejecutor.json").write_text(json.dumps(k), encoding="utf-8")
        except OSError: pass
        if self.cfg.get("panel"):
            tx = [f"EJECUTAR-ACTIONS-QA-GPT  lote #{lid}  {dt.datetime.now():%H:%M:%S}   [Q] parar tras guardar  [Ctrl+C] parada controlada",
                  f"  Grupos en GitHub ahora: {k['grupos_remotos']}/{k['limite']}   (cerrar esta ventana NO cancela los runs ya enviados)",
                  f"  Esperando {k['esperando']} | validando en local {k['validando']} | listos para enviar {k['local_ok']} | enviados {k['enviados']} | ejecutando {k['ejecutando']}",
                  f"  Terminados {k['terminados']}/{k['total']}: aprobados {k['aprobados']} | fallos de producto {k['fallos_producto']} | fallos del test {k['fallos_test']} | infraestructura {k['infra']} | revision humana {k['revision']}",
                  f"  Pendientes de analisis GPT: {k['analisis_pendiente']}" + (f"   >>> {k['parando']}: no se lanzan grupos nuevos" if k["parando"] else "")]
            print("\x1b[H\x1b[J" + "\n".join(tx), flush=True)
        return k

    def reintentar_infra(self, its):
        for it in its:
            if it["estado"] == "infra" and it["intentos"] < self.cfg["reintentos_infra"] and not self.parando:
                if it["local_clase"] == "infra": self.set(it["clave"], "preparada", "reintento local tras fallo de infraestructura")
                else: self.set(it["clave"], "local_hallazgo" if it["local_clase"] in ("a_triar", "defecto_demostrado") else "local_ok", "reintento de envio tras fallo de infraestructura", intentos=it["intentos"] + 1)

    def sondear(self, lid, forzar=False):
        """Consulta GitHub por los grupos vivos (como mucho cada poll_s). False si GitHub no responde."""
        if not forzar and time.time() - self._ultimo_sondeo < self.cfg["poll_s"]: return True
        self._ultimo_sondeo = time.time()
        for it in [self.item(i["clave"]) for i in self.items(lid) if self.item(i["clave"])["estado"] in self.VIVOS]:
            r = self.reconciliar(it)
            if r and str(r).startswith("gh:"): self.log(f"GitHub no responde ({r[3:60]}); se reintenta"); return False
        return True

    def cerrar_lote(self, lid):
        for it in self.items(lid): self.cerrar_propuestas(self.item(it["clave"]))
        its = self.items(lid)
        cerrado = all(i["estado"] in ESTADOS_FINALES for i in its)
        resumen = {}; [resumen.__setitem__(i["estado"], resumen.get(i["estado"], 0) + 1) for i in its]
        self.c.execute("UPDATE lotes SET estado=?,fin=?,resumen=? WHERE id=?", ("cerrado" if cerrado else "en_curso", self.q.now() if cerrado else None, json.dumps(resumen), lid)); self.c.commit()
        try:
            import qa_triaje; n, _ = qa_triaje.encolar(self.q, self.c)  # el analisis GPT va a la cola del worker: EJECUTAR no lo espera
            if n: self.log(f"{n} causa(s) de fallo encoladas para analisis GPT (no bloquea)")
        except Exception as e: self.log(f"Encolado de analisis omitido ({str(e)[:100]})")
        self.panel(lid)
        self.log(f"Lote #{lid}: {resumen}" + ("" if cerrado else "  (quedan trabajos abiertos: vuelve a pulsar el BAT para reanudar)") + (f"  [{self.parando}]" if self.parando else ""))
        (self.dir / "ultimo.json").write_text(json.dumps({"lote": lid, "fecha": self.q.now(), "cerrado": cerrado, "resumen": resumen}), encoding="utf-8")
        return cerrado

    def arrancar_ciclo(self, gh_ok):
        """Hilo del flujo Claude -> GPT -> PR -> CI -> revision (qa_pr.Ciclo). Limites propios (config `flujo`), independientes de los 3 grupos de Actions.
        Un solo hilo y una conexion propia; si EJECUTAR se para, termina tras su paso en curso y todo queda en estado.db."""
        import threading, qa_pr
        cfg = qa_pr.flujo(self.q)
        if not (gh_ok and cfg["activo"] and hasattr(self.gh, "prs_abiertas")) or getattr(self, "_hilo_ciclo", None): return
        def bucle():
            c = self.q.db(); c.execute("PRAGMA busy_timeout=180000"); ciclo = qa_pr.Ciclo(self.q, self.gh, self.runner, self.log)
            while not self.parando:
                try: ciclo.paso(c)
                except GhAuthError as e: self.log(f"Flujo PR: GitHub rechaza el token ({str(e)[:80]})"); return
                except Exception as e: self.log(f"Flujo PR: paso omitido ({type(e).__name__}: {str(e)[:120]}); se reintenta")
                fin = time.time() + cfg["ciclo_s"]
                while time.time() < fin and not self.parando: time.sleep(1)
        self._hilo_ciclo = threading.Thread(target=bucle, name="flujo-pr", daemon=True); self._hilo_ciclo.start()

    def ejecutar(self):
        """Bucle continuo: valida en local (concurrencia_local, independiente de la remota), mantiene hasta 3 grupos en Actions, recoge resultados,
        envia el siguiente y abre lotes nuevos mientras haya trabajo. Con `continuo`, sin trabajo espera propuestas nuevas; solo Q/Ctrl+C/cierre lo detiene.
        Parar = dejar de lanzar grupos: los runs vivos se registran y se recogen en la siguiente apertura."""
        q = self.q; t_fin = time.time() + self.cfg["max_horas"] * 3600 if self.cfg["max_horas"] else float("inf"); cap = max(1, min(self.MAX_GRUPOS, int(self.cfg["concurrencia"])))
        try: self.gh.ok(); gh_ok = True
        except GhAuthError as e: gh_ok = False; self.log(f"GitHub RECHAZA el token ({str(e)[:80]}): ejecuta `gh auth login` (o `gh auth refresh -s repo`). Se valida en local; los envios quedan para el siguiente clic")
        except (GhError, OSError) as e: gh_ok = False; self.log(f"GitHub no disponible ({str(e)[:80]}): se valida en local y se reintenta el envio en el siguiente clic")
        try:  # Via A: contratos masivos locales (reutiliza el resultado si no cambian SHA ni contratos); un fallo aqui no bloquea la Via B
            q.git("fetch", "origin", "main", "--quiet", check=False)
            import qa_viaa; qa_viaa.ejecutar(self.c, q, q.ROOT, out=self.log)
        except Exception as e: self.log(f"Via A: fallo de infraestructura ({str(e)[:120]}); se continua con los tests")
        lid = self.abrir_lote()
        self.arrancar_ciclo(gh_ok)
        if gh_ok: self.sondear(lid, forzar=True)  # recuperar lo enviado en ejecuciones anteriores (run ids existentes) antes de lanzar nada
        ult_idle = 0; cerrado = None
        while True:
            self.tecla()
            if self.parando:  # una pasada final para recoger lo ya terminado; los runs vivos NO se cancelan ni se esperan
                if gh_ok: self.sondear(lid, forzar=True)
                break
            its = [self.item(i["clave"]) for i in self.items(lid)]
            if gh_ok:
                self.reintentar_infra(its)
                if not self.sondear(lid): gh_ok = False
                its = [self.item(i["clave"]) for i in self.items(lid)]
                libres = cap - sum(1 for i in its if i["estado"] in self.VIVOS)
                for it in [i for i in its if i["estado"] in ENVIABLES][:max(0, libres)]:
                    if self.parando: break
                    self.enviar(it)
                its = [self.item(i["clave"]) for i in self.items(lid)]
            listos = sum(1 for i in its if i["estado"] in ENVIABLES)
            por_validar = [i for i in its if i["estado"] in ("preparada", "validacion_local") or (i["estado"] in REINTENTABLES and not i["local_log"])]
            # con GitHub activo se valida de uno en uno y solo mientras no haya ya grupos de sobra esperando hueco (no se agota el PC validando de mas)
            hueco = 10**6 if not gh_ok else max(0, self.cfg["concurrencia_local"] * cap - listos) if listos >= cap else self.cfg["concurrencia_local"]
            for it in por_validar[:hueco]:
                if self.parando: break
                self.validar_local(it)
            if por_validar[:hueco] and not self.parando:
                self.panel(lid)
                if gh_ok: continue
            its = [self.item(i["clave"]) for i in self.items(lid)]
            self.panel(lid)
            pendientes = [i for i in its if i["estado"] in self.VIVOS + ENVIABLES + ("preparada", "validacion_local")]
            if not pendientes or not gh_ok:
                if not gh_ok or self.parando or time.time() > t_fin: break
                self.c.commit()  # sin transaccion abierta mientras espera: si no, bloquea la escritura del servicio ('database is locked')
                if lid != cerrado: self.cerrar_lote(lid); cerrado = lid  # lote agotado: se cierra una vez y se abre el siguiente con lo preparado desde entonces
                if self.hay_nuevo(): lid = self.abrir_lote(); cerrado = None; self.esperar(2); continue
                if not self.cfg.get("continuo"): break
                self.c.commit()
                if time.time() - ult_idle > 600: self.log("Sin trabajo pendiente: esperando propuestas nuevas del worker (Q para salir)"); ult_idle = time.time()
                self.esperar(self.cfg["espera_ociosa_s"]); continue
            if time.time() > t_fin: break
            self.esperar(self.cfg["poll_s"])
        self.cerrar_lote(lid)
        h = getattr(self, "_hilo_ciclo", None)
        if h and self.parando: h.join(timeout=20)  # deja terminar el paso en curso (todo ya esta en estado.db); no cancela nada en GitHub
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


def instalar_parada(lo):
    """Ctrl+C, cierre de consola y Q solo DEJAN de lanzar grupos nuevos; nunca cancelan runs de GitHub."""
    import signal
    signal.signal(signal.SIGINT, lambda *a: lo.pedir_parada("Ctrl+C"))
    try: signal.signal(signal.SIGBREAK, lambda *a: lo.pedir_parada("cierre de ventana"))
    except (AttributeError, ValueError): pass
    if os.name == "nt":
        try:
            import ctypes
            H = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_uint)
            def al_cerrar(t):
                if t not in (0, 1, 2, 5, 6): return 0
                lo.pedir_parada("cierre de ventana" if t != 0 else "Ctrl+C")
                if t in (2, 5, 6): time.sleep(8)  # margen para guardar estado antes de que Windows mate el proceso
                return 1
            lo._h = H(al_cerrar)
            ctypes.windll.kernel32.SetConsoleCtrlHandler(lo._h, True)
        except Exception: pass


def salida_inmediata():
    """Redirigido a fichero, print va con buffer de bloque: el log queda vacio minutos aunque el lote trabaje. Linea a linea siempre."""
    for f in (sys.stdout, sys.stderr):
        try: f.reconfigure(line_buffering=True, errors="replace")
        except Exception: pass


def main(q, a=None):
    salida_inmediata()
    with LoteLock(q):
        lo = Lote(q, cfg={"panel": sys.stdout.isatty(), "limite": getattr(a, "limite", None), "continuo": bool(getattr(a, "continuo", False)), "max_horas": 0 if getattr(a, "continuo", False) else 8}); lo.interactivo = sys.stdin.isatty()
        instalar_parada(lo); return lo.ejecutar()


def bloque_flujo(q, c):
    """Metricas del flujo Claude -> GPT -> PR (consumo medido, decisiones, PR activas/legado, revision e integracion)."""
    import qa_claude, qa_pr
    cfg = qa_pr.flujo(q); n = lambda sql, *a: c.execute(sql, a).fetchone()[0]
    dec = dict(c.execute("SELECT COALESCE(decision,'sin decidir'),COUNT(*) FROM triaje GROUP BY 1").fetchall())
    ig = dict(c.execute("SELECT integracion,COUNT(*) FROM triaje WHERE pr_nueva=1 AND integracion IS NOT NULL GROUP BY 1").fetchall())
    cl = qa_claude.resumen_consumo(c)
    try: ci = json.loads((q.STATE / "lote" / "ciclo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError): ci = {}
    fallos = dict(c.execute("SELECT pr_estado,COUNT(*) FROM triaje WHERE pr_estado IN ('test_no_fiable','no_reproduce','validacion_fallida','sin_test','parche_no_encaja','conflicto_main','descartada') GROUP BY 1").fetchall())
    return ["Flujo Claude -> GPT -> PR (Claude decide, GPT desarrolla, Claude revisa):",
            f"  - Decisiones de Claude: " + (", ".join(f"{k} {v}" for k, v in sorted(dec.items(), key=lambda x: -x[1])) or "(ninguna)"),
            f"  - Desarrollo GPT: en cola {n('SELECT COUNT(*) FROM jobs WHERE tipo=? AND clave LIKE ? AND estado IN (?,?)', 'T', 'D:%', 'pendiente', 'en_curso')} | intentos usados {n('SELECT COALESCE(SUM(intentos_dev),0) FROM triaje')} | sin PR por validacion: " + (", ".join(f"{k} {v}" for k, v in fallos.items()) or "ninguno"),
            f"  - PR nuevas activas: {n('SELECT COUNT(*) FROM triaje WHERE pr_nueva=1 AND pr_estado=?', 'pr_abierta')}/{cfg['max_pr_activas']} | PR antiguas (legado) abiertas: {ci.get('pr_legado', '?')} | integradas {n('SELECT COUNT(*) FROM triaje WHERE pr_estado=?', 'integrada')}",
            f"  - Revision de Claude / integracion ({cfg['integracion']['modo']}): " + (", ".join(f"{k} {v}" for k, v in ig.items()) or "(sin PR revisadas)") + f" | calibracion {ig.get('integrada_acierto', 0)}/{cfg['integracion']['calibracion_min']}",
            f"  - Claude: {cl['llamadas']} consultas ({cl['ok']} ok), {cl['usd']} USD, {cl['tok_entrada']} tok entrada / {cl['tok_salida']} salida, {cl['seg_medio']} s medios | {qa_claude.config(q)['modelo']}"]


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
             f"  - Validados en local (aptos para Actions): {li('local_ok')}  (se validan al pulsar EJECUTAR; hasta entonces estan en 'Escritos, sin ejecutar')",
             f"  - Defectos de producto demostrados: {li('defecto_demostrado')}  (el test falla por el defecto descrito: es un hallazgo, no un fallo)",
             f"  - Posible defecto, a triar (exploratorias que fallan): {li('a_triar')}",
             f"  - Fallo del propio test: {li('fallo_test')}",
             f"  - Enviados a Actions: {li('enviado', 'actions_pendiente', 'actions_ejecutando', 'actions_ok', 'actions_fallida')}  "
             f"(en cola {li('enviado', 'actions_pendiente')}, ejecutandose {li('actions_ejecutando')}, aprobados {li('actions_ok')}, fallidos {li('actions_fallida')})",
             f"  - Errores de infraestructura: {li('infra')}  | requieren revision humana: {li('revision_humana')}"]
    try:
        n = lambda sql, *a: c.execute(sql, a).fetchone()[0]
        gen = n("SELECT COUNT(*) FROM propuestas"); an_pend = n("SELECT COUNT(*) FROM jobs WHERE tipo='T' AND estado IN ('pendiente','en_curso')")
        prs = dict(c.execute("SELECT COALESCE(pr_estado,''),COUNT(*) FROM triaje GROUP BY 1").fetchall())
        lines += [f"  - Propuestas generadas (todas): {gen}  (no son archivos ni aserciones: una propuesta = un test escrito por GPT)",
                  f"  - Tests invalidos (no ejecutables): {n('SELECT COUNT(*) FROM propuestas WHERE estado=?', 'invalida')} propuestas | descartadas por duplicado/ruido: {n('SELECT COUNT(*) FROM propuestas WHERE estado=?', 'rechazada')}",
                  "Analisis GPT y PR:",
                  f"  - Analisis GPT pendientes: {an_pend} | terminados: {n('SELECT COUNT(*) FROM jobs WHERE tipo=? AND estado=?', 'T', 'hecho')} | causas triadas: {n('SELECT COUNT(*) FROM triaje')} (con parche propuesto {n('SELECT COUNT(*) FROM triaje WHERE parche IS NOT NULL')})",
                  f"  - PR creadas por QA GPT: {prs.get('pr_abierta', 0) + prs.get('pr_borrador', 0)} (listas para revisar {prs.get('pr_abierta', 0)} | borrador con comprobaciones pendientes {prs.get('pr_borrador', 0)}) | parche no encaja: {prs.get('parche_no_encaja', 0)} | sin PR todavia: {prs.get('', 0)}"]
        lines += bloque_flujo(q, c)
    except Exception: pass
    try: import qa_viaa; lines += qa_viaa.bloque_estado(q, c)
    except Exception: pass
    ul = c.execute("SELECT id,inicio,fin,estado,resumen FROM lotes ORDER BY id DESC LIMIT 1").fetchone()
    lines.append(f"Ultimo lote: {('#' + str(ul['id']) + ' ' + ul['inicio'] + ' (' + ul['estado'] + ')') if ul else '(ninguno)'}")
    ue = c.execute("SELECT rama,sha,runs FROM lote_items WHERE runs LIKE '%\"id\"%' ORDER BY actualizado DESC LIMIT 1").fetchone()
    if ue: rid = next(iter(json.loads(ue["runs"]).values()))["id"]; lines.append(f"Ultima ejecucion en Actions: {ue['rama']} / {ue['sha'][:8]} / run {rid}")
    for r in c.execute("SELECT rama,sha,estado,detalle FROM lote_items WHERE estado IN ('defecto_demostrado','a_triar','revision_humana','infra','fallo_test','actions_fallida') ORDER BY actualizado DESC LIMIT 8"):
        lines.append(f"    {r['estado']:<19} {r['rama'].replace('gpt-qa/', '')}@{r['sha'][:8]}: {(r['detalle'] or '')[:100]}")
    sig = c.execute("SELECT id FROM propuestas WHERE estado IN ('preparada','aprobada') ORDER BY id LIMIT 1").fetchone()
    sig_lote = c.execute("SELECT rama FROM lote_items WHERE estado IN ('preparada','validacion_local','local_ok','infra') ORDER BY rama LIMIT 1").fetchone()
    lines.append(f"Proximo pendiente: {('propuesta #' + str(sig[0])) if sig else (sig_lote['rama'] + ' (ya en lote abierto)' if sig_lote else '(ninguno)')}")
    return lines
