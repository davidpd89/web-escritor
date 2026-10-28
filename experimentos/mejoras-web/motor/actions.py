"""actions: EJECUTAR-ACTIONS-MEJORAS-WEB.bat. Consume los expedientes `preparado`, los valida en local (worktree separado, sin publicar), los deja en una
COLA PERSISTENTE (rama@sha, tests, resultados) y, SOLO por esta accion manual, los envia a un workflow dedicado `workflow_dispatch` con un maximo
configurable de grupos simultaneos (3). Recoge los resultados (runs existentes, artefacto, log), los clasifica y nunca duplica un envio por rama+SHA.

PROCEDENCIA: scripts/qa-gpt/qa_lote.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, blob 644aa2884fa672f88d28f7ea67e58b62358d63dd. Reutilizado (adaptado):
- `run_cmd` / `matar_arbol` (test local abortable, arbol de procesos), `ServidorEstatico` (de qa_cobertura.py, blob ea94e2ebf1c07123ba2a1ddcb06dbfb6e91c6a2e),
  `entorno_url`/`puerto_libre`/`ejecutar_test`, `precheck` (sintaxis sin ejecutar), `registrar_test`, `set` con reintento ante 'database is locked',
- `Gh.runs_grupo/resultados/log_failed/run` (recuperacion de runs y artefactos), `enviar` (push del sha exacto + dispatch + localizar el run),
  `reconciliar` + `veredicto_remoto` (el artefacto manda sobre el color del job), `sondear`, `reintentar_infra`, `ejecutar` (bucle con tope de grupos, parada
  que NO cancela runs, reanudacion), `instalar_parada` (Ctrl+C / cierre de consola) y `LoteLock` (aqui mw.Lock("actions")).
EXCLUIDO a proposito (el QA lo hace y el laboratorio NO): `pr_auto`, `pr_merge`, `pr_cerrar --delete-branch`, `pr_actualizar`, `rerun_fallidos`, la
escritura sobre ramas gpt-qa/*, el flujo `Ciclo` (fusion automatica), Via A, qa_triaje y toda lectura/escritura de estado.db del QA.
Cambios de diseno: la clave de cola es rama@sha; el run-name del workflow lleva `sha #intento`, de modo que un reintento por infraestructura es una
accion explicita (`reintentar-infra`) y nunca un reenvio silencioso.
"""
import datetime as dt, json, os, re, signal, socket, sqlite3, subprocess, sys, time
from pathlib import Path

import clases, mw, parches

AUTORIZADO = False  # solo main() lo activa (accion EJECUTAR). Con False, ni push ni dispatch: el servicio de INICIAR no puede enviar nada.
VIVOS = ("enviado", "actions_pendiente", "actions_ejecutando")
ENVIABLES = ("validado",)
FINALES = {"fallo_local", "remoto_ok", "remoto_fallo_parche", "remoto_fallo_test", "remoto_infra", "revision_humana"}
EXP_DE_COLA = {"validado": "validado", "fallo_local": "fallo_local", "enviado": "en_actions", "actions_pendiente": "en_actions", "actions_ejecutando": "en_actions",
               "remoto_ok": "remoto_ok", "remoto_fallo_parche": "remoto_fallo", "remoto_fallo_test": "remoto_fallo", "remoto_infra": "remoto_infra", "revision_humana": "revision_humana"}
INFRA = clases.INFRA
ASERCION = clases.ASERCION
ABORTAR = None  # callable -> True cuando hay que soltar el test en curso (Q / Ctrl+C / cierre de ventana)
RC_ABORTADO = 130
SIN_ENTORNO_PUERTO = "SIN_ENTORNO: ningun puerto libre; se valida en Actions"


class GhError(RuntimeError): pass
class GhAuthError(GhError): """Token sin sesion o sin permisos: no es transitorio, reintentar no sirve."""
class NoAutorizado(RuntimeError): """Se intento publicar/despachar fuera de la accion manual EJECUTAR."""


# ---------- procesos locales ----------
def matar(p):
    """El test y todo lo que lanzo (node, servidores, navegadores): ninguno queda huerfano."""
    try: mw.matar_arbol(p.pid)
    except Exception: p.kill()


def run_cmd(args, cwd, env=None, timeout=300):
    """Ejecuta un comando local; devuelve (rc, salida). Se interrumpe en ~1 s si ABORTAR() pide parar (rc 130)."""
    # UTF-8 como en CI (Linux): en Windows open() sin encoding usa cp1252 y los tests fallaban con 'charmap' sin que el parche tuviera culpa
    p = mw.popen(args, cwd=cwd, env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", **(env or {})}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                 text=True, encoding="utf-8", errors="replace")
    fin = time.monotonic() + timeout
    while True:
        try:
            out, _ = p.communicate(timeout=1); return p.returncode, out or ""
        except subprocess.TimeoutExpired:
            if ABORTAR and ABORTAR():
                matar(p); p.communicate(); return RC_ABORTADO, "ABORTADO: parada solicitada durante la ejecucion"
            if time.monotonic() > fin:
                matar(p); out, _ = p.communicate()
                return 124, f"TimeoutExpired tras {timeout}s\n{(out or '')[-1500:]}"


class ServidorEstatico:
    """Servidor estatico en un hilo del propio proceso (literal de qa_cobertura.ServidorEstatico): sin http.server hijo que sobreviva si EJECUTAR muere."""
    def __init__(self, directorio, puerto=0): self.dir, self.puerto = str(directorio), puerto

    def __enter__(self):
        import functools, threading, http.server
        class Silencioso(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
        class Servidor(http.server.ThreadingHTTPServer):
            def handle_error(self, request, client_address):  # el navegador corta descargas al cerrar la pagina: no es un fallo
                if not isinstance(sys.exc_info()[1], (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)): super().handle_error(request, client_address)
        self.srv = Servidor(("127.0.0.1", self.puerto), functools.partial(Silencioso, directory=self.dir))
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, name="servidor-estatico", daemon=True).start()
        return self.srv.server_address[1]

    def __exit__(self, *a): self.srv.shutdown(); self.srv.server_close()


# ---------- GitHub (subconjunto SEGURO de qa_lote.Gh) ----------
class Gh:
    """Fachada de `gh`/git remoto; todo fallo de red/API sale como GhError (transitorio). Solo lectura de runs, push de mejoras-web/* y UN dispatch."""
    def __init__(self, q):
        self.q = q; self.repo = q.CFG["repo"]; self.wf = q.CFG["workflow_grupo"]

    def _gh(self, *a):
        r = self.q.run(["gh", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode:
            msg = (r.stderr or r.stdout).strip()[:300]
            raise (GhAuthError if re.search(r"HTTP 40[13]|Bad credentials|auth login|not logged|Resource not accessible|must have admin|requires.*scope", msg, re.I) else GhError)(msg)
        return r.stdout

    def ok(self): self._gh("api", "user", "--jq", ".login"); return True

    def remotos(self):
        """Ramas mejoras-web/* del remoto en UNA consulta."""
        if getattr(self, "_remotos", None) is None:
            r = self.q.run(["git", "ls-remote", "origin", f"refs/heads/{self.q.CFG['prefijo_rama']}*"], cwd=self.q.REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if r.returncode: raise GhError(r.stderr.strip()[:300])
            self._remotos = {ref.removeprefix("refs/heads/"): sha for sha, ref in (ln.split() for ln in r.stdout.splitlines() if len(ln.split()) == 2)}
        return self._remotos

    def remote_sha(self, rama): return self.remotos().get(rama)

    def push(self, sha, rama):
        if not AUTORIZADO: raise NoAutorizado("push solo desde la accion manual EJECUTAR")
        if not self.q.rama_permitida(rama): raise GhAuthError(f"push bloqueado: solo ramas {self.q.CFG['prefijo_rama']}* (no {rama})")
        r = self.q.run(["git", "push", "origin", f"{sha}:refs/heads/{rama}"], cwd=self.q.REPO, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode: raise GhError((r.stderr or r.stdout).strip()[:400])
        self.remotos()[rama] = sha

    def dispatch(self, sha, modo, tests, intento):
        """workflow_dispatch del workflow dedicado en la rama `workflow_ref`. UNICO punto del laboratorio que lanza Actions."""
        if not AUTORIZADO: raise NoAutorizado("dispatch solo desde la accion manual EJECUTAR")
        campos = {"sha": sha, "modo": modo, "tests": tests, "intento": str(intento)}
        self._gh("workflow", "run", self.wf, "-R", self.repo, "--ref", self.q.CFG["workflow_ref"], *[a for k, v in campos.items() for a in ("-f", f"{k}={v}")])

    def workflow_disponible(self):
        """El workflow dedicado existe en la rama `workflow_ref` (GitHub solo despacha lo que existe en el --ref). Mismo metodo que qa_lote.Gh.workflow_ref del QA.
        -> None si esta disponible; texto del problema si no (rama borrada tras fusionar una PR, workflow ausente...)."""
        ref = self.q.CFG["workflow_ref"]
        try: self._gh("api", f"repos/{self.repo}/contents/.github/workflows/{self.wf}?ref={ref}", "--silent")
        except GhAuthError: raise
        except GhError as e:
            return f"{self.wf} no existe en la rama '{ref}' (config.json -> workflow_ref): {str(e)[:120]}. Pon en workflow_ref una rama del remoto que contenga el workflow (p. ej. {self.q.CFG['rama_base']})."
        try: self._gh("api", f"repos/{self.repo}/contents/.github/workflows/{self.wf}", "--silent")  # sin ref = rama POR DEFECTO
        except GhAuthError: raise
        except GhError as e:
            return (f"{self.wf} no existe en la rama por defecto del repositorio y GitHub responde 404 al despachar ('not found on the default branch'): "
                    f"fusiona primero el workflow en main. Detalle: {str(e)[:100]}")
        return None

    def runs_grupo(self, sha, intento=1):
        """Runs del workflow dedicado para ESTE commit e intento (el run-name lleva `sha #intento`)."""
        rs = json.loads(self._gh("run", "list", "-R", self.repo, "--workflow", self.wf, "--limit", "100", "--json", "databaseId,headSha,status,conclusion,event,createdAt,url,displayTitle") or "[]")
        return [r for r in rs if f"{sha} #{intento}" in (r.get("displayTitle") or "")]

    def run(self, rid):
        return json.loads(self._gh("run", "view", str(rid), "-R", self.repo, "--json", "databaseId,status,conclusion,headSha,url"))

    def resultados(self, rid):
        """resultados.json del artefacto mejoras-web-resultados; None si el run no lo subio. Un error de red se propaga."""
        import shutil, tempfile
        d = Path(tempfile.mkdtemp(prefix="mw-res-", dir=self.q.STATE))
        try:
            try: self._gh("run", "download", str(rid), "-R", self.repo, "-n", "mejoras-web-resultados", "-D", str(d))
            except GhAuthError: raise
            except GhError as e:
                if re.search(r"no valid artifacts|not found|no artifact", str(e), re.I): return None
                raise
            f = next(d.rglob("resultados.json"), None)
            return json.loads(f.read_text(encoding="utf-8")) if f else None
        finally: shutil.rmtree(d, ignore_errors=True)

    def log_failed(self, rid):
        """Log de los jobs fallidos de un run, o "" si Actions no lo ofrece (nunca el texto de un error). Logica del QA (cae a la API de logs por job)."""
        try: log = self._gh("run", "view", str(rid), "-R", self.repo, "--log-failed")
        except GhAuthError: raise
        except GhError: log = ""
        if log.strip(): return log
        try: jobs = json.loads(self._gh("run", "view", str(rid), "-R", self.repo, "--json", "jobs") or "{}").get("jobs") or []
        except GhAuthError: raise
        except (GhError, ValueError): return ""
        partes = []
        for j in [j for j in jobs if j.get("conclusion") in ("failure", "timed_out", "cancelled")][:5]:
            pasos = ", ".join(s.get("name") or "?" for s in j.get("steps") or [] if s.get("conclusion") in ("failure", "timed_out", "cancelled")) or "?"
            try: txt = self._gh("api", f"repos/{self.repo}/actions/jobs/{j['databaseId']}/logs")
            except GhAuthError: raise
            except (GhError, KeyError): txt = ""
            partes.append(f"== job {j.get('name')} ({j.get('conclusion')}); pasos fallidos: {pasos}\n{txt[-4000:]}")
        return "\n".join(partes)


def slug(clave): return re.sub(r"\W", "_", clave)


class Ejecutor:
    MAX_GRUPOS = 3

    def __init__(self, q, gh=None, runner=run_cmd, sleep=time.sleep, out=print, cfg=None):
        self.q, self.gh, self.runner, self.sleep, self.out = q, gh or Gh(q), runner, sleep, out
        self.cfg = {**q.CFG.get("actions", {}), **(cfg or {})}
        self.dir = q.STATE / "actions"; self.dir.mkdir(parents=True, exist_ok=True)
        self.c = q.db(); self.c.execute("PRAGMA busy_timeout=180000")
        global ABORTAR
        ABORTAR = lambda: bool(self.parando) or q.flag("stop_actions")
        self.parando = None; self.interactivo = False; self._ultimo_sondeo = 0

    # ---------- persistencia ----------
    def log(self, msg):
        linea = f"[{dt.datetime.now():%H:%M:%S}] {msg}"; self.out(linea)
        try:
            f = self.dir / "ejecutar.log"
            if f.exists() and f.stat().st_size > 20e6: f.replace(f.with_suffix(".log.1"))
            with f.open("a", encoding="utf-8") as fh: fh.write(f"{dt.date.today()} {linea}\n")
        except OSError: pass

    def _retry(self, fn):
        for intento in range(6):  # el servicio escribe en la misma base: un bloqueo transitorio no debe tumbar el lote
            try: return fn()
            except sqlite3.OperationalError:
                self.c.rollback()
                if intento == 5: raise
                self.sleep(5)

    def set(self, clave, estado, detalle=None, **extra):
        cols = {"estado": estado, "actualizado": self.q.now(), **extra}
        if detalle is not None: cols["detalle"] = detalle[:600]
        def f():
            self.c.execute(f"UPDATE cola SET {','.join(k + '=?' for k in cols)} WHERE clave=?", (*cols.values(), clave))
            it = self.c.execute("SELECT exp FROM cola WHERE clave=?", (clave,)).fetchone()
            if it and estado in EXP_DE_COLA:
                self.c.execute("UPDATE expedientes SET estado=?, actualizado=?, motivo=? WHERE id=?", (EXP_DE_COLA[estado], self.q.now(), (detalle or "")[:400], it["exp"]))
                self.c.execute("INSERT INTO historial VALUES(?,?,?,?)", (it["exp"], self.q.now(), EXP_DE_COLA[estado], (detalle or "")[:300]))
            self.c.commit()
        self._retry(f)
        self.log(f"{clave.split('@')[0].replace(self.q.CFG['prefijo_rama'], '')}: {estado}" + (f" - {detalle[:140]}" if detalle else ""))

    def item(self, clave): return self.c.execute("SELECT * FROM cola WHERE clave=?", (clave,)).fetchone()
    def items(self): return self.c.execute("SELECT * FROM cola ORDER BY rama").fetchall()

    def registrar_test(self, clave, fuente, ruta, clase, rc, run_id=None):
        self._retry(lambda: (self.c.execute("INSERT OR REPLACE INTO cola_tests VALUES(?,?,?,?,?,?,?)", (clave, fuente, ruta, clase, rc, run_id, self.q.now())), self.c.commit()))

    # ---------- captura y validacion local ----------
    def capturar(self):
        """Expedientes `preparado` sin item en la cola. El clic de EJECUTAR es la autorizacion. -> n nuevos"""
        n = 0
        tope = int(self.cfg.get("limite") or 10**6)
        for e in self.c.execute("SELECT * FROM expedientes WHERE estado='preparado' ORDER BY rowid").fetchall():
            if n >= tope: break
            if self.c.execute("SELECT 1 FROM cola WHERE exp=? AND estado NOT IN ('fallo_local')", (e["id"],)).fetchone(): continue
            n += 1; self.validar_local(e["id"])
        return n

    def comandos(self, prop):
        return [(t["ruta"], [sys.executable if t["exe"] == "python" else "node", t["ruta"]]) for t in prop["pruebas"]]

    def precheck(self, tmp, ruta):
        """Sintaxis sin ejecutar el test: `compile` para Python, `node --check` para JS. (0, '') si parsea."""
        try:
            if ruta.endswith(".py"): compile((tmp / ruta).read_text(encoding="utf-8"), ruta, "exec"); return 0, ""
            if ruta.endswith((".mjs", ".js", ".cjs")):
                r = self.runner(["node", "--check", ruta], tmp, {}, 60)
                return (0, "") if r[0] == 0 else r
        except SyntaxError as e: return 1, f"SyntaxError: {e}"
        return 0, ""

    def puerto_libre(self):
        base = int(self.cfg.get("puerto_estatico", 4273))
        for puerto in range(base, base + 40):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", puerto)) != 0: return puerto
        return None

    @staticmethod
    def entorno_url(fichero, puerto):
        """Variables `process.env.X` del test que contienen la URL base (X termina en URL/ORIGIN/BASE) apuntadas al puerto propio."""
        txt = fichero.read_text(encoding="utf-8", errors="replace")
        return {n: f"http://127.0.0.1:{puerto}" for n in set(re.findall(r"process\.env\.([A-Z][A-Z0-9_]*(?:URL|ORIGIN|BASE))", txt))}

    def enlazar_node_modules(self, tmp):
        nm = Path(self.cfg.get("node_modules") or self.q.STATE / "node_modules")
        dst = tmp / "node_modules"
        if not nm.is_dir() or dst.exists(): return
        try:
            if os.name == "nt":
                import _winapi; _winapi.CreateJunction(str(nm), str(dst))  # sin `cmd /c mklink`: un proceso y una ventana menos
            else: dst.symlink_to(nm, target_is_directory=True)
        except Exception: pass

    def ejecutar_test(self, tmp, ruta, cmd):
        texto = (tmp / ruta).read_text(encoding="utf-8", errors="replace")
        if cmd[0] != "node" or ("playwright" not in texto and not self.entorno_url(tmp / ruta, 0)): return self.runner(cmd, tmp, {}, self.cfg["timeout_test_s"])
        puerto = self.puerto_libre()
        if puerto is None: return 0, SIN_ENTORNO_PUERTO
        env = self.entorno_url(tmp / ruta, puerto)  # el test apunta a NUESTRO servidor, nunca a uno ajeno
        env.setdefault("SITE_ORIGIN", f"http://127.0.0.1:{puerto}")
        srv = ServidorEstatico(tmp, puerto)
        try: srv.__enter__()
        except OSError: return 0, "SIN_ENTORNO: el puerto se ocupo antes de servir; se valida en Actions"
        try: return self.runner(cmd, tmp, env, self.cfg["timeout_test_s"])
        finally: srv.__exit__()

    def en_base_falla(self, e, prop, base):
        """El test de aceptacion debe FALLAR sin el cambio (si pasa en la base, no demuestra nada). -> (ok, detalle). Worktree propio en la base."""
        wt = self.q.STATE / "wt" / (e["id"] + "-base"); parches.limpiar_wt(wt)
        try:
            self.q.git("worktree", "add", "--detach", str(wt), base)
            for t in prop["pruebas"]:
                p = wt / t["ruta"]; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t["contenido"], encoding="utf-8", newline="")
            self.enlazar_node_modules(wt)
            for ruta, cmd in self.comandos(prop):
                rc, out = self.ejecutar_test(wt, ruta, cmd)
                cl = clases.clasificar_salida(rc, out)
                if cl == "sin_entorno": return True, "linea base no comprobable en este equipo (sin navegador); se confia en Actions"
                if cl == "ok": return False, f"{ruta} PASA sin el cambio: no demuestra la mejora"
                if cl != "hallazgo": return False, f"{ruta} no es ejecutable en la base ({cl}): {out[-200:]}"
            return True, "los tests fallan en la base (demuestran la mejora)"
        finally: parches.limpiar_wt(wt)

    def validar_local(self, exp_id):
        """Construye la candidata (worktree + commit local, SIN publicar), ejecuta los tests de aceptacion y deja el item en la cola."""
        q = self.q
        e = self.c.execute("SELECT * FROM expedientes WHERE id=?", (exp_id,)).fetchone()
        if not e["parche"]: return q.set_estado(self.c, exp_id, "fallo_local", "el expediente no tiene parche guardado")
        prop = json.loads(e["parche"])
        q.set_estado(self.c, exp_id, "validando", "validacion local en worktree separado")
        try: wt, sha, base, tocados = parches.construir_candidata(e)
        except (ValueError, RuntimeError) as err:
            return q.set_estado(self.c, exp_id, "fallo_local", f"no se pudo construir la candidata: {str(err)[:300]}")
        clave = f"{e['rama'] or q.CFG['prefijo_rama'] + exp_id.lower()}@{sha[:12]}"
        rama = e["rama"] or q.CFG["prefijo_rama"] + exp_id.lower()
        self.c.execute("UPDATE expedientes SET rama=?, base_sha=?, sha=? WHERE id=?", (rama, base, sha, exp_id))
        self.c.execute("INSERT OR IGNORE INTO cola(clave,exp,rama,sha,estado,tests,runs,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?)",
                       (clave, exp_id, rama, sha, "validando", json.dumps([t["ruta"] for t in prop["pruebas"]]), "{}", q.now(), q.now())); self.c.commit()
        try:
            self.enlazar_node_modules(wt)
            ok_base, det_base = self.en_base_falla(e, prop, base)
            partes, cls = [f"linea base: {det_base}"], []
            if not ok_base:
                return self.set(clave, "fallo_local", det_base, local_clase="fallo_test")
            for ruta, cmd in self.comandos(prop):
                rc, salida = self.precheck(wt, ruta)
                if rc == 0: rc, salida = self.ejecutar_test(wt, ruta, cmd)
                if rc == RC_ABORTADO and (self.parando or q.flag("stop_actions")):  # no es un fallo del test: se suelta y se revalida al reabrir
                    return self.set(clave, "validando", f"validacion interrumpida ({self.parando or 'stop'}); se reanuda al reabrir", intentos=(self.item(clave)["intentos"] or 0))
                cl = clases.clasificar_salida(rc, salida); cls.append(cl); self.registrar_test(clave, "local", ruta, cl, rc)
                partes.append(f"### {' '.join(map(str, cmd[-2:]))} -> exit {rc} [{cl}]\n{salida[-6000:]}")
            logp = self.dir / f"{slug(clave)}.log"
            logp.write_text(f"rama {rama}\nsha {sha}\nbase {base}\nfecha {q.now()}\n\n" + "\n".join(partes), encoding="utf-8")
            veredicto = clases.estado_remoto(cls)
            upd = dict(local_clase=veredicto, local_log=str(logp))
            if veredicto in ("valido", "sin_entorno"):
                self.set(clave, "validado", "tests locales correctos" + (" (parte sin navegador: se valida en Actions)" if veredicto == "sin_entorno" else "") + f"; {det_base}", **upd)
            elif veredicto == "infra":
                self.set(clave, "fallo_local", "fallo de entorno al ejecutar localmente (reintentable con validar)", **upd)
            else:
                self.set(clave, "fallo_local", {"fallo_parche": "el test de aceptacion FALLA con el cambio aplicado", "fallo_test": "test invalido o no ejecutable"}[veredicto], **upd)
        finally: parches.limpiar_wt(wt)

    # ---------- GitHub: enviar ----------
    def enviados_hoy(self):
        return self.c.execute("SELECT COUNT(*) FROM envios WHERE fecha=?", (self.q.today(),)).fetchone()[0]

    def hallar_run(self, sha, intento):
        return self.gh.runs_grupo(sha, intento)

    def enviar(self, it):
        """push del sha exacto a mejoras-web/<id> y UN workflow_dispatch. Antes busca un run existente de ese sha+intento (no duplica)."""
        clave, rama, sha = it["clave"], it["rama"], it["sha"]
        if not AUTORIZADO: raise NoAutorizado("enviar solo desde EJECUTAR")
        intento = it["remoto_intentos"] + 1
        despachado = False
        try:
            prev = self.hallar_run(sha, intento)  # primero lo que ya existe: un cierre entre dispatch y registro no duplica
            if not prev:
                if self.enviados_hoy() >= int(self.cfg.get("max_envios_dia", 12)):
                    return self.log(f"Tope diario de envios a Actions alcanzado ({self.cfg.get('max_envios_dia', 12)}): {clave.split('@')[0]} espera a manana")
                if self.gh.remote_sha(rama) != sha: self.gh.push(sha, rama)
                tests = " ".join(f"{'node' if r.endswith(('.mjs', '.js')) else 'python'}:{r}" for r in json.loads(it["tests"]))
                self.c.execute("UPDATE cola SET enviado=?, actualizado=? WHERE clave=?", (self.q.now(), self.q.now(), clave)); self.c.commit()
                despachado = True  # desde aqui un fallo NO vuelve a `validado`: el dispatch pudo haber salido; se busca su run, no se reenvia
                self.gh.dispatch(sha, "aceptacion", tests, intento)
                self.c.execute("INSERT INTO envios VALUES(?,?,?)", (self.q.today(), clave, None)); self.c.commit()
                for _ in range(12):
                    self.sleep(5); prev = self.hallar_run(sha, intento)
                    if prev: break
            runs = json.loads(it["runs"] or "{}")
            if prev: runs[str(intento)] = {"id": prev[0]["databaseId"], "url": prev[0]["url"]}
            self.set(clave, "actions_pendiente" if prev else "enviado", f"run {runs[str(intento)]['id']} (intento {intento})" if prev else "workflow lanzado, run por localizar", runs=json.dumps(runs))
        except NoAutorizado: raise
        except GhAuthError as e:
            self.set(clave, "enviado" if despachado else "revision_humana", f"GitHub rechaza el token/permisos ({str(e)[:120]}): `gh auth refresh -s repo,workflow` y pulsa de nuevo")
        except GhError as e:
            if not despachado and re.search(r"rejected|non-fast-forward|fetch first", str(e), re.I):  # la rama remota ya existe con otro historial: reintentar no sirve
                return self.set(clave, "revision_humana", f"push rechazado (la rama {rama} existe en GitHub con otro historial): {str(e)[:150]}")
            self.set(clave, "enviado" if despachado else "validado", f"GitHub no responde ({'run por localizar' if despachado else 'se reintenta'}): {str(e)[:150]}")
        except RuntimeError as e:
            self.set(clave, "enviado" if despachado else ("revision_humana" if "rejected" in str(e) or "non-fast" in str(e) else "validado"), f"push/dispatch: {str(e)[:200]}")

    def reconciliar(self, it):
        """Consulta GitHub y avanza el item; tambien recupera `enviado` sin run id (cierre tras el dispatch). -> viva | fin | falta | gh:..."""
        clave, sha = it["clave"], it["sha"]; runs = json.loads(it["runs"] or "{}"); intento = it["remoto_intentos"] + 1
        try:
            if str(intento) not in runs:
                hit = self.hallar_run(sha, intento)
                if hit: runs[str(intento)] = {"id": hit[0]["databaseId"], "url": hit[0]["url"]}
            if str(intento) not in runs:
                if it["enviado"] and (dt.datetime.fromisoformat(self.q.now()) - dt.datetime.fromisoformat(it["enviado"])).total_seconds() > self.cfg["espera_run_min"] * 60:
                    self.set(clave, "revision_humana", f"el dispatch no creo ningun run en {self.cfg['espera_run_min']} min: revisa que {self.q.CFG['workflow_grupo']} exista en {self.q.CFG['workflow_ref']}")
                    return "fin"
                return "falta"
            r = self.gh.run(runs[str(intento)]["id"])
        except GhError as e: return f"gh:{e}"
        runs[str(intento)].update(status=r["status"], conclusion=r["conclusion"])
        if r["status"] != "completed":
            self.set(clave, "actions_ejecutando" if r["status"] == "in_progress" else "actions_pendiente", runs=json.dumps(runs)); return "viva"
        rid = r["databaseId"]
        try: res = self.gh.resultados(rid)
        except GhError as e: return f"gh:{e}"
        if res is not None:  # el artefacto manda: un job verde o rojo solo dice si el driver termino, no que encontro
            est, det = self.veredicto_remoto(it, res, rid)
            (self.dir / f"{slug(clave)}.actions.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            self.set(clave, est, f"run {rid}: {det}", runs=json.dumps(runs)); return "fin"
        try: log = self.gh.log_failed(rid) if r["conclusion"] != "success" else ""
        except GhError as e: return f"gh:{e}"
        logp = self.dir / f"{slug(clave)}.actions.log"; logp.write_text(f"run {rid} {r.get('url', '')}\nsha {sha}\n\n{log[-20000:]}", encoding="utf-8")
        if r["conclusion"] == "success": est, det = "remoto_infra", "run verde SIN resultados.json: no se da por valido"
        elif r["conclusion"] in ("cancelled", "timed_out", "startup_failure"): est, det = "remoto_infra", f"run {r['conclusion']}"
        elif ASERCION.search(log) and not INFRA.search(log): est, det = "remoto_fallo_parche", "asercion fallida en el log"
        else: est, det = "remoto_infra", "el run fallo antes de producir resultados (no atribuible al parche)"
        self.set(clave, est, f"run {rid}: {det} (log {logp.name})", runs=json.dumps(runs)); return "fin"

    def veredicto_remoto(self, it, res, run_id):
        """Estado final a partir de resultados.json del runner: invalido/infra/sin_entorno nunca son 'valido'; asercion fallida = fallo del parche."""
        cls = []
        for t in res.get("tests", []):
            self.registrar_test(it["clave"], "actions", t["ruta"], t["clase"], t["rc"], run_id); cls.append(t["clase"])
        v = clases.estado_remoto(cls)
        resumen = ", ".join(f"{n} {k}" for k, n in sorted(res.get("resumen", {}).items()))
        return {"valido": "remoto_ok", "fallo_parche": "remoto_fallo_parche", "fallo_test": "remoto_fallo_test", "infra": "remoto_infra", "sin_entorno": "remoto_infra"}[v], resumen

    # ---------- orquestacion ----------
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

    def conteo(self):
        its = self.items(); n = lambda *es: sum(1 for i in its if i["estado"] in es)
        return {"total": len(its), "validando": n("validando"), "validados": n("validado"), "enviados": n("enviado", "actions_pendiente"), "ejecutando": n("actions_ejecutando"),
                "ok": n("remoto_ok"), "fallo_parche": n("remoto_fallo_parche"), "fallo_test": n("remoto_fallo_test", "fallo_local"), "infra": n("remoto_infra"),
                "revision": n("revision_humana"), "grupos_remotos": n(*VIVOS), "limite": self.MAX_GRUPOS, "parando": self.parando, "fecha": self.q.now()}

    def panel(self):
        k = self.conteo()
        try: (self.dir / "ejecutor.json").write_text(json.dumps(k), encoding="utf-8")
        except OSError: pass
        if self.cfg.get("panel"):
            print("\x1b[H\x1b[J" + "\n".join([
                f"EJECUTAR-ACTIONS-MEJORAS-WEB  {dt.datetime.now():%H:%M:%S}   [Q] parar tras guardar  [Ctrl+C] parada controlada",
                f"  Grupos en GitHub ahora: {k['grupos_remotos']}/{k['limite']}   (cerrar esta ventana NO cancela los runs ya enviados)",
                f"  Validando {k['validando']} | listos para enviar {k['validados']} | enviados {k['enviados']} | ejecutando {k['ejecutando']}",
                f"  Terminados: valid. {k['ok']} | fallo del parche {k['fallo_parche']} | fallo del test/local {k['fallo_test']} | infraestructura {k['infra']} | revision humana {k['revision']}"
                + (f"\n  >>> {k['parando']}: no se lanzan grupos nuevos" if k["parando"] else "")]), flush=True)
        return k

    def sondear(self, forzar=False):
        """Consulta GitHub por los grupos vivos (como mucho cada poll_s). False si GitHub no responde."""
        if not forzar and time.time() - self._ultimo_sondeo < self.cfg["poll_s"]: return True
        self._ultimo_sondeo = time.time()
        for it in [i for i in self.items() if i["estado"] in VIVOS]:
            r = self.reconciliar(self.item(it["clave"]))
            if r and str(r).startswith("gh:"): self.log(f"GitHub no responde ({r[3:60]}); se reintenta"); return False
        return True

    def ejecutar(self):
        """Bucle: captura+valida (uno a la vez), mantiene hasta MAX_GRUPOS grupos en Actions, recoge resultados y, con `continuo`, espera expedientes nuevos.
        Parar = dejar de lanzar grupos: los runs vivos se registran y se recogen en la siguiente apertura."""
        q = self.q; cap = max(1, min(self.MAX_GRUPOS, int(self.cfg["concurrencia"])))
        try: self.gh.ok(); gh_ok = True
        except GhAuthError as e: gh_ok = False; self.log(f"GitHub RECHAZA el token ({str(e)[:80]}): `gh auth login`. Se valida en local; los envios quedan para el siguiente clic")
        except (GhError, OSError) as e: gh_ok = False; self.log(f"GitHub no disponible ({str(e)[:80]}): se valida en local y se reintenta el envio en el siguiente clic")
        if gh_ok and hasattr(self.gh, "workflow_disponible"):
            try: problema = self.gh.workflow_disponible()
            except GhError as e: problema = None; self.log(f"No se pudo comprobar el workflow ({str(e)[:80]}); se intenta igualmente")
            if problema:  # sin esto, cada dispatch fallaba con un 422 poco claro y los items se quedaban reintentando
                self.log("NO SE ENVIA NADA A ACTIONS: " + problema + " Se valida en local y lo validado queda en la cola."); gh_ok = False
        # reanudar: items que se quedaron validando (cierre a mitad) vuelven a validarse; los runs ya enviados se recuperan SIN reenviar
        for it in self.items():
            if it["estado"] == "validando": self.c.execute("UPDATE expedientes SET estado='preparado' WHERE id=? AND estado='validando'", (it["exp"],)); self.c.execute("DELETE FROM cola WHERE clave=?", (it["clave"],))
        self.c.commit()
        if gh_ok: self.sondear(forzar=True)
        ult_idle = 0
        while True:
            self.tecla()
            if self.parando or q.flag("stop_actions"):
                self.pedir_parada("stop")
                if gh_ok: self.sondear(forzar=True)  # una pasada final; los runs vivos NO se cancelan ni se esperan
                break
            if gh_ok and not self.sondear(): gh_ok = False
            nuevos = self.capturar() if not self.parando else 0
            its = self.items()
            if gh_ok:
                libres = cap - sum(1 for i in its if i["estado"] in VIVOS)
                for it in [i for i in its if i["estado"] in ENVIABLES][:max(0, libres)]:
                    if self.parando or q.flag("stop_actions"): break
                    self.enviar(self.item(it["clave"]))
            self.panel()
            its = self.items()
            tope_dia = self.enviados_hoy() >= int(self.cfg.get("max_envios_dia", 12))
            pendientes = [i for i in its if i["estado"] in VIVOS + (() if tope_dia else ENVIABLES)]  # con el tope diario agotado, lo enviable espera a manana (no es trabajo)
            if tope_dia and not self.parando and not pendientes and any(i["estado"] in ENVIABLES for i in its) and time.time() - ult_idle > 600:
                self.log(f"Tope diario de envios a Actions alcanzado ({self.cfg.get('max_envios_dia', 12)}): lo validado queda en cola para manana"); ult_idle = time.time()
            if nuevos or (pendientes and gh_ok):
                if pendientes and not nuevos: self.esperar(self.cfg["poll_s"])
                continue
            if not gh_ok or not self.cfg.get("continuo"): break
            if time.time() - ult_idle > 600: self.log("Sin trabajo pendiente: esperando expedientes preparados del investigador (Q para salir)"); ult_idle = time.time()
            self.esperar(self.cfg["espera_ociosa_s"])
        self.panel()
        self.log(f"Resumen: {self.conteo()}")
        return 0


def instalar_parada(lo):
    """Ctrl+C, cierre de consola y Q solo DEJAN de lanzar grupos nuevos; nunca cancelan runs de GitHub. (Literal de qa_lote.instalar_parada.)"""
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


def main(q, a=None):
    """Punto de entrada de EJECUTAR-ACTIONS-MEJORAS-WEB.bat. UNICO sitio que concede AUTORIZADO (la pulsacion es la autorizacion)."""
    global AUTORIZADO
    for f in (sys.stdout, sys.stderr):
        try: f.reconfigure(line_buffering=True, errors="replace")
        except Exception: pass
    with q.Lock("actions", max_min=10**9):  # nunca se da por "colgado": un EJECUTAR largo no puede ser terminado por otro que arranca
        q.set_flag("stop_actions", False)
        AUTORIZADO = True
        try:
            lo = Ejecutor(q, cfg={"panel": sys.stdout.isatty(), "limite": getattr(a, "limite", None), "continuo": bool(getattr(a, "continuo", False))}); lo.interactivo = sys.stdin.isatty()
            instalar_parada(lo); return lo.ejecutar()
        finally: AUTORIZADO = False


def validar_solo(q, exp_id=None):
    """`mw.py validar [ID]`: captura y valida en local los `preparado` SIN GitHub (ni push ni dispatch)."""
    lo = Ejecutor(q, gh=_SinGh(), cfg={"limite": None})
    try: return _validar_solo(lo, exp_id)
    finally: lo.c.close()


def _validar_solo(lo, exp_id):
    if exp_id:
        e = lo.c.execute("SELECT estado FROM expedientes WHERE id=?", (exp_id,)).fetchone()
        if not e or e["estado"] not in ("preparado", "fallo_local"): print(f"{exp_id}: estado {e['estado'] if e else 'inexistente'}; solo se validan preparado/fallo_local"); return 2
        lo.c.execute("DELETE FROM cola WHERE exp=? AND estado='fallo_local'", (exp_id,)); lo.c.commit()
        lo.validar_local(exp_id)
    else: lo.capturar()
    return 0


class _SinGh:
    def __getattr__(self, n): raise NoAutorizado("validacion local: sin acceso a GitHub")


def reintentar_infra(q, clave_o_id):
    """Accion EXPLICITA: un item en infraestructura vuelve a `validado` con intento+1; el siguiente EJECUTAR lo enviara como run nuevo (#intento)."""
    c = q.db()
    try: return _reintentar(q, c, clave_o_id)
    finally: c.close()


def _reintentar(q, c, clave_o_id):
    it = c.execute("SELECT * FROM cola WHERE (clave=? OR exp=?) AND estado='remoto_infra'", (clave_o_id, clave_o_id)).fetchone()
    if not it: print("ningun item en remoto_infra con ese id"); return 2
    c.execute("UPDATE cola SET estado='validado', remoto_intentos=remoto_intentos+1, enviado=NULL, actualizado=?, detalle='reintento manual tras infraestructura' WHERE clave=?", (q.now(), it["clave"]))
    c.execute("UPDATE expedientes SET estado='validado' WHERE id=?", (it["exp"],)); c.commit()
    print(f"{it['clave']} listo para reenviar (intento {it['remoto_intentos'] + 2}) en el proximo EJECUTAR."); return 0
