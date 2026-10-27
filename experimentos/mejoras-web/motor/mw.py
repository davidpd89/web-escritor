#!/usr/bin/env python3
"""mw: nucleo del laboratorio de mejoras web de davidportodiaz.com (equivalente de qa_gpt.py en el QA GPT, SISTEMA TOTALMENTE SEPARADO).

Circuito: GPT investiga -> Claude contrasta -> GPT desarrolla -> Claude revisa -> validacion local en worktree -> cola persistente ->
Actions MANUAL (workflow_dispatch, max 3 grupos) -> resultados -> PR hija en borrador (accion explicita). Nunca fusiona, nunca toca main.

PROCEDENCIA de los patrones (scripts/qa-gpt @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, blob qa_gpt.py 010ae0137d3307e1c5f3050ecbfc21c97bb40252):
Conn/db (rollback ante 'database is locked', WAL), Lock con recuperacion de PID muerto, marcar()/servicio.json, dormir() con stop, load_json_block,
jobs reanudables por chat_id. Cambios: STATE propio, sin tasklist obligatorio (tambien Linux, para poder probar), guardas de aislamiento frente al QA.

Estado persistente FUERA de Git: %LOCALAPPDATA%\\web-escritor-mejoras-web\\estado (o MEJORAS_WEB_STATE). Nunca C:\\GIT\\qa-gpt-state.
"""
import argparse, datetime as dt, json, os, re, shutil, sqlite3, subprocess, sys, time
from pathlib import Path

sys.modules.setdefault("mw", sys.modules[__name__])  # `python mw.py`: los demas modulos hacen `import mw` y deben ver ESTE mismo modulo (mismo CFG/STATE)
HERE = Path(__file__).resolve().parent
LAB = HERE.parent
REPO = LAB.parents[1]  # checkout que contiene el codigo del laboratorio (su .git es el que usan los worktrees)
sys.path.insert(0, str(HERE))

PREFIJOS_AJENOS = ("gpt-qa/", "qa-fix/", "qa-dev/", "autofix/", "main", "master", "lab/", "research/", "automation/")
RUTAS_QA = ("qa-gpt-state", "web-escritor-qa-gpt", "qa-gpt")
PUERTOS_QA = (9230, 9224, 9225)
SIN_VENTANA = 0x08000000 if os.name == "nt" else 0
_SIN_PROMPT = {"GIT_TERMINAL_PROMPT": "0", "GH_PROMPT_DISABLED": "1"}
REINICIO = 75  # codigo de salida "relanzame" para el supervisor
RC_CONFIG = 2      # configuracion/aislamiento invalidos: el supervisor NO reintenta
RC_EN_MARCHA = 3   # ya hay otra instancia: el supervisor NO reintenta


def salir(msg, code):
    """Mensaje util en stderr y salida con un codigo que el supervisor entiende (no es un fallo que reiniciar)."""
    print(msg, file=sys.stderr); raise SystemExit(code)


def cargar_config():
    ruta = Path(os.environ.get("MEJORAS_WEB_CONFIG") or LAB / "config.json")
    cfg = json.loads(ruta.read_text(encoding="utf-8"))
    if os.environ.get("MEJORAS_WEB_PROJECT_ID"): cfg.setdefault("gpt", {})["project_id"] = os.environ["MEJORAS_WEB_PROJECT_ID"]
    return cfg


def estado_por_defecto():
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "state")
    return Path(base) / "web-escritor-mejoras-web" / "estado"


CFG = cargar_config()
STATE = Path(os.environ.get("MEJORAS_WEB_STATE") or estado_por_defecto())
TASK = "web-escritor-mejoras-web"

# ---------- tiempo ----------
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Madrid")
except Exception:  # sin tzdata: hora local del sistema
    TZ = None


def _ahora(): return dt.datetime.now(TZ).replace(tzinfo=None)
def now(): return _ahora().isoformat(timespec="seconds")
def today(): return _ahora().date().isoformat()


# ---------- aislamiento ----------
def rama_permitida(rama):
    """Solo ramas del laboratorio (mejoras-web/<slug>). Cualquier otra (main, lab/, gpt-qa/, qa-fix/...) es rechazada: ni push ni PR."""
    if not isinstance(rama, str) or not rama.startswith(CFG["prefijo_rama"]) or ".." in rama or rama.endswith(("/", ".lock")): return False
    if rama.startswith(PREFIJOS_AJENOS): return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", rama))


def verificar_aislamiento(state=None, puerto=None, perfil=None):
    """-> lista de problemas (vacia = aislado del QA original). Se llama al arrancar INICIAR y EJECUTAR."""
    state, p = Path(state or STATE), []
    puerto = int(puerto or CFG["gpt"]["puerto_cdp"])
    if puerto in PUERTOS_QA: p.append(f"puerto CDP {puerto} es del QA original")
    s = str(state).lower().replace("\\", "/")
    if any(x in s for x in RUTAS_QA): p.append(f"el estado {state} esta en una ruta del QA original")
    if not CFG["prefijo_rama"].startswith("mejoras-web/") or CFG["prefijo_rama"].startswith(PREFIJOS_AJENOS): p.append("prefijo de rama no aislado")
    if str(CFG["rama_base"]) in ("main", "master"): p.append("rama_base no puede ser main")
    return p


def exigir_aislamiento():
    import edge_launcher
    p = verificar_aislamiento(perfil=edge_launcher.perfil())
    if p: salir("AISLAMIENTO: " + "; ".join(p), RC_CONFIG)


# ---------- procesos ----------
def run(args, **kw):
    """subprocess.run sin ventana ni prompts; la salida y los errores NO se ocultan (el llamador decide con returncode)."""
    kw.setdefault("creationflags", SIN_VENTANA)
    if "input" not in kw: kw.setdefault("stdin", subprocess.DEVNULL)
    if os.path.basename(str(args[0])).lower().removesuffix(".exe") in ("git", "gh"): kw["env"] = {**(kw.get("env") or os.environ), **_SIN_PROMPT}
    return subprocess.run(args, **kw)


def popen(args, **kw):
    kw.setdefault("creationflags", SIN_VENTANA)
    if "input" not in kw: kw.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.Popen(args, **kw)


def sh(args, cwd=None, check=True):
    r = run(args, cwd=REPO if cwd is None else cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(map(str, args))[:120]}: {(r.stderr or r.stdout).strip()[:400]}")
    return r.stdout.strip()


def git(*a, cwd=None, check=True):
    return sh(["git", "-c", "core.autocrlf=false", *a], cwd=cwd, check=check)


def pid_alive(pid):
    pid = int(pid)
    if os.name == "nt":  # PID exacto (columna 2 del CSV); `str(pid) in salida` daba falsos positivos con cifras de memoria
        for ln in sh(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], check=False).splitlines():
            cols = [x.strip('"') for x in ln.split('","')]
            if len(cols) > 1 and cols[1] == str(pid): return True
        return False
    try: os.kill(pid, 0)
    except ProcessLookupError: return False
    except PermissionError: return True
    return True


def linea_comandos(pid):
    if os.name == "nt":
        return sh(["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"], check=False)
    try: return Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError: return ""


def es_mw(pid):
    """Evita matar un PID reutilizado por otro programa."""
    c = linea_comandos(pid)
    return any(x in c for x in ("mw.py", "supervisor.py", "mejoras-web"))


def matar_arbol(pid):
    if os.name == "nt": sh(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
    else:
        try: os.kill(int(pid), 15)
        except OSError: pass


# ---------- base de datos ----------
class Conn(sqlite3.Connection):
    """Un 'database is locked' a mitad de transaccion dejaba la conexion con su lock hasta cerrarla (QA, 2026-10-26: 20 min parado).
    Ante cualquier OperationalError se deshace al instante. (Literal de qa_gpt.Conn.)"""
    def _soltar(self):
        try: self.rollback()
        except sqlite3.Error: pass
    def execute(self, *a):
        try: return super().execute(*a)
        except sqlite3.OperationalError: self._soltar(); raise
    def executemany(self, *a):
        try: return super().executemany(*a)
        except sqlite3.OperationalError: self._soltar(); raise
    def commit(self):
        try: return super().commit()
        except sqlite3.OperationalError: self._soltar(); raise


ESQUEMA = """
CREATE TABLE IF NOT EXISTS expedientes(id TEXT PRIMARY KEY, area TEXT, lente TEXT, titulo TEXT, necesidad TEXT, h_necesidad TEXT, h_comportamiento TEXT,
  estado TEXT, datos TEXT, contraste TEXT, parche TEXT, revision TEXT, rama TEXT, base_sha TEXT, sha TEXT, intentos_parche INTEGER DEFAULT 0,
  motivo TEXT, duplicado_de TEXT, pr_url TEXT, creado TEXT, actualizado TEXT);
CREATE TABLE IF NOT EXISTS historial(exp TEXT, fecha TEXT, estado TEXT, detalle TEXT);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, clave TEXT UNIQUE, tipo TEXT, area TEXT, estado TEXT, payload TEXT, intentos INTEGER DEFAULT 0,
  no_antes TEXT, error TEXT, chat_id TEXT, fase TEXT, respuesta TEXT, creado TEXT, actualizado TEXT);
CREATE TABLE IF NOT EXISTS peticiones(fecha TEXT, hora TEXT, tipo TEXT, area TEXT, chars_in INTEGER, chars_out INTEGER, ok INTEGER, chat_id TEXT,
  estado TEXT, herramientas INTEGER, segundos INTEGER);
CREATE TABLE IF NOT EXISTS pares(par TEXT PRIMARY KEY, ultima TEXT, veces INTEGER DEFAULT 0, utiles INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS cola(clave TEXT PRIMARY KEY, exp TEXT, rama TEXT, sha TEXT, estado TEXT, detalle TEXT, tests TEXT, local_clase TEXT, local_log TEXT,
  runs TEXT, intentos INTEGER DEFAULT 0, remoto_intentos INTEGER DEFAULT 0, enviado TEXT, creado TEXT, actualizado TEXT);
CREATE TABLE IF NOT EXISTS cola_tests(clave TEXT, fuente TEXT, ruta TEXT, clase TEXT, rc INTEGER, run_id INTEGER, fecha TEXT, PRIMARY KEY(clave, fuente, ruta));
CREATE TABLE IF NOT EXISTS envios(fecha TEXT, clave TEXT, run_id INTEGER);
CREATE TABLE IF NOT EXISTS eventos(fecha TEXT, entidad TEXT, ident TEXT, estado TEXT, nota TEXT);
"""


def db():
    STATE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(STATE / "mejoras.db", timeout=30, factory=Conn)
    c.row_factory = sqlite3.Row
    try: c.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError: pass
    c.executescript(ESQUEMA)
    import claude_cli; claude_cli.migrar(c)
    c.commit()
    return c


def evento(c, entidad, ident, estado, nota=""):
    c.execute("INSERT INTO eventos VALUES(?,?,?,?,?)", (now(), entidad, str(ident), estado, (nota or "")[:300]))


def set_estado(c, exp_id, estado, detalle="", **extra):
    """Transicion de un expediente con rastro en historial (recuperable tras cualquier cierre)."""
    cols = {"estado": estado, "actualizado": now(), **extra}
    if detalle: cols["motivo"] = detalle[:400]
    c.execute(f"UPDATE expedientes SET {','.join(k + '=?' for k in cols)} WHERE id=?", (*cols.values(), exp_id))
    c.execute("INSERT INTO historial VALUES(?,?,?,?)", (exp_id, now(), estado, (detalle or "")[:300]))
    c.commit()


# ---------- bloqueos y estado vivo ----------
class Lock:
    """Un unico proceso por nombre; recupera bloqueos de procesos muertos (creacion exclusiva: dos procesos no pueden tomarlo a la vez)."""
    def __init__(self, nombre, max_min=None):
        self.nombre, self.max_min = nombre, max_min if max_min is not None else CFG.get("worker_max_min", 120)

    @property
    def path(self): return STATE / f"{self.nombre}.lock"

    def __enter__(self):
        STATE.mkdir(parents=True, exist_ok=True)
        for _ in range(5):
            try: fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError: pass
            else:
                with os.fdopen(fd, "w") as f: f.write(f"{os.getpid()} {now()}")
                return self
            try: pid = int(self.path.read_text().split()[0])
            except Exception: pid = 0
            if pid and pid != os.getpid() and pid_alive(pid):
                try: edad = (_ahora() - dt.datetime.fromisoformat(self.path.read_text().split(None, 1)[1].strip())).total_seconds() / 60
                except Exception: edad = 0
                if edad <= self.max_min or not es_mw(pid):
                    salir(f"Ya hay un proceso '{self.nombre}' en marcha (pid {pid}, {int(edad)} min). No se arranca otro (mira ESTADO-MEJORAS-WEB.bat).", RC_EN_MARCHA)
                print(f"Proceso '{self.nombre}' colgado (pid {pid}, {int(edad)} min): se termina y se toma el relevo")
                matar_arbol(pid); time.sleep(2)
            self.path.unlink(missing_ok=True)
        raise SystemExit(f"No se pudo tomar el bloqueo '{self.nombre}' (disputa continua).")

    def __exit__(self, *a):
        try:
            if self.path.read_text().split()[0] != str(os.getpid()): return
        except (OSError, IndexError): return
        self.path.unlink(missing_ok=True)

    def latido(self):
        try: self.path.write_text(f"{os.getpid()} {now()}")
        except OSError: pass

    def dueno(self):
        """PID vivo que lo sostiene (y es del laboratorio) o 0."""
        try: pid = int(self.path.read_text().split()[0])
        except Exception: return 0
        return pid if pid_alive(pid) and (pid == os.getpid() or es_mw(pid)) else 0


def flag(name): return (STATE / name).exists()


def set_flag(name, on):
    STATE.mkdir(parents=True, exist_ok=True)
    p = STATE / name
    if on: p.write_text(now())
    else: p.unlink(missing_ok=True)


def svc_path(): return STATE / "servicio.json"


def marcar(**kw):
    """Estado vivo del servicio (lo lee `estado`); escritura atomica."""
    try: cur = json.loads(svc_path().read_text(encoding="utf-8"))
    except Exception: cur = {}
    cur.update(kw, actualizado=now())
    tmp = svc_path().with_suffix(".tmp"); STATE.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8"); os.replace(tmp, svc_path())


def leer_servicio():
    try: return json.loads(svc_path().read_text(encoding="utf-8"))
    except Exception: return {}


def dormir(seg, lock=None):
    """Espera interrumpible: renueva el latido y sale en cuanto se pide parar."""
    fin = time.monotonic() + seg
    while time.monotonic() < fin and not flag("stop"):
        if lock: lock.latido()
        time.sleep(min(5, max(fin - time.monotonic(), 0)))


def parada_vencida():
    """Parada pedida y ya pasada la gracia: la generacion en curso se deja reanudable (no se pierde)."""
    f = STATE / "stop"
    return f.exists() and time.time() - f.stat().st_mtime > CFG.get("parada_gracia_min", 3) * 60


# ---------- repositorio de lectura (rama base del laboratorio) ----------
def fuente_ref():
    """Referencia que describe el sitio con las mejoras ya acumuladas: origin/<rama_base>."""
    return f"origin/{CFG['rama_base']}"


_ULTIMO_FETCH = {}


def refrescar_base(forzar=False, cada_min=20):
    """`git fetch` de la rama base como mucho cada `cada_min` minutos (o si la referencia no existe todavia en este clon).
    Un fallo de red no es grave si la referencia ya existe; si no existe, error claro (antes: 'unknown revision' en cada paso)."""
    ref = fuente_ref()
    existe = lambda: run(["git", "rev-parse", "--verify", "-q", ref], cwd=REPO, capture_output=True).returncode == 0
    if forzar or not existe() or time.time() - _ULTIMO_FETCH.get(str(REPO), 0) > cada_min * 60:
        git("fetch", "-q", "origin", CFG["rama_base"], check=False); _ULTIMO_FETCH[str(REPO)] = time.time()
    if not existe():
        raise RuntimeError(f"no existe {ref} en este clon ni en origin: `git fetch origin {CFG['rama_base']}` (la rama base del laboratorio debe estar publicada)")


def preparar_src():
    """Worktree desacoplado en origin/<rama_base> para que Claude lea el codigo (solo lectura). Nunca el checkout de David."""
    refrescar_base()
    src = STATE / "src"
    if (src / ".git").exists():
        git("checkout", "-q", "--detach", fuente_ref(), cwd=src, check=False)
    else:
        src.parent.mkdir(parents=True, exist_ok=True)
        git("worktree", "prune", check=False)
        git("worktree", "add", "--detach", "-f", str(src), fuente_ref())
    return src


def head_base():
    refrescar_base()
    return git("rev-parse", fuente_ref())


def load_json_block(text):
    """JSON de una respuesta de ChatGPT (con o sin ```json ni CodeBlock). Literal de qa_gpt.load_json_block."""
    m = re.search(r"<CodeBlock[^>]*>\s*\{`(.*)`\s*\}\s*</CodeBlock>", text, re.S)
    text = re.sub(r"\\([\\`$])", r"\1", m.group(1)) if m else re.sub(r"</?CodeBlock[^>]*>", "", text)
    t = re.sub(r"```(?:json)?", "", text)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j < i: raise ValueError("sin bloque JSON")
    return json.loads(t[i:j + 1])


# ---------- comandos del servicio ----------
def cmd_servicio(a):
    """Servicio CONTINUO (lo arranca INICIAR). Una peticion GPT cada vez. NUNCA despacha Actions ni abre PR (no importa actions.py con permiso)."""
    import gpt_browser, investigar
    exigir_aislamiento()
    gpt_browser.configurar(CFG["gpt"]["puerto_cdp"], CFG["gpt"].get("project_id") or None)
    lock = Lock("worker")
    with lock:
        set_flag("stop", False)  # solo con el bloqueo en la mano: un arranque duplicado no puede borrar la parada pedida al primero
        c = db(); inicio = now(); gpt_browser.PARADA = parada_vencida
        print(f"{inicio} SERVICIO iniciado (pid {os.getpid()})")
        marcar(estado="arrancando", inicio=inicio, pid=os.getpid(), ultimo_error=None, tarea=None, parado=None, hasta=None, errores_seguidos=0)
        c.execute("UPDATE jobs SET estado='pendiente' WHERE estado='en_curso'")  # caida a mitad: el job vuelve a la cola con su chat_id (reanuda, no reenvia)
        c.execute("UPDATE jobs SET no_antes=? WHERE estado='pendiente' AND fase='generando' AND chat_id IS NOT NULL", (now(),))
        c.commit(); (STATE / "limite").unlink(missing_ok=True)
        investigar.reconciliar(c)
        errores = 0
        try:
            while not flag("stop"):
                lock.latido()
                if flag("pause"): marcar(estado="pausado"); dormir(30, lock); continue
                try: r = investigar.paso(c)
                except SystemExit as e:
                    r = "limite" if (STATE / "limite").exists() else ("login", str(e))
                except Exception as e:
                    errores += 1
                    marcar(ultimo_error=f"{now()} {type(e).__name__}: {str(e)[:200]}", errores_seguidos=errores); print(f"{now()} ERROR en el paso: {e}")
                    if errores >= CFG.get("errores_para_reiniciar", 5): print("Errores repetidos: salida para que el supervisor relance"); return REINICIO
                    dormir(60, lock); continue
                errores = 0
                if r is True:
                    marcar(estado="ejecutando", ultimo_ok=now(), errores_seguidos=0)
                elif r == "limite":
                    mins = 30; hasta = (_ahora() + dt.timedelta(minutes=mins)).isoformat(timespec="seconds")
                    marcar(estado="pausado_limite", hasta=hasta, ultimo_error=f"{now()} limite de uso")
                    print(f"{now()} Limite de uso: espera {mins} min"); dormir(mins * 60, lock); (STATE / "limite").unlink(missing_ok=True)
                elif isinstance(r, tuple):
                    marcar(estado="login", ultimo_error=f"{now()} {r[1][:160]}"); print(f"{now()} Sin sesion de ChatGPT: reintento en 5 min"); dormir(300, lock)
                else:
                    prox = c.execute("SELECT MIN(no_antes) FROM jobs WHERE estado='pendiente' AND no_antes IS NOT NULL").fetchone()[0]
                    seg = 120 if not prox else max(15, min(600, (dt.datetime.fromisoformat(prox) - _ahora()).total_seconds()))
                    c.commit(); marcar(estado="esperando", tarea=None, hasta=(_ahora() + dt.timedelta(seconds=seg)).isoformat(timespec="seconds"))
                    dormir(seg, lock)
        finally:
            marcar(estado="parado", tarea=None, parado=now()); gpt_browser.PARADA = None; c.close()
            print(f"{now()} SERVICIO detenido")
    return 0


def _python_sin_consola():
    py = Path(sys.executable).with_name("pythonw.exe")
    return str(py if py.exists() else sys.executable)


def cmd_iniciar(a):
    """INICIAR-MEJORAS-WEB.bat: arranca (o reanuda) el investigador desvinculado de la consola. No envia Actions ni abre PR."""
    STATE.mkdir(parents=True, exist_ok=True)
    exigir_aislamiento()
    if Lock("worker").dueno():
        print(f"El investigador YA esta en marcha (pid {Lock('worker').dueno()}). No se arranca otro."); return 0
    if not CFG["gpt"].get("project_id"):
        print("FALTA el Project de ChatGPT del laboratorio: pon su id (g-p-...) en config.json (gpt.project_id) o en MEJORAS_WEB_PROJECT_ID."); return 2
    db().close()
    import edge_launcher
    if edge_launcher.alive() is None: print(f"Abriendo Edge {edge_launcher.PORT} (perfil propio del laboratorio)..."); edge_launcher.main()
    set_flag("pause", False); set_flag("stop", False)
    args = [_python_sin_consola(), str(HERE / "supervisor.py"), "servicio"]
    kw = dict(cwd=str(STATE), close_fds=True)
    if os.name == "nt": kw["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    else: kw["start_new_session"] = True
    popen(args, **kw)
    pid = 0
    for _ in range(40):
        time.sleep(0.5); pid = Lock("worker").dueno()
        if pid: break
    if not pid: print(f"El investigador no arranco. Mira {STATE / 'servicio.log'}"); return 1
    print(f"INVESTIGADOR DE MEJORAS WEB EN MARCHA (pid {pid}). Trabaja hasta que lo pares con PARAR-MEJORAS-WEB.bat.\n"
          f"No envia Actions ni abre PR. Estado: ESTADO-MEJORAS-WEB.bat. Registro: {STATE / 'servicio.log'}")
    return 0


def cmd_parar(a):
    rc = _parar(a)
    if getattr(a, "cerrar_edge", False):
        import edge_launcher; edge_launcher.cerrar()
    return rc


def _parar(a):
    """PARAR-MEJORAS-WEB.bat: parada ordenada y acotada del investigador y del ejecutor. NO cancela runs remotos."""
    set_flag("stop", True); set_flag("stop_actions", True)  # banderas separadas: arrancar EJECUTAR no cancela la parada del investigador
    pids = [p for p in (Lock("worker").dueno(), Lock("actions").dueno()) if p]
    sup = Lock("supervisor").dueno()
    if sup and sup not in pids: pids.append(sup)
    if not pids:
        print("Nada en marcha. Marcado como parado."); Lock("worker").path.unlink(missing_ok=True); return 0
    limite = time.monotonic() + (CFG.get("parada_gracia_min", 3) + 3) * 60
    print(f"Parada solicitada (pids {pids}). Si hay una respuesta generandose se espera hasta {CFG.get('parada_gracia_min', 3)} min a capturarla; si no, queda reanudable.")
    print("Los runs ya enviados a GitHub Actions NO se cancelan: se recogen al abrir EJECUTAR de nuevo.")
    while time.monotonic() < limite and any(pid_alive(p) for p in pids): time.sleep(2)
    vivos = [p for p in pids if pid_alive(p)]
    if vivos:
        print("No terminaron a tiempo: se cierran SOLO sus procesos (cola y chat recuperables).")
        for p in vivos:
            if es_mw(p): matar_arbol(p)
        time.sleep(1)
        for nombre in ("worker", "actions", "supervisor", "supervisor_actions"): Lock(nombre).path.unlink(missing_ok=True)
        marcar(estado="parado", parado=now(), tarea=None); print("PARADO (forzado, estado conservado)."); return 0
    marcar(estado="parado", parado=now(), tarea=None)
    print("PARADO correctamente. Progreso guardado; el siguiente INICIAR continua donde quedo."); return 0


def cmd_ejecutar_actions(a):
    import actions
    exigir_aislamiento()
    return actions.main(sys.modules[__name__], a)


def cmd_estado(a):
    import informe
    print(informe.texto(sys.modules[__name__], completo=getattr(a, "completo", False))); return 0


def cmd_validar(a):
    import actions
    exigir_aislamiento()
    return actions.validar_solo(sys.modules[__name__], a.id)


def cmd_pr(a):
    import pr_hija
    exigir_aislamiento()
    return pr_hija.main(sys.modules[__name__], a)


def cmd_vista_previa(a):
    import preview
    return preview.main(sys.modules[__name__], a)


def cmd_reintentar_infra(a):
    import actions
    return actions.reintentar_infra(sys.modules[__name__], a.id)


def cmd_descartar(a):
    c = db()
    try:
        if not c.execute("SELECT estado FROM expedientes WHERE id=?", (a.id,)).fetchone(): print("expediente inexistente"); return 2
        set_estado(c, a.id, "descartado_manual", a.motivo or "descartado por David"); print(f"{a.id} descartado."); return 0
    finally: c.close()


def main(argv=None):
    p = argparse.ArgumentParser(prog="mw.py", description="Laboratorio de mejoras web (aislado del QA GPT)")
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("iniciar").set_defaults(f=cmd_iniciar)
    s.add_parser("servicio").set_defaults(f=cmd_servicio)
    pa = s.add_parser("parar"); pa.add_argument("--cerrar-edge", action="store_true"); pa.set_defaults(f=cmd_parar)
    e = s.add_parser("estado"); e.add_argument("--completo", action="store_true"); e.set_defaults(f=cmd_estado)
    x = s.add_parser("ejecutar-actions"); x.add_argument("--continuo", action="store_true"); x.add_argument("--limite", type=int); x.set_defaults(f=cmd_ejecutar_actions)
    v = s.add_parser("validar"); v.add_argument("id", nargs="?"); v.set_defaults(f=cmd_validar)
    pr = s.add_parser("pr"); pr.add_argument("id"); pr.add_argument("--confirmar", action="store_true"); pr.add_argument("--solo-local", action="store_true"); pr.set_defaults(f=cmd_pr)
    vp = s.add_parser("vista-previa"); vp.add_argument("id", nargs="?"); vp.add_argument("--puerto", type=int, default=8766); vp.add_argument("--sin-abrir", action="store_true"); vp.set_defaults(f=cmd_vista_previa)
    ri = s.add_parser("reintentar-infra"); ri.add_argument("id"); ri.set_defaults(f=cmd_reintentar_infra)
    d = s.add_parser("descartar"); d.add_argument("id"); d.add_argument("--motivo"); d.set_defaults(f=cmd_descartar)
    a = p.parse_args(argv)
    return a.f(a) or 0


if __name__ == "__main__":
    for f in (sys.stdout, sys.stderr):
        try: f.reconfigure(line_buffering=True, errors="replace")
        except Exception: pass
    if sys.stdout is None or sys.stderr is None:  # pythonw: sin consola, a fichero
        STATE.mkdir(parents=True, exist_ok=True)
        _log = open(STATE / "servicio.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or _log; sys.stderr = sys.stderr or _log
    sys.exit(main())
