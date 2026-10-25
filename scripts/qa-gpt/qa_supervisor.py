"""Supervisor 24 h de qa-gpt: el seguro para lo que la automatizacion no sabe resolver sola.

  python qa_supervisor.py iniciar                      (lo usa INICIAR-QA-GPT.bat)
  python qa_supervisor.py ejecutar-actions --continuo  (lo usa EJECUTAR-ACTIONS-QA-GPT.bat)

1) CAIDA del pipeline (traceback): Claude corrige la causa raiz en un worktree aislado y anade un test de regresion; el supervisor pasa la
   suite completa y, solo si queda verde, integra el arreglo (fast-forward en automation/qa-gpt) y relanza el proceso. El mismo fallo no vuelve.
2) MAIN EN ROJO confirmado (ya relanzado una vez): Claude corrige la web o el test en una rama qa-fix/main-*, que se publica como PR con
   auto-merge; las fusiones del pipeline no se bloquean mientras tanto (qa_pr._freno_main).
3) ATASCO: 20 min sin actividad con trabajo pendiente -> Claude diagnostica con el estado y los logs y corrige por la via 1.
Limites: una reparacion por firma de fallo y dia, `max_reparaciones_dia` en total, y Q/Ctrl+C del usuario nunca se tratan como fallo.
"""
import datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_QA = HERE.parents[1]  # C:\GIT\web-escritor-qa-gpt (rama automation/qa-gpt): el codigo vivo del pipeline
sys.path.insert(0, str(HERE))

REINICIO = 75  # = qa_gpt.REINICIO
ESQUEMA = {"type": "object", "properties": {"resultado": {"type": "string", "enum": ["corregido", "no_se_puede"]}, "causa": {"type": "string"},
                                              "resumen": {"type": "string"}}, "required": ["resultado", "causa", "resumen"], "additionalProperties": False}
SIS_CODIGO = ("Eres el mantenedor del pipeline qa-gpt (Python 3.11, Windows; codigo en este directorio). Te llega un INCIDENTE real: un traceback que "
              "tumbo el proceso o un atasco sin progreso. Encuentra y corrige la CAUSA RAIZ con el cambio minimo, siguiendo el estilo del fichero. "
              "Anade un test de regresion en el test_*.py que corresponda que falle sin tu arreglo y pase con el. Ejecuta los tests con "
              "`python -m unittest <modulo>` hasta que pasen. No hagas commits, no toques config.json salvo que sea la causa, no borres tests. "
              "Si el incidente no es un fallo del codigo (red caida, GitHub caido), responde no_se_puede y explica por que.")
SIS_MAIN = ("Eres el desarrollador de un sitio web estatico (repo web-escritor, checkout de origin/main). La auditoria posterior al despliegue de "
            "main fallo dos veces seguidas con el log adjunto. Decide si el defecto esta en la web publicada o en el test/auditoria (falso positivo) "
            "y corrige la causa raiz con el cambio minimo: en la web si la web esta mal; en el test si el test esta mal (sin debilitarlo: debe seguir "
            "detectando el defecto real que vigila). Si tocas un test, amplia su autotest con el caso. Comprueba con node/python los tests afectados. "
            "No hagas commits. No toques .github/workflows ni scripts/qa-gpt. No busques .env, URLs ni credenciales: el comando de prueba "
            "levanta el servidor local por ti. Ve directo al test que falla y a la pagina que vigila; tienes pocos turnos.")


def firma(texto):
    """Firma estable de un traceback: tipo de excepcion + ultimo fichero:funcion propio (sin numeros de linea, que cambian con cada arreglo)."""
    marcos = re.findall(r'File "([^"]+)", line \d+, in (\w+)', texto)
    propios = [f"{Path(f).name}:{fn}" for f, fn in marcos if "Python3" not in f and "Lib" not in Path(f).parts] or [f"{Path(f).name}:{fn}" for f, fn in marcos[-1:]]
    exc = (re.findall(r"^(\w+(?:Error|Exception|Interrupt)\w*)\b", texto, re.M) or ["?"])[-1]
    return f"{exc}@{propios[-1] if propios else '?'}"


def traceback_de(texto):
    i = texto.rfind("Traceback (most recent call last):")
    return texto[i:] if i >= 0 else ""


class Supervisor:
    def __init__(self, q, out=print, claude=None, run=None):
        self.q, self.out = q, out
        self.dir = Path(q.STATE) / "supervisor"; self.dir.mkdir(parents=True, exist_ok=True)
        self.cfg = {"max_reparaciones_dia": 6, "atasco_min": 20, "vigilar_s": 300, **(q.CFG.get("supervisor") or {})}
        self._claude = claude; self._run = run or self._run_real

    # ---------- utilidades ----------
    @staticmethod
    def _run_real(cmd, cwd, timeout=600, env=None):
        import qa_cobertura as cob
        try:
            r = cob.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired: return 124, f"timeout {timeout}s"
        except OSError as e: return 127, str(e)

    def claude(self, clave, sistema, entrada, herramientas, cwd, max_turnos=40):
        if self._claude: return self._claude(clave, sistema, entrada, herramientas, cwd)
        import qa_claude
        c = self.q.db(); qa_claude.migrar(c)
        try: return qa_claude.llamar(self.q, c, clave, "desarrollo", sistema, entrada, ESQUEMA, herramientas=herramientas, cwd=cwd, max_turnos=max_turnos,
                                     esfuerzo="medium", usar_cache=False, timeout_s=1800, max_usd=3.0)[0]
        finally: c.close()

    def _registro(self):
        try: return json.loads((self.dir / "reparaciones.json").read_text(encoding="utf-8"))
        except (OSError, ValueError): return {}

    def permitido(self, fir):
        """Una reparacion por firma y dia, y un tope diario total: Claude no entra en bucle con el mismo fallo.
        Main en rojo es distinto: si el intento no dejo PR (Claude agoto turnos, error...) se reintenta a la hora, hasta 3 veces por run,
        fuera del tope diario: esperar a manana dejaba la web publicada rota toda la noche (run 40227985780)."""
        reg, hoy = self._registro(), self.q.today()
        if fir.startswith("main-rojo:"):
            ts, _, resto = reg.get(fir, "").partition(" "); resultado, _, n = resto.partition(" ")
            if not ts: return True
            if resultado == "pr_abierta" or int(n or 1) >= 3: return False
            return (dt.datetime.fromisoformat(self.q.now()) - dt.datetime.fromisoformat(ts[:19])).total_seconds() >= 3600
        if reg.get(fir, "")[:10] == hoy: return False
        return sum(1 for f, v in reg.items() if v[:10] == hoy and not f.startswith("main-rojo:")) < self.cfg["max_reparaciones_dia"]

    def anotar(self, fir, resultado, detalle):
        reg = self._registro()
        if fir.startswith("main-rojo:"):  # "fecha resultado intentos": permitido() decide el reintento
            n = int((reg.get(fir, "").split(" ") + ["", "", "0"])[2] or 0) + 1
            reg[fir] = f"{self.q.now()} {resultado} {n}"
        else: reg[fir] = self.q.now()
        (self.dir / "reparaciones.json").write_text(json.dumps(reg, indent=1), encoding="utf-8")
        with open(self.dir / "historial.log", "a", encoding="utf-8") as f: f.write(f"{self.q.now()} {fir} -> {resultado}: {detalle[:300]}\n")
        try:
            c = self.q.db(); __import__("qa_cobertura").evento(c, "supervisor", 0, resultado, f"{fir}: {detalle[:200]}", self.q.now()); c.commit(); c.close()
        except Exception: pass
        self.out(f"[supervisor] {fir}: {resultado} - {detalle[:160]}")

    # ---------- 1) y 3): reparar el codigo del pipeline ----------
    def reparar_codigo(self, incidente, fir):
        if not self.permitido(fir): self.out(f"[supervisor] {fir}: ya se intento reparar hoy; no se repite"); return "omitido"
        ts = dt.datetime.now().strftime("%m%d%H%M%S"); rama = f"autofix/{ts}"; wt = self.dir / f"wt-{ts}"
        g = lambda *a, cwd=REPO_QA, t=300: self._run(["git", *a], cwd, t)
        if g("worktree", "add", "-B", rama, str(wt), "HEAD")[0]: self.anotar(fir, "error", "no se pudo crear el worktree"); return "error"
        try:
            cod = wt / "scripts" / "qa-gpt"
            entrada = f"INCIDENTE ({fir}):\n{incidente[-6000:]}"
            try: res = self.claude(f"autofix:{fir}:{ts}", SIS_CODIGO, entrada, "Read,Edit,Write,Grep,Glob,Bash(python -m unittest:*),Bash(python -m py_compile:*)", cod)
            except Exception as e: self.anotar(fir, "claude_fallo", str(e)); return "claude_fallo"
            if res["resultado"] != "corregido": self.anotar(fir, "no_se_puede", res["causa"] + " | " + res["resumen"]); return "no_se_puede"
            if not g("status", "--porcelain", cwd=wt)[1].strip(): self.anotar(fir, "sin_cambios", res["resumen"]); return "sin_cambios"
            rc, o = self._run([sys.executable, "-m", "unittest", "discover", "-p", "test_*.py"], cod, 1800)
            if rc: self.anotar(fir, "suite_roja", o[-400:]); return "suite_roja"
            g("add", "-A", "--", ".", ":(exclude,glob)**/__pycache__/**", ":(exclude,glob)**/*.pyc", cwd=wt)  # nunca la cache de Python (rompia el fast-forward)
            msg = f"autofix(qa-gpt): {res['causa'][:90]}\n\n{res['resumen'][:1500]}\n\nIncidente: {fir}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
            if g("-c", "user.name=qa-gpt-supervisor", "-c", "user.email=qa-gpt@users.noreply.github.com", "commit", "-q", "-m", msg, cwd=wt)[0]:
                self.anotar(fir, "error", "commit fallo"); return "error"
            rc, o = g("merge", "--ff-only", "-q", rama)  # el codigo vivo solo avanza si nadie lo cambio entretanto
            if rc: self.anotar(fir, "no_integrado", f"rama {rama} lista pero sin fast-forward: {o[-200:]}"); return "no_integrado"
            self.anotar(fir, "corregido", res["causa"] + " | " + res["resumen"]); return "corregido"
        finally:
            g("worktree", "remove", "--force", str(wt)); shutil.rmtree(wt, ignore_errors=True)
            if not g("merge-base", "--is-ancestor", rama, "HEAD")[0]: g("branch", "-D", rama)

    # ---------- 2): main en rojo ----------
    def reparar_main(self, run_id, log):
        fir = f"main-rojo:{run_id}"
        if not self.permitido(fir): return "omitido"
        q = self.q; root = Path(q.ROOT); rama = f"qa-fix/main-{run_id}"; wt = self.dir / f"main-{run_id}"
        g = lambda *a, cwd=root, t=300: self._run(["git", *a], cwd, t)
        g("fetch", "-q", "origin", "main", t=180)
        if g("ls-remote", "--exit-code", "--heads", "origin", rama, t=60)[0] == 0:  # ya hay rama/PR de este run: un reintento no la machaca con push -f
            self.anotar(fir, "pr_abierta", f"la rama {rama} ya existe"); return "omitido"
        if g("worktree", "add", "-B", rama, str(wt), "origin/main")[0]: self.anotar(fir, "error", "worktree"); return "error"
        try:
            import qa_pr
            run = lambda cmd, cwd, timeout=300: self._run(cmd, Path(cwd), timeout)
            # el repo de la automatizacion no tiene node_modules: sin el enlace al de la web, pagefind vaciaba su indice (#870 borraba 412 ficheros)
            qa_pr.enlazar_node_modules(run, wt)
            from qa_dev_claude import CMD_PROBAR
            # un reintento identico daria el mismo resultado: Claude ve que fallo antes y tiene mas turnos en cada intento
            try: previos = [l.split(" -> ", 1)[1].strip() for l in (self.dir / "historial.log").read_text(encoding="utf-8").splitlines() if f" {fir} -> " in l]
            except OSError: previos = []
            antes = ("\n\nINTENTOS ANTERIORES QUE NO DEJARON PR (no repitas el mismo enfoque; si agotaste turnos, ve directo al fichero y al arreglo minimo):\n"
                     + "\n".join(f"- {p[:400]}" for p in previos[-3:])) if previos else ""
            try: res = self.claude(f"main:{run_id}", SIS_MAIN, f"LOG DEL FALLO (run {run_id}):\n{log[-8000:]}{antes}\n\nPara ejecutar un test con servidor local: `{CMD_PROBAR} <ruta>`",
                                   f"Read,Edit,Write,Grep,Glob,Bash({CMD_PROBAR}:*),Bash(node:*)", wt, max_turnos=80 + 40 * len(previos))  # 40 no bastaba (run 40227985780)
            except Exception as e: self.anotar(fir, "claude_fallo", str(e)); return "claude_fallo"
            if res["resultado"] != "corregido": self.anotar(fir, "no_se_puede", res["causa"] + " | " + res["resumen"]); return "no_se_puede"
            cambios = [l[3:] for l in g("status", "--porcelain", cwd=wt)[1].splitlines() if l.strip() and not l[3:].startswith("node_modules")]
            if not cambios: self.anotar(fir, "sin_cambios", res["resumen"]); return "sin_cambios"
            if any(x.endswith(".html") for x in cambios):
                # shell e indice de busqueda derivan del HTML: sin regenerarlos, content-indexes queda en rojo (#868 -> #869; #870: shell desactualizado)
                qa_pr.regenerar(run, wt, cambios)  # mismo regenerador que los lotes: solo lo que su --check da por obsoleto
                if not (wt / "pagefind" / "pagefind-ui.js").exists() and g("cat-file", "-e", "origin/main:pagefind/pagefind-ui.js", cwd=wt)[0] == 0:
                    g("checkout", "origin/main", "--", "pagefind", cwd=wt)  # indice destruido a medias: mejor el de main que una PR que lo borra
                g("add", "-A", "--", ".", ":!node_modules", cwd=wt)  # paginas que el shell reescribio e indice nuevo
            g("add", "--", *cambios, cwd=wt)
            msg = f"fix: {res['causa'][:90]}\n\n{res['resumen'][:1500]}\n\nAuditoria post-despliegue de main en rojo (run {run_id}).\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
            if g("-c", "user.name=qa-gpt-supervisor", "-c", "user.email=qa-gpt@users.noreply.github.com", "commit", "-q", "-m", msg, cwd=wt)[0]: self.anotar(fir, "error", "commit"); return "error"
            if (r := g("push", "-q", "-f", "origin", f"HEAD:refs/heads/{rama}", cwd=wt, t=300))[0]: self.anotar(fir, "error", "push: " + r[1][-200:]); return "error"
            cuerpo = f"Main en rojo en la auditoria post-despliegue (run {run_id}), confirmado tras relanzar.\n\n**Causa:** {res['causa']}\n\n{res['resumen']}\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)"
            rc, o = self._run(["gh", "pr", "create", "--base", "main", "--head", rama, "--title", f"fix: main en rojo (run {run_id}): {res['causa'][:60]}", "--body", cuerpo], wt, 120)
            if rc and "already exists" not in o: self.anotar(fir, "error", "pr: " + o[-200:]); return "error"
            self._run(["gh", "pr", "merge", "--auto", "--squash", rama], wt, 120)
            self.anotar(fir, "pr_abierta", (o.strip().splitlines() or [""])[-1] + " | " + res["causa"]); return "pr_abierta"
        finally:
            self._run(["cmd", "/c", "rmdir", str(wt / "node_modules")], self.dir, 30)
            g("worktree", "remove", "--force", str(wt)); shutil.rmtree(wt, ignore_errors=True)

    # ---------- 3): atasco ----------
    ESPERAS_LEGITIMAS = ("pausado_limite", "login", "pausado")  # limite de uso de ChatGPT, sin sesion o pausa manual: no son fallos de codigo

    def atasco(self):
        """-> descripcion del atasco o None. Trabajo pendiente YA ejecutable y ninguna actividad (eventos ni jobs) en `atasco_min` minutos."""
        try: est = json.loads((Path(self.q.STATE) / "servicio.json").read_text(encoding="utf-8")).get("estado")
        except (OSError, ValueError): est = None
        if est in self.ESPERAS_LEGITIMAS: return None
        c = self.q.db(); ahora = self.q.now()
        try:
            ult = max(filter(None, [c.execute("SELECT MAX(fecha) FROM eventos").fetchone()[0], c.execute("SELECT MAX(actualizado) FROM jobs").fetchone()[0]]), default=None)
            pend = c.execute("SELECT COUNT(*) FROM jobs WHERE estado='en_curso' OR (estado='pendiente' AND COALESCE(no_antes,'')<=?)", (ahora,)).fetchone()[0]
            listas = c.execute("SELECT COUNT(*) FROM triaje WHERE pr_estado='listo_lote'").fetchone()[0] if c.execute("SELECT 1 FROM sqlite_master WHERE name='triaje'").fetchone() else 0
        finally: c.close()
        if not ult or not (pend or listas): return None
        minutos = (dt.datetime.fromisoformat(ahora) - dt.datetime.fromisoformat(ult[:19])).total_seconds() / 60
        return f"sin actividad desde {ult} ({minutos:.0f} min) con {pend} jobs ejecutables y {listas} correcciones listas" if minutos >= self.cfg["atasco_min"] else None

    def vigilar(self, parar):
        while not parar.wait(self.cfg["vigilar_s"]):
            try:
                desc = self.atasco()
                if not desc: continue
                estado = self._run([sys.executable, str(HERE / "qa_gpt.py"), "estado"], HERE, 300)[1][-4000:]
                try: log = (Path(self.q.STATE) / "servicio.log").read_text(encoding="utf-8", errors="replace")[-3000:]
                except OSError: log = ""
                self.reparar_codigo(f"ATASCO: {desc}\n\nESTADO:\n{estado}\n\nULTIMO LOG DEL WORKER:\n{log}", f"atasco:{self.q.now()[:13]}")
            except Exception as e: self.out(f"[supervisor] vigilancia omitida: {str(e)[:120]}")

    # ---------- envoltorio de INICIAR / EJECUTAR ----------
    def ejecutar(self, args):
        """Lanza qa_gpt.py <args>; si muere con traceback, repara y relanza. Q/Ctrl+C (salida limpia) terminan el supervisor."""
        parar = threading.Event()
        if args[:1] == ["servicio"]: threading.Thread(target=self.vigilar, args=(parar,), daemon=True, name="vigilancia").start()  # un solo vigilante: el del servicio 24 h
        caidas = []
        try:
            while True:
                rc, err = self._hijo(args)
                if rc == REINICIO: self.out("[supervisor] codigo reparado: se relanza con el arreglo"); continue
                tb = traceback_de(err)
                if rc == 0 or not tb or "KeyboardInterrupt" in tb: return rc
                fir = firma(tb); self.out(f"\n[supervisor] el proceso cayo ({fir}); se encarga la reparacion a Claude")
                res = self.reparar_codigo(tb, fir)
                caidas = [t for t in caidas if time.time() - t < 3600] + [time.time()]
                if len(caidas) > 5: self.out("[supervisor] 5 caidas en una hora: se detiene para no entrar en bucle (ver supervisor/historial.log)"); return rc
                self.out(f"[supervisor] reparacion: {res}; se relanza en 30 s"); time.sleep(30)
        finally: parar.set()

    @staticmethod
    def _hijo(args):
        # sin consola (servicio lanzado por INICIAR con pythonw) el hijo heredaba un stdout vacio: su salida se perdia en vez de ir a servicio.log
        consola = getattr(sys.stdout, "isatty", lambda: False)()
        salida = None if consola else getattr(sys.stdout, "buffer", None) and sys.stdout
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", **({} if consola else {"PYTHONUNBUFFERED": "1"})}  # a fichero: linea a linea, no en bloques de 8 KB
        p = subprocess.Popen([sys.executable, str(HERE / "qa_gpt.py"), *args], stdout=salida, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", env=env)
        cola = []
        def leer():
            for linea in p.stderr: sys.stderr.write(linea); sys.stderr.flush(); cola.append(linea); del cola[:-400]
        h = threading.Thread(target=leer, daemon=True); h.start()
        while True:
            try: rc = p.wait(); break
            except KeyboardInterrupt: continue  # Ctrl+C llega tambien al hijo: se espera a su parada controlada
        h.join(5)
        return rc, "".join(cola)


def main(argv):
    import qa_gpt as q
    return Supervisor(q).ejecutar(argv or ["estado"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
