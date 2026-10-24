#!/usr/bin/env python3
"""qa-gpt: descubrimiento y preparacion de tests QA asistidos por GPT (web-escritor).

Estado en C:\GIT\qa-gpt-state (fuera de los worktrees). El descubrimiento corre solo; NUNCA ejecuta tests ni lanza Actions
salvo `lote-nocturno --confirmar` tras `autorizar-noche` (ambos manuales). Ver README.md.
"""
import argparse, datetime as dt, glob, hashlib, json, os, re, sqlite3, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Aislamiento: codigo = HERE (worktree propio, rama automation/qa-gpt); contenido leido = ROOT (worktree desacoplado en origin/main,
# solo lo toca este servicio); estado persistente = STATE (fuera de cualquier worktree). Sobrescribibles por entorno (tests).
ROOT = Path(os.environ.get("QA_GPT_SRC", r"C:\GIT\web-escritor-qa-gpt-src"))
STATE = Path(os.environ.get("QA_GPT_STATE", r"C:\GIT\qa-gpt-state"))
if not ROOT.exists(): ROOT = HERE.parents[1]
DB_PATH = STATE / "estado.db"
WT = STATE / "wt"
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
TASK = "web-escritor-qa-gpt"
sys.path.insert(0, str(HERE))
import qa_cobertura as cob

if sys.stdout is None or sys.stderr is None:  # pythonw (tarea programada): sin consola, a fichero
    STATE.mkdir(parents=True, exist_ok=True)
    sys.stdout = sys.stderr = open(STATE / "servicio.log", "a", encoding="utf-8", buffering=1)


# ---------- utilidades ----------
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Madrid")
except Exception:  # sin tzdata: hora local del sistema (Windows de David ya esta en Madrid)
    TZ = None

def _ahora(): return dt.datetime.now(TZ).replace(tzinfo=None)
def now(): return _ahora().isoformat(timespec="seconds")
def today(): return _ahora().date().isoformat()

def sh(args, cwd=ROOT, check=True):
    r = cob.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        raise RuntimeError(f"{' '.join(map(str, args))[:120]}: {(r.stderr or r.stdout).strip()[:400]}")
    return r.stdout.strip()

def git(*a, cwd=ROOT, check=True):
    if a and a[0] in ("fetch", "checkout", "reset", "commit", "merge", "rebase", "pull"): cob.olvidar_git()  # la historia pudo cambiar: la cache de lecturas ya no vale
    if not check and cwd == ROOT and a and a[0] in ("log", "rev-list", "ls-files"): return cob._git(cwd, *a)  # lectura repetida: cache por (HEAD, origin/main, dia)
    return sh(["git", *a], cwd=cwd, check=check)

def db():
    STATE.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, clave TEXT UNIQUE, tipo TEXT, area TEXT, estado TEXT,
      payload TEXT, intentos INTEGER DEFAULT 0, no_antes TEXT, error TEXT, creado TEXT, actualizado TEXT);
    CREATE TABLE IF NOT EXISTS analisis(area TEXT, fecha TEXT, head TEXT, fuente_sha TEXT);
    CREATE TABLE IF NOT EXISTS propuestas(id INTEGER PRIMARY KEY, huella TEXT UNIQUE, area TEXT, titulo TEXT, datos TEXT,
      estado TEXT, veredicto TEXT, rama TEXT, creado TEXT, actualizado TEXT);
    CREATE TABLE IF NOT EXISTS peticiones(fecha TEXT, hora TEXT, tipo TEXT, area TEXT, chars_in INTEGER, chars_out INTEGER, ok INTEGER);
    CREATE TABLE IF NOT EXISTS ramas(rama TEXT PRIMARY KEY, area TEXT, ruta TEXT, sha TEXT, estado TEXT, pr INTEGER, url TEXT);
    """)
    cob.migrar(c); cob.sembrar_tecnicas(c, CFG, now()); c.commit()
    import qa_lote; qa_lote.migrar(c)
    import qa_triaje; qa_triaje.migrar(c)
    return c

def pid_alive(pid):
    """PID exacto (columna 2 del CSV de tasklist); `str(pid) in salida` daba falsos positivos con cifras de memoria."""
    for ln in sh(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], check=False).splitlines():
        cols = [x.strip('"') for x in ln.split('","')]
        if len(cols) > 1 and cols[1] == str(pid): return True
    return False

def es_qa_gpt(pid):
    """Evita matar un PID reutilizado por otro programa."""
    out = sh(["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}').CommandLine"], check=False)
    return "qa_gpt.py" in out

class Lock:
    """Un unico trabajador a la vez; recupera bloqueos de procesos muertos."""
    path = STATE / "worker.lock"
    def __enter__(self):
        STATE.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try: pid = int(self.path.read_text().split()[0])
            except Exception: pid = 0
            if pid and pid != os.getpid() and pid_alive(pid):
                try: edad = (_ahora() - dt.datetime.fromisoformat(self.path.read_text().split(None, 1)[1].strip())).total_seconds() / 60
                except Exception: edad = 0
                if edad <= CFG.get("worker_max_min", 120) or not es_qa_gpt(pid):
                    raise SystemExit(f"Ya hay un trabajador en marcha (pid {pid}, {int(edad)} min).")
                print(f"Trabajador colgado (pid {pid}, {int(edad)} min > {CFG.get('worker_max_min', 120)}): se termina y se toma el relevo")
                sh(["taskkill", "/PID", str(pid), "/T", "/F"], check=False); time.sleep(2)
        self.path.write_text(f"{os.getpid()} {now()}")
        return self
    def __exit__(self, *a): self.path.unlink(missing_ok=True)
    @classmethod
    def latido(cls):
        """El servicio continuo renueva la marca: un lock viejo = trabajador colgado (relevo), no un servicio largo."""
        try: cls.path.write_text(f"{os.getpid()} {now()}")
        except OSError: pass

def flag(name): return (STATE / name).exists()

def _desenvolver_codeblock(text):
    """ChatGPT a veces entrega <CodeBlock ...>{`json`}</CodeBlock>: plantilla JS con \\, \` y \$ escapados."""
    m = re.search(r"<CodeBlock[^>]*>\s*\{`(.*)`\s*\}\s*</CodeBlock>", text, re.S)
    if not m:  # variante sin plantilla: <CodeBlock ...>{json}</CodeBlock>
        return re.sub(r"</?CodeBlock[^>]*>", "", text)
    return re.sub(r"\\([\\`$])", r"\1", m.group(1))

def load_json_block(text):
    text = _desenvolver_codeblock(text)
    t = re.sub(r"```(?:json)?", "", text)
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j < i: raise ValueError("sin bloque JSON")
    return json.loads(t[i:j + 1])

def enqueue_revision(c, area, pid):
    """Cada intento lleva su ordinal: un job R fallido no impide reencolar (la clave UNIQUE dejo #1 sin salida)."""
    n = c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='R' AND payload=?", (json.dumps({"id": pid}),)).fetchone()[0]
    if n >= 3: return False
    c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", (f"revision GPT en cola (intento {n + 1})", pid))
    return enqueue(c, "R", area, {"id": pid}, f"R:{area}:{pid}:{n + 1}")

def reconciliar(c):
    """Toda propuesta no terminal debe tener un job vivo o una razon+siguiente paso; aqui se curan los huerfanos."""
    vivos = {"B": set(), "R": set()}
    for j in c.execute("SELECT tipo,payload FROM jobs WHERE estado IN ('pendiente','en_curso','manual') AND tipo IN ('B','R')"):
        p = json.loads(j["payload"]); vivos[j["tipo"]].update(p.get("ids") or [p.get("id")])
    for r in c.execute("SELECT id,area,estado,datos FROM propuestas WHERE estado IN ('propuesta','revisar')").fetchall():
        revisada = bool(json.loads(r["datos"]).get("revision"))
        if r["id"] in vivos["B"] or r["id"] in vivos["R"]: continue
        if r["estado"] == "propuesta":
            enqueue(c, "B", r["area"], {"ids": [r["id"]]}, f"B:{r['area']}:{r['id']}:rec{c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]}")
            c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", ("PASS B reencolado (no habia job vivo)", r["id"]))
        elif revisada:
            estado_prop(c, r["id"], "bloqueada", "revisada y sin decision definitiva")
            c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", ("`reabrir <id>` o `descartar <id> --motivo ...`", r["id"]))
        elif not enqueue_revision(c, r["area"], r["id"]):
            estado_prop(c, r["id"], "bloqueada", "3 revisiones fallidas")
            c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", ("`reabrir <id>` o `descartar <id> --motivo ...`", r["id"]))
    c.commit()

def estado_prop(c, pid, estado, nota="", **extra):
    sets = ",".join(f"{k}=?" for k in extra)
    c.execute(f"UPDATE propuestas SET estado=?,actualizado=?{',' + sets if sets else ''} WHERE id=?", (estado, now(), *extra.values(), pid))
    cob.evento(c, "propuesta", pid, estado, nota, now())


# ---------- inventario por areas curadas (semilla de riesgo) ----------
def expand(globs):
    out = []
    for g in globs:
        out += [Path(p).relative_to(ROOT).as_posix() for p in glob.glob(str(ROOT / g), recursive=True) if Path(p).is_file()]
    return sorted({p for p in out if not p.startswith(("node_modules/", ".ci/", "pagefind/"))})

def tests_for(area):
    kws = [k.lower() for k in area["tests_kw"]]
    pool = expand(["tests/*", "qa/*", ".github/workflows/*"])
    return [p for p in pool if any(k in Path(p).name.lower() for k in kws)]

def last_run(c, clave):
    return c.execute("SELECT fecha, fuente_sha, head FROM analisis WHERE area=? ORDER BY rowid DESC LIMIT 1", (clave,)).fetchone()

def dias_desde(last):
    return 30 if not last else (_ahora().date() - dt.date.fromisoformat(last["fecha"])).days

def area_stats(area, c):
    src = expand(area["fuentes"])
    sha = git("log", "-1", "--format=%h", "--", *src, check=False) if src else ""
    commits = int(git("rev-list", "--count", "--since=14 days ago", "HEAD", "--", *src, check=False) or 0) if src else 0
    return src, sha, commits, last_run(c, "zona:" + area["id"])

def priority(area, c):
    src, sha, commits, last = area_stats(area, c)
    ntests = len(tests_for(area)); dias = dias_desde(last)
    changed = bool(last and last["fuente_sha"] != sha)
    cooldown = bool(last) and dias < CFG["cooldown_dias"] and not changed
    score = area["riesgo"] * 2 + min(commits, 10) * 0.5 + min(dias, 30) / 3 + 9 / (1 + ntests) + (4 if changed else 0) + (0 if last else 3)
    return (-1 if cooldown else score), dict(ntests=ntests, commits=commits, dias=dias, changed=changed, sha=sha, nsrc=len(src))


# ---------- contexto y peticiones ----------
def fill(tpl, **kv):
    for k, v in kv.items(): tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl

def budget(c, ronda):
    """Sin cupo diario ni por ronda: solo se respetan los limites reales de ChatGPT (RateLimited). Devuelve (True, peticiones de hoy)."""
    return True, c.execute("SELECT COUNT(*) FROM peticiones WHERE fecha=?", (today(),)).fetchone()[0]

def enqueue(c, tipo, area, payload, clave):
    try:
        c.execute("INSERT INTO jobs(clave,tipo,area,estado,payload,no_antes,creado,actualizado,modo) VALUES(?,?,?,?,?,?,?,?,?)",
                  (clave, tipo, area, "pendiente", json.dumps(payload), now(), now(), now(), area.split(":", 1)[0])); c.commit(); return True
    except sqlite3.IntegrityError:
        return False

AREAS = {a["id"]: a for a in CFG["areas"]}
TIPOS = {t["id"]: t for t in CFG["tipos"]}

def tipo_tests(t):
    kws = [k.lower() for k in t["kw"]]
    return [p for p in expand(["tests/*", "qa/*", ".github/workflows/*"]) if any(k in Path(p).name.lower() for k in kws)]

def tipo_huecos(t):
    kws = [k.lower() for k in t["kw"]]
    cubiertas = [a["id"] for a in CFG["areas"] if any(any(k in Path(p).name.lower() for k in kws) for p in tests_for(a))]
    return cubiertas, [a for a in CFG["areas"] if a["id"] not in cubiertas]


# ---------- seleccion de trabajo (modos y rotacion) ----------
def matriz(c, forzar=False):
    return cob.construir(c, ROOT, CFG, now(), forzar)

def candidates(c, modo):
    """[(puntuacion, clave, payload)] ordenados; puntuacion < 0 = en descanso/no elegible."""
    out = []
    if modo == "zona":
        for a in CFG["areas"]:
            sc, st = priority(a, c); out.append((sc, "zona:" + a["id"], {"motivo": f"prioridad {sc:.1f}; tests {st['ntests']}; commits14d {st['commits']}; " + ("fuentes cambiadas" if st["changed"] else f"{st['dias']} dias sin analizar"), "sha": st["sha"]}))
    elif modo == "tipo":
        for t in CFG["tipos"]:
            cub, hue = tipo_huecos(t); last = last_run(c, "tipo:" + t["id"]); dias = dias_desde(last)
            sc = sum(a["riesgo"] for a in hue) * (1.5 if cub else 0.7) + min(dias, 30) / 3
            out.append((-1 if (last and dias < CFG["cooldown_tipo_dias"]) else sc, "tipo:" + t["id"], {"motivo": f"{len(hue)} areas sin el tipo, {len(cub)} con patron", "sha": ""}))
    elif modo == "familia":
        cruces = {r[0]: r[1] for r in c.execute("SELECT familia, COUNT(*) FROM cruces WHERE estado='pendiente' GROUP BY familia")}
        bugs = {}
        for r in c.execute("SELECT familias FROM propuestas WHERE estado IN ('aceptada','preparada','aprobada','ejecutada') AND datos LIKE '%\"descubre_defecto\"%'"):
            for f in json.loads(r[0] or "[]"): bugs[f] = bugs.get(f, 0) + 1
        for fam, d in matriz(c).items():
            last = last_run(c, "familia:" + fam); dias = dias_desde(last); changed = bool(last and last["fuente_sha"] != d["sha"])
            hay = d["huecos"] or cruces.get(fam) or changed
            sc = d["riesgo"] * 2 + min(d["commits14d"], 10) * 0.5 + min(len(d["huecos"]), 8) * 0.8 + 9 / (1 + d["tests_propios"]) + (4 if changed else 0) + (3 if not last else 0) + 2 * cruces.get(fam, 0) + 1.5 * bugs.get(fam, 0)
            frio = bool(last) and dias < CFG["cooldown_familia_dias"] and not changed
            out.append((-1 if (frio or not hay) else sc, "familia:" + fam, {"motivo": f"{len(d['huecos'])} tecnicas sin cubrir, {d['tests_propios']} tests propios, commits14d {d['commits14d']}" + ("; fuentes cambiadas" if changed else ""), "sha": d["sha"]}))
    elif modo == "cambio":
        base = git("rev-parse", "--short", "origin/main", check=False); dias = CFG["ventana_cambio_dias"]
        n = int(git("rev-list", "--count", f"--since={dias} days ago", "origin/main", check=False) or 0); last = last_run(c, "cambio:reciente")
        sc = 5 + min(n, 20) * 0.4
        out.append((-1 if (n == 0 or (last and (last["head"] == base or dias_desde(last) < CFG["cooldown_cambio_dias"]))) else sc, "cambio:reciente", {"motivo": f"{n} commits en {dias} dias", "sha": base}))
    else:  # auditoria
        for a in CFG["areas"]:
            n = len(tests_for(a)); last = last_run(c, "audit:" + a["id"]); dias = dias_desde(last)
            sc = a["riesgo"] + n * 0.15 + min(dias, 30) / 3
            out.append((-1 if (n < 3 or (last and dias < CFG["cooldown_auditoria_dias"])) else sc, "audit:" + a["id"], {"motivo": f"{n} tests, {dias} dias", "sha": ""}))
    return sorted(out, key=lambda t: -t[0])

def elegir_modo(c):
    """Rotacion dinamica: el modo con menos analisis en 7 dias entre los que tienen algo elegible; empate -> mayor prioridad."""
    corte = (_ahora().date() - dt.timedelta(days=7)).isoformat(); elig = []
    for modo in dict.fromkeys(CFG["ciclo"]):
        sc, clave, pl = candidates(c, modo)[0]
        if sc < 0: continue
        pref = {"audit": "audit:"}.get(modo, modo + ":") if modo != "auditoria" else "audit:"
        n7 = c.execute("SELECT COUNT(*) FROM analisis WHERE area LIKE ? AND fecha>=?", (pref + "%", corte)).fetchone()[0]
        elig.append((n7, -sc, modo, clave, pl))
    return min(elig)[2:] if elig else None


# ---------- prompts ----------
def lote_activo(): return CFG.get("modo_generacion") == "lote"
def tope_propuestas(): return CFG.get("max_propuestas_lote", 15) if lote_activo() else CFG["max_propuestas"]


def prompt_for(job, c):
    """Prompt compacto SIN adjuntos: el Project lee el repo por GitHub; solo se le dan rutas y contexto minimo."""
    p = json.loads(job["payload"]); head = git("rev-parse", "--short", "origin/main")
    modo, ident = job["area"].split(":", 1)
    if job["tipo"] == "T":
        import qa_triaje; return qa_triaje.prompt(sys.modules[__name__], job, c)
    if job["tipo"] == "A":
        blk = {"zona": "modo_zona", "tipo": "modo_tipo", "audit": "modo_auditoria", "familia": "modo_familia", "cambio": "modo_cambio"}[modo]
        tpl = (HERE / "prompts" / f"{blk}.txt").read_text(encoding="utf-8")
        if modo == "tipo":
            t = TIPOS[ident]; cub, hue = tipo_huecos(t)
            blk_txt = fill(tpl, NOMBRE=t["nombre"], ID=ident, TESTS=", ".join(tipo_tests(t)[:15]) or "(ninguno: tipo nuevo)", HUECOS=", ".join(a["id"] + " [" + "; ".join(a["fuentes"][:3]) + "]" for a in hue) or "(ninguna)")
        elif modo == "familia":
            d = matriz(c)[ident]
            cr = [f"{r['familia']}←#{r['propuesta']}({r['tecnica']})" for r in c.execute("SELECT * FROM cruces WHERE familia=? AND estado='pendiente'", (ident,))]
            blk_txt = fill(tpl, ID=ident, FICHEROS=d["ficheros"], RASGOS=",".join(d["rasgos"]), TESTS=", ".join(d["ejemplos_tests"]) or "(ninguno propio; puede haber tests globales)",
                           CUBIERTAS=", ".join(d["tecnicas_cubiertas"]) or "(ninguna)", HUECOS=", ".join(d["huecos"][:12]) or "(ninguno por heuristica)",
                           CRUCES=", ".join(cr) or "(ninguno)")
        elif modo == "cambio":
            dias = CFG["ventana_cambio_dias"]
            commits = git("log", f"--since={dias} days ago", "-14", "--format=%h %s", "origin/main", check=False)
            fams = sorted({f.split("/")[0] if "/" in f else "(raiz)" for f in git("log", f"--since={dias} days ago", "--name-only", "--format=", "origin/main", check=False).splitlines() if f})
            blk_txt = fill(tpl, DIAS=dias, COMMITS=commits or "(ninguno)", FAMILIAS=", ".join(fams[:25]))
        else:
            a = AREAS[ident]
            commits = git("log", "--since=14 days ago", "-6", "--format=%h %s", "--", *expand(a["fuentes"]), check=False) or "(ninguno)"
            blk_txt = fill(tpl, NOMBRE=a["nombre"], ID=ident, FUENTES=", ".join(a["fuentes"]), TESTS=", ".join(Path(x).name for x in tests_for(a)[:30]) or "(ninguno)", COMMITS=commits)
        prev = " | ".join(r["titulo"][:70] for r in c.execute("SELECT titulo FROM propuestas ORDER BY id DESC LIMIT 15")) or "(ninguno)"
        tecs = ", ".join(t["id"] for t in cob.tecnicas(c))
        plantilla = "pass_lote_v1.txt" if CFG.get("modo_generacion") == "lote" else "pass_a_v2.txt"
        return fill((HERE / "prompts" / plantilla).read_text(encoding="utf-8"), MODO=modo, HEAD_SHA=head, MODO_INSTRUCCIONES=blk_txt, PREVIOS=prev, TECNICAS=tecs, MAX_PROPUESTAS=tope_propuestas())
    if job["tipo"] == "R":
        r = c.execute("SELECT datos, veredicto FROM propuestas WHERE id=?", (p["id"],)).fetchone(); v = json.loads(r["veredicto"])
        return fill((HERE / "prompts" / "pass_revision_v1.txt").read_text(encoding="utf-8"), HEAD_SHA=head, PROPUESTA=r["datos"],
                    OBJECIONES=json.dumps({k: v.get(k) for k in ("motivos", "cambios_requeridos", "pasa_hoy")}, ensure_ascii=False))
    rows = c.execute("SELECT id, datos FROM propuestas WHERE id IN (%s)" % ",".join("?" * len(p["ids"])), p["ids"]).fetchall()
    props = json.dumps([{"id": r["id"], **json.loads(r["datos"]), "verificacion_local": verif_local(json.loads(r["datos"]))} for r in rows], ensure_ascii=False)
    return fill((HERE / "prompts" / "pass_b_v2.txt").read_text(encoding="utf-8"), HEAD_SHA=head, CONTEXTO=job["area"], PROPUESTAS_JSON=props)


# ---------- peticion robusta: envio -> captura -> validacion -> guardado -> cierre de pestana ----------
class RespuestaInvalida(ValueError):
    pass

def existe_en_main(ruta):
    return cob.run(["git", "cat-file", "-e", f"origin/main:{ruta}"], cwd=ROOT, capture_output=True).returncode == 0

def validar_lectura(data, herramientas):
    """Una respuesta sin lectura verificable del repo se trata como INCOMPLETA (no se aceptan conjeturas)."""
    lr = data.get("lectura_repo")
    if not isinstance(lr, dict) or not lr.get("ficheros_leidos"): raise RespuestaInvalida("sin lectura_repo.ficheros_leidos: el repo no se leyo")
    if herramientas is not None and herramientas < 1: raise RespuestaInvalida("el chat no registra ninguna lectura del conector GitHub")
    leidos = [f for f in lr["ficheros_leidos"] if isinstance(f, str)]
    reales = [f for f in leidos if existe_en_main(f)]
    if not reales or len(reales) < len(leidos) / 2: raise RespuestaInvalida(f"lectura_repo cita rutas inexistentes en main ({len(reales)}/{len(leidos)})")
    com = str(lr.get("commit", "")).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{7,40}", com): raise RespuestaInvalida("lectura_repo.commit no es un sha")
    return len(reales)

def verif_local(d):
    """Comprobaciones NO ejecutantes sobre los bytes exactos guardados: sintaxis, sha256, existencia en main y parches aplicables.
    Se entrega a PASS B porque GPT ve su mensaje con escapes de Markdown que no existen en el fichero real."""
    import tempfile
    out = {"commit_base": git("rev-parse", "--short", "origin/main", check=False), "ficheros_nuevos": [], "parches": []}
    for f in d.get("ficheros_nuevos") or []:
        rel, txt = f.get("ruta", ""), f.get("contenido", "")
        it = {"ruta": rel, "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16], "bytes": len(txt.encode("utf-8")), "ya_existe_en_main": existe_en_main(rel)}
        try:
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / Path(rel).name; tmp.write_text(txt, encoding="utf-8", newline="\n"); syntax_check(tmp)
            it["sintaxis"] = "OK (ast.parse/node --check sobre los bytes guardados)"
        except Exception as e: it["sintaxis"] = f"ERROR: {str(e)[:200]}"
        it["artefactos_markdown"] = bool(re.search(r"\\_\\_|\]\(https?://", txt))
        out["ficheros_nuevos"].append(it)
    for m in d.get("ficheros_modificados") or []:
        out["parches"].append({"ruta": m.get("ruta"), "aplica_sobre_main": parche_aplica(m)})
    return out

def parche_aplica(m):
    """git apply --check contra origin/main con un indice temporal: no toca el arbol de trabajo."""
    import tempfile
    if not m.get("parche"): return "sin parche unified_diff (no preparable)"
    rel = m.get("ruta", "")
    if not re.match(r"^(\.github/workflows/[\w.-]+\.yml|(tests|qa)/[\w./-]+)$", rel) or ".." in rel: return f"ruta no permitida: {rel}"
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(td) / "idx")}
        cob.run(["git", "read-tree", "origin/main"], cwd=ROOT, env=env, capture_output=True)
        pf = Path(td) / "p.diff"; pf.write_text(m["parche"], encoding="utf-8", newline="\n")
        r = cob.run(["git", "apply", "--cached", "--check", str(pf)], cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return "OK" if r.returncode == 0 else f"NO APLICA: {r.stderr.strip()[:160]}"

def guardar_respuesta(job, cid, texto):
    d = STATE / "respuestas"; d.mkdir(parents=True, exist_ok=True)
    f = d / f"job{job['id']}-{(cid or 'manual')[:8]}.txt"; f.write_text(texto, encoding="utf-8"); return f

def process(job, c, manual=False):
    text = prompt_for(job, c)
    if manual:
        d = STATE / "manual"; d.mkdir(exist_ok=True)
        (d / f"job{job['id']}.prompt.txt").write_text(text, encoding="utf-8")
        c.execute("UPDATE jobs SET estado='manual',actualizado=? WHERE id=?", (now(), job["id"])); c.commit()
        print(f"  manual: {d}/job{job['id']}.prompt.txt . Pega la respuesta con: ingest {job['id']} fichero.json"); return
    import gpt_browser as g
    jid, area = job["id"], job["area"]
    # 1) respuesta ya capturada y guardada pero sin ingerir (caida entre captura e ingesta): no se vuelve a preguntar
    if job["respuesta"] and Path(job["respuesta"]).exists():
        print(f"  reingesta desde {job['respuesta']}")
        try: return ingest_answer(c, job, Path(job["respuesta"]).read_text(encoding="utf-8"), None)
        except Exception as e: return fallo(c, job, f"reingesta: {e}", nuevo_chat=True)
    reanudar = job["chat_id"] if job["fase"] == "generando" else None
    if not reanudar:
        c.execute("UPDATE jobs SET intentos=intentos+1 WHERE id=?", (jid,))
    c.execute("UPDATE jobs SET estado='en_curso',actualizado=? WHERE id=?", (now(), jid)); c.commit()
    t0 = time.monotonic(); estado_peticion = {"cid": reanudar}

    def on_chat(cid):  # chat creado: persistir YA (permite reanudar si todo se cae)
        estado_peticion["cid"] = cid
        c.execute("UPDATE jobs SET chat_id=?,fase='generando',actualizado=? WHERE id=?", (cid, now(), jid))
        c.execute("INSERT INTO peticiones(fecha,hora,tipo,area,chars_in,chars_out,ok,chat_id,estado) VALUES(?,?,?,?,?,?,?,?,?)",
                  (today(), now(), job["tipo"], area, len(text), 0, 0, cid, "enviada")); c.commit()

    def on_result(res):  # respuesta COMPLETA: validar y guardar antes de que se cierre la pestana
        if not res.texto.strip(): raise RespuestaInvalida("respuesta vacia")
        f = guardar_respuesta(job, res.cid, res.texto)
        c.execute("UPDATE jobs SET respuesta=?,fase='capturada',actualizado=? WHERE id=?", (str(f), now(), jid))
        c.execute("UPDATE peticiones SET chars_out=?,ok=1,estado='terminada',herramientas=?,segundos=? WHERE chat_id=?", (len(res.texto), res.herramientas, int(time.monotonic() - t0), res.cid)); c.commit()
        estado_peticion["res"] = res
        load_json_block(res.texto)  # nada se da por bueno si no es JSON

    try:
        res = g.ask(text, CFG["espera_respuesta_min"], CFG["stall_min"], on_chat, on_result, resume_cid=reanudar)
    except g.LoginRequired:
        c.execute("UPDATE jobs SET estado='pendiente',error='login',actualizado=? WHERE id=?", (now(), jid)); c.commit()
        raise SystemExit("ChatGPT sin sesion en el Edge 9230: inicia sesion y relanza (la cola se conserva).")
    except g.RateLimited as e:
        (STATE / "limite").write_text(now())
        c.execute("UPDATE jobs SET estado='pendiente',error=?,no_antes=?,actualizado=? WHERE id=?", (str(e), (_ahora() + dt.timedelta(minutes=5)).isoformat(timespec="seconds"), jid)); c.commit()
        raise SystemExit("Limite de uso de ChatGPT: pausa con espera escalonada (no se reintenta en bucle).")
    except g.Incompleta as e:
        cid = e.cid or estado_peticion.get("cid")
        c.execute("UPDATE peticiones SET estado=? WHERE chat_id=?", (e.estado, cid)); c.commit()
        if e.estado in ("generando", "estancada", "backend") and cid:  # recuperable: se conserva el chat, se reanuda sin reenviar
            edad = (_ahora() - dt.datetime.fromisoformat(job["creado"])).total_seconds() / 3600
            if edad > CFG["reanudar_max_horas"]:
                c.execute("UPDATE jobs SET estado='error',error=?,actualizado=? WHERE id=?", (f"{e} (>{CFG['reanudar_max_horas']} h)", now(), jid))
            else:
                nb = (_ahora() + dt.timedelta(minutes=CFG["backoff_min"][0])).isoformat(timespec="seconds")
                c.execute("UPDATE jobs SET estado='pendiente',chat_id=?,fase='generando',error=?,no_antes=?,actualizado=? WHERE id=?", (cid, str(e)[:300], nb, now(), jid))
            c.commit(); print(f"  INCOMPLETA ({e.estado}), chat conservado para reanudar: {e}"); return
        return fallo(c, job, f"{e}", nuevo_chat=True)
    except RespuestaInvalida as e:
        return fallo(c, job, f"respuesta invalida: {e}", nuevo_chat=True)
    except Exception as e:
        cid = estado_peticion.get("cid")
        if cid and "res" not in estado_peticion and job["fase"] != "capturada":  # fallo tecnico con chat creado: reanudable
            c.execute("UPDATE jobs SET estado='pendiente',chat_id=?,fase='generando',error=?,no_antes=?,actualizado=? WHERE id=?", (cid, str(e)[:300], (_ahora() + dt.timedelta(minutes=CFG["backoff_min"][0])).isoformat(timespec="seconds"), now(), jid)); c.commit()
            print(f"  fallo tecnico, chat conservado: {str(e)[:160]}"); return
        return fallo(c, job, str(e), nuevo_chat=True)
    try:
        ingest_answer(c, job, res.texto, res.herramientas)
    except Exception as e:  # la respuesta esta guardada en disco: se puede reingerir sin volver a preguntar
        fallo(c, job, f"ingesta: {e}", nuevo_chat=False)

def fallo(c, job, err, nuevo_chat=True):
    n = c.execute("SELECT intentos FROM jobs WHERE id=?", (job["id"],)).fetchone()[0]
    reset = ",chat_id=NULL,fase=NULL,respuesta=NULL" if nuevo_chat else ""
    if n > CFG["reintentos"]:
        c.execute(f"UPDATE jobs SET estado='error',error=?,actualizado=?{reset} WHERE id=?", (err[:300], now(), job["id"]))
    else:
        nb = (_ahora() + dt.timedelta(minutes=CFG["backoff_min"][min(n - 1, len(CFG["backoff_min"]) - 1)])).isoformat(timespec="seconds")
        c.execute(f"UPDATE jobs SET estado='pendiente',error=?,no_antes=?,actualizado=?{reset} WHERE id=?", (err[:300], nb, now(), job["id"]))
    c.commit(); print(f"  fallo (intento {n}/{CFG['reintentos'] + 1}): {err[:160]}")


# ---------- ingesta ----------
def ingest_answer(c, job, answer, herramientas):
    data = load_json_block(answer)
    if not isinstance(data, dict): raise ValueError("la respuesta no es un objeto JSON")
    if job["tipo"] == "T":
        import qa_triaje; qa_triaje.ingest(sys.modules[__name__], c, job, data)
        c.execute("UPDATE jobs SET estado='hecho',error=NULL,actualizado=? WHERE id=?", (now(), job["id"])); c.commit()
        try: __import__("qa_pr").correr(sys.modules[__name__], c)  # defecto real con parche validado -> PR (sin merge); un fallo aqui no afecta al analisis
        except Exception as e: print(f"  PR automatica omitida: {str(e)[:160]}")
        return
    n_leidos = validar_lectura(data, herramientas)
    area = job["area"]
    if job["tipo"] == "R":
        pid = json.loads(job["payload"])["id"]; new = (data.get("propuestas") or [None])[0]
        if new:
            new["revision"] = 1
            cob.normalizar_comandos(new)
            d = cob.datos_prop(new)
            c.execute("UPDATE propuestas SET datos=?,tecnica=?,funcionalidad=?,huella_conductual=?,fuente_sha=? WHERE id=?",
                      (json.dumps(new, ensure_ascii=False), d["tecnica"], d["funcionalidad"], d["huella"], cob.sha_fuentes(ROOT, d["fuentes"]), pid))
            estado_prop(c, pid, "propuesta", "revision enviada a PASS B")
            enqueue(c, "B", area, {"ids": [pid]}, f"B:{area}:{pid}:rev1")
        print(f"  REVISION {area} #{pid}: {'reenviada a PASS B' if new else 'sin propuesta'}")
    elif job["tipo"] == "A":
        ids, desc, dups = [], 0, 0
        for pr in data.get("propuestas", [])[: tope_propuestas()]:
            cob.normalizar_comandos(pr)
            d = cob.datos_prop(pr)
            malas = [f for f in d["fuentes"] if not existe_en_main(f)]
            if not d["fuentes"] or malas:
                desc += 1; print(f"  descartada (fuentes inexistentes/ausentes): {pr.get('titulo', '?')[:60]} {malas[:2]}"); continue
            vl = verif_local(pr)
            roto = [x for x in vl["ficheros_nuevos"] if x["sintaxis"].startswith("ERROR") or x["ya_existe_en_main"]]
            if roto:
                desc += 1; print(f"  descartada (sintaxis/ruta): {pr.get('titulo', '?')[:60]} {roto[0]['ruta']}: {roto[0]['sintaxis'][:80]}"); continue
            previa, motivo = cob.buscar_duplicado(c, ROOT, pr)
            if previa:
                dups += 1; cob.evento(c, "propuesta", previa["id"], "duplicada_detectada", f"{pr.get('titulo', '?')[:80]} :: {motivo}", now())
                print(f"  duplicada: {pr.get('titulo', '?')[:60]} -> {motivo}"); continue
            h = hashlib.sha1((area + pr.get("titulo", "") + json.dumps([f.get("ruta") for f in pr.get("ficheros_nuevos", [])])).encode()).hexdigest()[:16]
            try:
                cur = c.execute("INSERT INTO propuestas(huella,area,titulo,datos,estado,creado,actualizado,tecnica,funcionalidad,huella_conductual,fuente_sha,familias) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                                (h, area, pr.get("titulo", "?")[:200], json.dumps({**pr, "via": "lote"} if lote_activo() else pr, ensure_ascii=False), "aceptada" if lote_activo() else "propuesta", now(), now(), d["tecnica"], d["funcionalidad"], d["huella"],
                                 cob.sha_fuentes(ROOT, d["fuentes"]), json.dumps(pr.get("familias") or sorted({f.split('/')[0] for f in d["fuentes"]}))))
            except sqlite3.IntegrityError:
                dups += 1; continue
            pid = cur.lastrowid; ids.append(pid); cob.evento(c, "propuesta", pid, "propuesta", f"{area} tecnica={d['tecnica']}", now())
            t = pr.get("tecnica") if isinstance(pr.get("tecnica"), dict) else {"id": d["tecnica"]}
            if cob.registrar_tecnica(c, {**t, "id": d["tecnica"]}, now(), pid): print(f"  TECNICA NUEVA registrada: {d['tecnica']}")
            for e in pr.get("equivalentes_a_revisar") or []:
                if isinstance(e, dict) and e.get("familia"): c.execute("INSERT OR IGNORE INTO cruces(propuesta,familia,tecnica) VALUES(?,?,?)", (pid, e["familia"], d["tecnica"]))
        ident = area.split(":", 1)[1]
        fsha = area_stats(AREAS[ident], c)[1] if area.startswith(("zona:", "audit:")) else (json.loads(job["payload"]).get("sha", "") if area.startswith(("familia:", "cambio:")) else "")
        c.execute("INSERT INTO analisis VALUES(?,?,?,?)", (area, today(), git("rev-parse", "--short", "origin/main"), fsha))
        if ids and not lote_activo(): enqueue(c, "B", area, {"ids": ids}, f"B:{area}:{','.join(map(str, ids))}")
        print(f"  PASS A {area}: {len(ids)} nuevas, {dups} duplicadas, {desc} descartadas; lectura repo: {n_leidos} ficheros verificados")
    else:
        ids = json.loads(job["payload"])["ids"]; n = {"aceptar": 0, "revisar": 0, "rechazar": 0}; vistos = set()
        for d in data.get("decisiones", []):
            pid = d.get("id")
            if pid not in ids: continue
            vistos.add(pid); v = d.get("veredicto", "rechazar")
            if v not in n: v = "rechazar"
            r = c.execute("SELECT datos FROM propuestas WHERE id=?", (pid,)).fetchone()
            cat = d.get("categoria_correcta") or json.loads(r["datos"]).get("categoria")
            if v == "aceptar" and ((cat == "regresion" and d.get("pasa_hoy") == "no") or (cat == "descubre_defecto" and d.get("detecta_el_defecto") == "no")): v = "revisar"
            n[v] += 1
            est = {"aceptar": "aceptada", "revisar": "revisar", "rechazar": "rechazada"}[v]
            estado_prop(c, pid, est, "; ".join(d.get("motivos", []))[:200], veredicto=json.dumps(d, ensure_ascii=False))
            if v == "revisar":
                if json.loads(r["datos"]).get("revision"):
                    estado_prop(c, pid, "bloqueada", "; ".join(d.get("cambios_requeridos") or d.get("motivos", []))[:200], veredicto=json.dumps(d, ensure_ascii=False))
                    c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", ("revision agotada tras PASS B: decidir `reabrir <id>` (reevalua con el contexto actual) o `descartar <id> --motivo ...`", pid))
                else:
                    enqueue_revision(c, area, pid)
        falt = [i for i in ids if i not in vistos]
        if falt: enqueue(c, "B", area, {"ids": falt}, f"B:{area}:{','.join(map(str, falt))}:faltan"); print(f"  PASS B sin decision para {falt}: reencolado")
        print(f"  PASS B {area}: {n}")
    c.execute("UPDATE jobs SET estado='hecho',error=NULL,fase='ingerida',actualizado=? WHERE id=?", (now(), job["id"])); c.commit()


# ---------- preparacion local (sin ejecutar tests) ----------
OK_PATH = re.compile(r"^(tests|qa)/[A-Za-z0-9_./-]+\.(py|mjs|js)$")

def validate_files(files):
    import gpt_browser
    for f in files:
        rel = f.get("ruta", "")
        if not OK_PATH.match(rel) or ".." in rel: raise ValueError(f"ruta no permitida: {rel}")
        if (ROOT / rel).exists() or existe_en_main(rel): raise ValueError(f"ya existe (no se sobrescribe): {rel}")
        if c_dup(rel): raise ValueError(f"ya preparado en otra rama/propuesta: {rel}")
        if gpt_browser.TOKEN_RE.search(f.get("contenido", "")): raise ValueError(f"posible secreto en {rel}")

def c_dup(rel):
    """Ruta ya reservada por otra propuesta preparada/aprobada (evita dos implementaciones del mismo fichero)."""
    c = sqlite3.connect(DB_PATH, timeout=30)
    try:
        for (d,) in c.execute("SELECT datos FROM propuestas WHERE estado IN ('preparada','aprobada','publicada')"):
            if rel in [f.get("ruta") for f in json.loads(d).get("ficheros_nuevos", [])]: return True
    finally: c.close()
    return False

def syntax_check(path):
    """Solo parseo; no ejecuta el test."""
    if path.suffix == ".py": sh([sys.executable, "-c", "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())", str(path)])
    else: sh(["node", "--check", str(path)])

def reparar_perdidas(c):
    """Una propuesta `preparada` cuyos ficheros no estan en el commit de su rama no es un test ejecutable (la perdio un rollback o un commit
    interrumpido): vuelve a `aceptada` para que stage la prepare de nuevo desde su contenido guardado. Un solo proceso git para todas."""
    ramas = {r["rama"]: r["sha"] for r in c.execute("SELECT rama,sha FROM ramas")}
    props = [(r["id"], r["rama"], json.loads(r["datos"])) for r in c.execute("SELECT id,rama,datos FROM propuestas WHERE estado='preparada'") if r["rama"] in ramas]
    pares = [(pid, f"{ramas[rama]}:{f['ruta']}") for pid, rama, d in props for f in d.get("ficheros_nuevos") or []]
    if not pares: return 0
    r = cob.run(["git", "cat-file", "--batch-check"], cwd=ROOT, input="".join(spec + "\n" for _, spec in pares), capture_output=True, text=True, encoding="utf-8", errors="replace")
    sal = r.stdout.splitlines()
    if r.returncode or len(sal) != len(pares): return 0  # sin certeza no se toca nada
    perdidas = sorted({pid for (pid, _), ln in zip(pares, sal) if ln.endswith(" missing")})
    for pid in perdidas: estado_prop(c, pid, "aceptada", "ficheros ausentes del commit de la rama: se prepara de nuevo", siguiente="reparada: pendiente de preparar otra vez")
    if perdidas: c.commit(); print(f"  reparadas {len(perdidas)} propuestas sin fichero en su rama: {perdidas[:10]}")
    return len(perdidas)

def stage(c):
    reparar_perdidas(c)
    rows = c.execute("SELECT * FROM propuestas WHERE estado='aceptada' ORDER BY area, id").fetchall()
    if not rows: print("Nada aceptado pendiente de preparar."); return
    base = git("rev-parse", "origin/main")
    for area in sorted({r["area"] for r in rows}):
        branch = f"gpt-qa/{area.replace(':', '-')}-{today().replace('-', '')}"
        wt = WT / branch.replace("/", "_")
        if not wt.exists():
            WT.mkdir(parents=True, exist_ok=True)
            git("worktree", "add", "-b", branch, str(wt), base)
        done = []
        for r in [x for x in rows if x["area"] == area]:
            d = json.loads(r["datos"]); created = []; nuevos = []
            try:
                if d.get("tipo_propuesta") == "informe" or not d.get("ficheros_nuevos"):
                    estado_prop(c, r["id"], "informe", "informe sin fichero de test"); continue
                if d.get("via") != "lote" and not (d.get("mutacion_que_lo_rompe") and d.get("por_que_pasa_hoy")): raise ValueError("falta mutacion/por_que_pasa_hoy")
                validate_files(d["ficheros_nuevos"])
                mods = d.get("ficheros_modificados") or []
                for m in mods:
                    ap = parche_aplica(m)
                    if ap != "OK": raise ValueError(f"parche de {m.get('ruta')}: {ap}")
                for f in d["ficheros_nuevos"]:
                    p = wt / f["ruta"]; p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(f["contenido"], encoding="utf-8", newline="\n"); created.append(p); nuevos.append(p); syntax_check(p)
                for m in mods:
                    pf = wt.parent / f"{wt.name}-p{r['id']}.diff"; pf.write_text(m["parche"], encoding="utf-8", newline=chr(10))
                    try: git("apply", str(pf), cwd=wt)
                    finally: pf.unlink(missing_ok=True)
                    created.append(wt / m["ruta"])  # no se borra en rollback: se restaura con checkout
                git("add", "--", *[f["ruta"] for f in d["ficheros_nuevos"]], *[m["ruta"] for m in mods], cwd=wt)
                ver = hashlib.sha1("".join(f["contenido"] for f in d["ficheros_nuevos"]).encode()).hexdigest()[:10]
                estado_prop(c, r["id"], "preparada", f"rama {branch} base {base[:8]} v{ver}", rama=branch, base_sha=base[:10], version_test=ver, siguiente="esperando `aprobar` + noche autorizada; NO ejecutado")
                done.append(r["titulo"])
            except Exception as e:
                # solo se deshace ESTA propuesta: un `reset --hard` borraba tambien las anteriores del area, ya marcadas preparadas pero aun sin commit
                git("reset", "-q", "--", *[f["ruta"] for f in d.get("ficheros_nuevos") or []], cwd=wt, check=False)
                for p in nuevos: p.unlink(missing_ok=True)
                estado_prop(c, r["id"], "invalida", str(e)[:200], veredicto=str(e)[:300], siguiente="descartada: el diseño aceptado no se pudo preparar; `reabrir <id>` para nueva revision")
                print(f"  invalida #{r['id']}: {e}")
        if done:
            git("commit", "-q", "-m", f"test(qa-gpt/{area}): {len(done)} tests preparados por revision GPT\n\n" + "\n".join("- " + t for t in done) +
                "\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>", cwd=wt)
            cmds = sorted({json.loads(x["datos"]).get("como_ejecutar") or "" for x in rows if x["area"] == area})
            c.execute("INSERT INTO ramas(rama,area,ruta,sha,estado,pr,url,base_sha,comandos) VALUES(?,?,?,?,?,NULL,NULL,?,?) "
                      "ON CONFLICT(rama) DO UPDATE SET sha=excluded.sha,comandos=excluded.comandos,estado=CASE WHEN ramas.estado IN ('publicada','ejecutada') THEN ramas.estado ELSE 'preparada' END",
                      (branch, area, str(wt), git("rev-parse", "HEAD", cwd=wt), "preparada", base[:10], json.dumps([x for x in cmds if x])))
            print(f"  rama local {branch}: {len(done)} propuestas (sin push, sin tests)")
        c.commit()


# ---------- Edge dedicado: salud, memoria y pestanas ----------
def edge_info():
    out = sh(["powershell", "-NoProfile", "-Command",
              "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object {$_.CommandLine -like '*web-escritor-qa-gpt-edge*'} | Select-Object ProcessId,WorkingSetSize,CommandLine | ConvertTo-Json -Compress"], check=False)
    try: ps = json.loads(out) if out else []
    except Exception: ps = []
    ps = [ps] if isinstance(ps, dict) else ps
    main = [p["ProcessId"] for p in ps if "--type=" not in (p.get("CommandLine") or "")]
    return dict(n=len(ps), mb=sum(p.get("WorkingSetSize") or 0 for p in ps) // 1_000_000, main=main)

def edge_asegurar():
    """Edge 9230 vivo y bajo el limite de memoria. Reinicia SOLO el Edge del perfil qa-gpt y solo sin peticion activa (somos el unico worker)."""
    import edge_launcher
    if edge_launcher.alive() is None:
        print("Edge 9230 no responde: lanzandolo"); edge_launcher.main()
    else:
        inf = edge_info()
        if inf["mb"] > CFG["edge_mem_mb"] and inf["main"]:
            print(f"Edge 9230 usa {inf['mb']} MB (> {CFG['edge_mem_mb']}): reinicio controlado")
            for pid in inf["main"]: sh(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
            time.sleep(3); edge_launcher.main()

def limpiar_pestanas_cdp():
    """Cierra pestanas de ChatGPT ya guardadas/terminadas (nunca una generacion en curso)."""
    import gpt_browser
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        try:
            ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{gpt_browser.PORT}").contexts[0]
            n = gpt_browser.limpiar_pestanas(ctx)
            print(f"Pestanas: {n} cerradas; quedan {len([x for x in ctx.pages if 'chatgpt.com' in x.url])} de ChatGPT")
        finally: p.stop()
    except Exception as e: print(f"limpieza de pestanas omitida: {str(e)[:100]}")

def tabs_chatgpt():
    import edge_launcher
    try: return [t for t in edge_launcher.pages() if "chatgpt.com" in t["url"]]
    except Exception: return []


# ---------- comandos ----------
def cmd_setup(a):
    import edge_launcher
    c = db()
    if edge_launcher.main() != 0: return 1
    snap = STATE / "repo_map.md"
    lines = ["# Mapa compacto de web-escritor (generado)", f"main: {git('rev-parse', '--short', 'origin/main', check=False)}", "", "## Areas de QA"]
    for ar in CFG["areas"]:
        _, st = priority(ar, c)
        lines.append(f"- {ar['id']}: {ar['nombre']} | fuentes {st['nsrc']} | tests/workflows {st['ntests']} | commits14d {st['commits']}")
    lines += ["", "## Workflows", *[f"- {Path(p).name}" for p in expand([".github/workflows/*.yml"])]]
    snap.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSnapshot: {snap}\nProject: ver scripts/qa-gpt/project_instructions.md (comprobar con `verificar-project`).")

def cmd_inventario(a):
    c = db(); m = matriz(c, forzar=a.forzar)
    print(f"Matriz de cobertura: {len(m)} familias, {len(cob.tecnicas(c))} tecnicas ({c.execute('SELECT COUNT(*) FROM tecnicas WHERE origen=?', ('descubierta',)).fetchone()[0]} descubiertas)")
    print(f"{'familia':<28}{'ficheros':>8} {'tests':>5} {'glob':>4} {'commits14d':>10} {'huecos':>6}  rasgos")
    for f, d in sorted(m.items(), key=lambda t: -len(t[1]["huecos"]))[: a.top]:
        print(f"{f:<28}{d['ficheros']:>8} {d['tests_propios']:>5} {d['tests_globales']:>4} {d['commits14d']:>10} {len(d['huecos']):>6}  {','.join(d['rasgos'])}")

def cmd_status(a):
    c = db(); q = lambda s, *p: c.execute(s, p).fetchone()[0]
    try: sv = json.loads(SVC.read_text(encoding="utf-8"))
    except Exception: sv = {}
    pid = trabajador_vivo(); est = sv.get("estado", "parado") if pid else "PARADO"
    est = {"pausado_limite": f"PAUSADO por limite de ChatGPT hasta {sv.get('hasta')}", "login": "ESPERANDO inicio de sesion de ChatGPT (Edge 9230)", "esperando": f"EN MARCHA, sin trabajo util ahora (reintenta {sv.get('hasta')})",
           "ejecutando": "EN MARCHA", "arrancando": "ARRANCANDO", "pausado": "PAUSADO manualmente"}.get(est, est)
    print(f"Servicio: {est}" + (f" | pid {pid} desde {sv.get('inicio')}" if pid else ""))
    if pid and sv.get("tarea"): print(f"  Ahora: {sv['tarea']} sobre {sv.get('area')} (desde {sv.get('desde_tarea')})")
    ini = sv.get("inicio") or "9999"
    if pid:
        print(f"  Esta sesion: {q('SELECT COUNT(*) FROM peticiones WHERE hora>=?', ini)} peticiones | propuestas decididas {q('SELECT COUNT(*) FROM propuestas WHERE actualizado>=? AND estado IN (?,?,?,?)', ini, 'aceptada', 'preparada', 'aprobada', 'publicada')} aceptadas, "
              f"{q('SELECT COUNT(*) FROM propuestas WHERE actualizado>=? AND estado IN (?,?,?,?)', ini, 'rechazada', 'invalida', 'descartada', 'duplicada')} rechazadas")
    print(f"  Ultima actividad correcta: {sv.get('ultimo_ok') or '(ninguna)'} | ultimo error: {sv.get('ultimo_error') or '(ninguno)'}")
    ts = sh(["powershell", "-NoProfile", "-Command", f"try{{(Get-ScheduledTask -TaskName {TASK} -ErrorAction Stop).State}}catch{{'no existe'}}"], check=False)
    print(f"Tarea programada heredada {TASK}: {ts} (el servicio NO usa horarios)")
    print(f"Ejecucion de tests/Actions: {'AUTORIZADA hoy' if autorizada() else 'solo al pulsar EJECUTAR-ACTIONS-QA-GPT.bat (el servicio nunca los ejecuta)'}")
    print("Cola:", {r[0]: r[1] for r in c.execute("SELECT estado,COUNT(*) FROM jobs GROUP BY estado")})
    rean = c.execute("SELECT id,tipo,area,chat_id,error FROM jobs WHERE chat_id IS NOT NULL AND estado='pendiente' AND respuesta IS NULL").fetchall()
    for r in rean: print(f"  reanudable job{r[0]} {r[1]} {r[2]} chat {str(r[3])[:8]} ({(r[4] or '')[:70]})")
    print("Propuestas:", {r[0]: r[1] for r in c.execute("SELECT estado,COUNT(*) FROM propuestas GROUP BY estado")})
    print("  duplicadas detectadas:", q("SELECT COUNT(*) FROM eventos WHERE estado='duplicada_detectada'"), "| esperando aprobacion (preparada):", q("SELECT COUNT(*) FROM propuestas WHERE estado='preparada'"))
    print("Ramas:", {r[0]: r[1] for r in c.execute("SELECT estado,COUNT(*) FROM ramas GROUP BY estado")})
    ult = c.execute("SELECT hora,tipo,area,estado,herramientas,segundos FROM peticiones ORDER BY rowid DESC LIMIT 1").fetchone()
    if ult: print(f"Ultima peticion: {ult[0]} {ult[1]} {ult[2]} -> {ult[3]} (lecturas repo {ult[4]}, {ult[5]} s)")
    usadas = q("SELECT COUNT(*) FROM peticiones WHERE fecha=?", today()); tot = q("SELECT COUNT(*) FROM peticiones")
    utiles = q("SELECT COUNT(*) FROM propuestas WHERE estado IN ('aceptada','preparada','aprobada','publicada','ejecutada','informe')")
    print(f"Peticiones a ChatGPT: hoy {usadas}, total {tot} (sin cupo configurado; solo cuentan los limites reales de la cuenta)")
    n = lambda *es: q(f"SELECT COUNT(*) FROM propuestas WHERE estado IN ({','.join('?' * len(es))})", *es)
    defectos = q("SELECT COUNT(*) FROM lote_items WHERE estado='defecto_demostrado'")  # antes: LIKE '%descubre_defecto%true%' no casaba nunca (0 eterno)
    print(f"Ciclo de vida: descubiertas {q('SELECT COUNT(*) FROM propuestas')} | esperando PASS B {n('propuesta')} | con veredicto PASS B {q('SELECT COUNT(*) FROM propuestas WHERE veredicto IS NOT NULL AND estado<>?', 'propuesta')} "
          f"(aceptadas {n('aceptada', 'preparada', 'aprobada', 'publicada', 'ejecutada', 'informe')}, en revision {n('revisar')}, bloqueadas {n('bloqueada')}, rechazadas {n('rechazada', 'invalida', 'descartada', 'duplicada')}) | "
          f"parches generados {q('SELECT COUNT(*) FROM ramas')} | en rama local (STAGED) {n('preparada')} | ejecutadas {n('ejecutada', 'publicada')} | defectos de producto confirmados {defectos}")
    if Lock.path.exists():
        try: pid, desde = Lock.path.read_text().split(None, 1); print(f"Lock del trabajador: pid {pid} desde {desde.strip()} (vivo: {pid_alive(int(pid))})")
        except Exception: print("Lock del trabajador: ilegible")
    el = elegir_modo(c)
    print(f"Proxima ronda: {'modo ' + el[0] + ' -> ' + el[1] if el else 'todo en descanso'} (a partir de la hora de la tarea)")
    print(f"Tests preparados (rama local, sin ejecutar): {q('SELECT COUNT(*) FROM propuestas WHERE estado=?', 'preparada')} | aprobados esperando noche: {q('SELECT COUNT(*) FROM propuestas WHERE estado=?', 'aprobada')} (la aprobacion es el clic de EJECUTAR: antes es normal que sea 0) | ejecutados/validados: {q('SELECT COUNT(*) FROM propuestas WHERE estado IN (?,?)', 'ejecutada', 'publicada')}")
    vivas = set()
    for j in c.execute("SELECT payload FROM jobs WHERE estado IN ('pendiente','en_curso','manual') AND tipo IN ('B','R')"):
        p = json.loads(j[0]); vivas.update(p.get("ids") or [p.get("id")])
    for r in c.execute("SELECT id,estado,siguiente,titulo FROM propuestas WHERE estado IN ('revisar','bloqueada','invalida','propuesta')"):
        tag = "EN COLA " if r["id"] in vivas else ("BLOQUEADA (decide David)" if r["estado"] in ("bloqueada", "invalida") else "ESPERA (se reconcilia en la proxima ronda)")
        print(f"  {tag} #{r['id']} [{r['estado']}] {r['titulo'][:55]} -> {r['siguiente'] or '-'}")
    prob = [r for r in c.execute("SELECT id,error FROM jobs WHERE estado='pendiente' AND error IS NOT NULL")]
    print("Sesion/navegador:", "; ".join(f"job{r['id']}: {r['error'][:60]}" for r in prob) if prob else "sin incidencias pendientes")
    inf = edge_info(); tabs = tabs_chatgpt()
    print(f"Edge 9230: {'vivo' if inf['n'] else 'no corre'}, {inf['n']} procesos, {inf['mb']} MB (limite {CFG['edge_mem_mb']}) | pestanas ChatGPT: {len(tabs)} (max {CFG['max_tabs_chatgpt']})")
    tec = {r[0]: r[1] for r in c.execute("SELECT origen,COUNT(*) FROM tecnicas GROUP BY origen")}
    print("Tecnicas:", tec, "| descubiertas:", ", ".join(r[0] for r in c.execute("SELECT id FROM tecnicas WHERE origen='descubierta'")) or "(ninguna aun)")
    m = matriz(c); print(f"Cobertura: {len(m)} familias, {sum(len(d['huecos']) for d in m.values())} huecos tecnica x familia (heuristicos); analizadas: {q('SELECT COUNT(DISTINCT area) FROM analisis')} unidades")
    for modo in dict.fromkeys(CFG["ciclo"]):
        sc, clave, pl = candidates(c, modo)[0]; print(f"  siguiente {modo:<9} {clave:<34} {'(en descanso)' if sc < 0 else f'prioridad {sc:.1f}'}")
    for r in c.execute("SELECT id,tipo,area,error FROM jobs WHERE estado='error' ORDER BY id DESC LIMIT 5"): print(f"  ERROR job{r[0]} {r[1]} {r[2]}: {r[3]}")
    import qa_lote; print(chr(10).join(qa_lote.bloque_estado(sys.modules[__name__], c)))

SECRETOS = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._~+/=-]{16,}|(?i:(?:token|secret|password|passwd|api[_-]?key|authorization)\s*[=:]\s*)\S+)")

def texto_informe(c):
    """Informe completo del estado en texto plano, pensado para pegar en ChatGPT. Sin listado de tecnicas (solo recuento) y sin secretos."""
    import contextlib, io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): cmd_status(argparse.Namespace())
    q = lambda sql, *p: c.execute(sql, p).fetchone()[0]
    try: sv = json.loads(SVC.read_text(encoding="utf-8"))
    except Exception: sv = {}
    pid = trabajador_vivo(); ini = sv.get("inicio") or "9999"
    n = lambda *es: q(f"SELECT COUNT(*) FROM propuestas WHERE estado IN ({','.join('?' * len(es))})", *es)
    li = lambda *es: q(f"SELECT COUNT(*) FROM lote_items WHERE estado IN ({','.join('?' * len(es))})", *es)
    hall = {r[0]: r[1] for r in c.execute("SELECT estado,COUNT(*) FROM hallazgos GROUP BY estado")} if c.execute("SELECT 1 FROM sqlite_master WHERE name='hallazgos'").fetchone() else {}
    L = [f"INFORME QA-GPT web-escritor - {now()}", "",
         "== METRICAS ==",
         f"- Pruebas preparadas, sin ejecutar: {n('preparada', 'aprobada')}",
         f"- Pruebas ejecutadas: {n('ejecutada', 'publicada')}",
         f"- GitHub Actions aprobadas: {li('actions_ok')} (fallidas {li('actions_fallida')}, en curso {li('enviado', 'actions_pendiente', 'actions_ejecutando')})",
         f"- Defectos de producto demostrados: {li('defecto_demostrado')} | posibles defectos a triar: {li('a_triar')}",
         f"- Hallazgos de contratos masivos a revisar: {hall.get('a_triar', 0)} (defectos demostrados {hall.get('defecto_demostrado', 0)})",
         f"- Consultas GPT en esta sesion: {q('SELECT COUNT(*) FROM peticiones WHERE hora>=?', ini)} (hoy {q('SELECT COUNT(*) FROM peticiones WHERE fecha=?', today())}, total {q('SELECT COUNT(*) FROM peticiones')})",
         f"- Worker: {'activo, PID ' + str(pid) if pid else 'PARADO'}",
         f"- Tecnicas registradas: {q('SELECT COUNT(*) FROM tecnicas')} (descubiertas por GPT {q('SELECT COUNT(*) FROM tecnicas WHERE origen=?', 'descubierta')}; no se listan)", "",
         "== TESTS PENDIENTES (preparada/aprobada) POR RAMA =="]
    ramas = c.execute("SELECT rama, COUNT(*) k FROM propuestas WHERE estado IN ('preparada','aprobada') GROUP BY rama ORDER BY rama").fetchall()
    L += [f"- {r['rama'] or '(sin rama)'}: {r['k']}" for r in ramas] or ["(ninguno)"]
    L += ["", "== ACTIONS EJECUTADAS =="]
    acts = [f"- {r['rama']}@{r['sha'][:8]} [{r['estado']}] {', '.join(str(v.get('url') or v.get('id')) + ' ' + str(v.get('conclusion') or v.get('status') or '') for v in json.loads(r['runs'] or '{}').values())}"
            for r in c.execute("SELECT rama,sha,estado,runs FROM lote_items WHERE runs LIKE '%\"id\"%' ORDER BY actualizado DESC")]
    L += acts or ["(ninguna todavia)"]
    L += ["", "== ERRORES =="]
    errs = [f"- job{r['id']} {r['tipo']} {r['area']}: {(r['error'] or '')[:200]}" for r in c.execute("SELECT id,tipo,area,error FROM jobs WHERE estado='error' ORDER BY id DESC LIMIT 15")]
    errs += [f"- {r['estado']} {r['rama']}@{r['sha'][:8]}: {(r['detalle'] or '')[:200]}" for r in c.execute("SELECT rama,sha,estado,detalle FROM lote_items WHERE estado IN ('infra','fallo_test','revision_humana','actions_fallida') ORDER BY actualizado DESC LIMIT 20")]
    if sv.get("ultimo_error"): errs.append(f"- ultimo error del servicio: {str(sv['ultimo_error'])[:200]}")
    L += errs or ["(ninguno)"]
    L += ["", "== DEFECTOS DETECTADOS =="]
    defs = [f"- {r['estado']} {r['rama'].replace('gpt-qa/', '')}@{r['sha'][:8]}: {(r['detalle'] or '')[:200]}" for r in c.execute("SELECT rama,sha,estado,detalle FROM lote_items WHERE estado IN ('defecto_demostrado','a_triar') ORDER BY estado, actualizado DESC LIMIT 30")]
    defs += [f"- contrato a_triar [{r['contrato']}] {r['causa']} | {r['familia']} | {r['paginas']} pag." for r in c.execute("SELECT contrato,causa,familia,paginas FROM hallazgos WHERE estado='a_triar' ORDER BY paginas DESC LIMIT 15")] if hall else []
    L += defs or ["(ninguno)"]
    estado = [ln for ln in buf.getvalue().splitlines() if not ln.startswith("Tecnicas:")]
    L += ["", "== SALIDA DE ESTADO-QA-GPT (sin listado de tecnicas) =="] + estado
    return SECRETOS.sub("[SECRETO OCULTO]", "\n".join(L)) + "\n"

def cmd_informe(a):
    """`informe`: imprime el informe. `informe --copiar`: lo deja en el portapapeles (PowerShell Set-Clipboard, UTF-8) y comprueba que llego."""
    texto = texto_informe(db())
    if not a.copiar: print(texto); return 0
    STATE.mkdir(parents=True, exist_ok=True); f = STATE / "informe-estado.txt"
    f.write_text(texto, encoding="utf-8", newline="\r\n")
    ps = lambda cmd: cob.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", "$ErrorActionPreference='Stop';[Console]::OutputEncoding=[Text.Encoding]::UTF8;" + cmd], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    r = ps(f"Set-Clipboard -Value ([IO.File]::ReadAllText('{f}',[Text.Encoding]::UTF8))")
    if r.returncode: print("No se pudo copiar:", (r.stderr or r.stdout).strip()[:300]); return 1
    v = ps("Get-Clipboard -Raw")
    n_cb = v.stdout.replace("\r\n", "\n").rstrip("\n"); n_tx = texto.rstrip("\n")
    if v.returncode or n_cb != n_tx: print(f"COPIA NO VERIFICADA: portapapeles {len(n_cb)} caracteres, informe {len(n_tx)}. Fichero: {f}"); return 1
    print(f"Informe copiado al portapapeles: {len(n_tx)} caracteres, {n_tx.count(chr(10)) + 1} lineas (verificado). Pegalo en ChatGPT con Ctrl+V.\nTambien guardado en {f}"); return 0

def respaldar(c):
    """Copia consistente del estado fuera del repo (sqlite backup API); conserva las 7 ultimas."""
    d = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "web-escritor-qa-gpt-backup"; d.mkdir(parents=True, exist_ok=True)
    dest = d / f"estado-{today()}.db"
    if dest.exists() and (time.time() - dest.stat().st_mtime) < 3600: return
    b = sqlite3.connect(dest); c.backup(b); b.close()
    for old in sorted(d.glob("estado-*.db"))[:-7]: old.unlink(missing_ok=True)

def next_job(c):
    return c.execute("SELECT * FROM jobs WHERE estado='pendiente' AND no_antes<=? ORDER BY (fase='generando') DESC, (tipo='B') DESC, (tipo='R') DESC, id LIMIT 1", (now(),)).fetchone()

def cmd_scan_once(a, manual=False):
    manual = manual or getattr(a, "manual", False)
    if flag("stop") or flag("pause"): print(f"{now()} Pausado/parado (usa reanudar)."); return 0
    (STATE / "limite").unlink(missing_ok=True)
    with Lock():
        c = db(); print(f"{now()} ronda")
        git("fetch", "origin", "main", "--quiet", check=False)
        if ROOT != HERE.parents[1]: git("checkout", "--detach", "--quiet", "origin/main", check=False)  # worktree de lectura propio del servicio
        c.execute("UPDATE jobs SET estado='pendiente' WHERE estado='en_curso'"); c.commit()  # recuperacion tras caida: bajo Lock no hay nadie mas
        reconciliar(c); respaldar(c)
        if not manual: edge_asegurar()
        ronda = 0
        while True:
            if flag("stop") or flag("pause"): print("Detenido por bandera."); break
            job = next_job(c)
            if job is None:
                ok, dia = budget(c, ronda)
                if not ok: print(f"Presupuesto agotado (hoy {dia}, ronda {ronda})."); break
                elegido = elegir_modo(c)
                if not elegido: print("Todo en descanso."); break
                modo, clave, pl = elegido
                print(f"   modo {modo}: {clave}: {pl['motivo']}")
                if not enqueue(c, "A", clave, pl, f"A:{clave}:{pl['sha']}:{today()}"): print("Ya encolado hoy."); break
                job = next_job(c)
                if job is None: break
            else:
                reanuda = job["fase"] == "generando" and job["chat_id"]
                ok, dia = budget(c, ronda if not reanuda else 0)
                if not ok and not reanuda: print(f"Presupuesto agotado (hoy {dia}, ronda {ronda})."); break
            print(f"-> {job['tipo']} {job['area']}" + (f" (reanudando chat {job['chat_id'][:8]})" if job["fase"] == "generando" and job["chat_id"] else ""))
            hab = c.execute("SELECT COUNT(*) FROM peticiones").fetchone()[0]
            process(job, c, manual)
            if c.execute("SELECT COUNT(*) FROM peticiones").fetchone()[0] > hab: ronda += 1
            if manual: break
        if not manual:
            stage(c)
            limpiar_pestanas_cdp()
    return 0

def cmd_start(a):
    for n in range(a.rondas):
        if flag("stop"): print("STOP."); break
        while flag("pause"): time.sleep(30)
        cmd_scan_once(a)
        if n < a.rondas - 1:
            print(f"Ronda {n + 1}/{a.rondas} hecha. Proxima en {a.intervalo} min."); time.sleep(a.intervalo * 60)
    return 0

def cmd_flag(name, on):
    STATE.mkdir(parents=True, exist_ok=True); p = STATE / name
    if on: p.write_text(now())
    else: p.unlink(missing_ok=True)
    print(f"{name}: {'activado' if on else 'desactivado'}")

def task_query():
    return sh(["schtasks", "/Query", "/TN", TASK], check=False)

SVC = STATE / "servicio.json"

def marcar(**kw):
    """Estado vivo del servicio (lo lee `estado`); fichero pequeno, escritura atomica."""
    try: cur = json.loads(SVC.read_text(encoding="utf-8"))
    except Exception: cur = {}
    cur.update(kw, actualizado=now())
    tmp = SVC.with_suffix(".tmp"); tmp.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8"); os.replace(tmp, SVC)

def parada_vencida():
    """Parada pedida y ya pasada la gracia: la generacion en curso se deja reanudable (no se pierde)."""
    f = STATE / "stop"
    return f.exists() and time.time() - f.stat().st_mtime > CFG.get("parada_gracia_min", 3) * 60

def dormir(seg):
    """Espera interrumpible: renueva el latido y sale en cuanto se pide parar."""
    fin = time.monotonic() + seg
    while time.monotonic() < fin and not flag("stop"):
        Lock.latido(); time.sleep(min(5, max(fin - time.monotonic(), 0)))

def trabajador_vivo():
    try: pid = int(Lock.path.read_text().split()[0])
    except Exception: return 0
    return pid if pid_alive(pid) and es_qa_gpt(pid) else 0

def paso_servicio(c):
    """Un paso del bucle continuo: ejecuta el siguiente job o elige objetivo nuevo. True=hizo trabajo; 'limite'/('login',msg)=esperar; False=nada ejecutable."""
    job = next_job(c)
    if job is None:  # fallos sin triar: un job T por tanda (el servicio nunca ejecuta tests; solo analiza los ya fallados)
        import qa_triaje
        qa_triaje.encolar(sys.modules[__name__], c)  # un job por causa (firma), no por test
        job = next_job(c)
    if job is None:
        elegido = elegir_modo(c)
        if elegido:
            modo, clave, pl = elegido
            if enqueue(c, "A", clave, pl, f"A:{clave}:{pl['sha']}:{today()}"):
                print(f"{now()} modo {modo}: {clave}: {pl['motivo']}"); job = next_job(c)
    if job is None: return False
    marcar(estado="ejecutando", tarea=f"PASS {job['tipo']}", area=job["area"], desde_tarea=now())
    print(f"{now()} -> {job['tipo']} {job['area']}" + (f" (reanudando chat {job['chat_id'][:8]})" if job["fase"] == "generando" and job["chat_id"] else ""))
    try: process(job, c, False)
    except SystemExit as e:
        return "limite" if (STATE / "limite").exists() else ("login", str(e))
    marcar(ultimo_ok=now(), limite_n=0)
    return True

def cmd_servicio(a):
    """Servicio CONTINUO (lo arranca INICIAR-QA-GPT.bat): una peticion cada vez, sin horario, cupos ni pausas entre rondas. Nunca ejecuta tests/Actions."""
    import gpt_browser
    (STATE / "stop").unlink(missing_ok=True)
    with Lock():
        c = db(); inicio = now(); gpt_browser.PARADA = parada_vencida
        print(f"{inicio} SERVICIO CONTINUO iniciado (pid {os.getpid()})")
        marcar(estado="arrancando", inicio=inicio, pid=os.getpid(), limite_n=0, ultimo_error=None, tarea=None, area=None, hasta=None, parado=None)
        c.execute("UPDATE jobs SET estado='pendiente' WHERE estado='en_curso'")
        c.execute("UPDATE jobs SET no_antes=? WHERE estado='pendiente' AND fase='generando' AND chat_id IS NOT NULL", (now(),))  # reanudar al instante, sin reenviar
        c.commit(); (STATE / "limite").unlink(missing_ok=True)
        reconciliar(c); respaldar(c); edge_asegurar()
        vacias, ultimo_fetch = 0, 0.0
        try:
            while not flag("stop"):
                Lock.latido()
                if flag("pause"): marcar(estado="pausado"); dormir(30); continue
                if time.monotonic() - ultimo_fetch > 1800:
                    git("fetch", "origin", "main", "--quiet", check=False)
                    if ROOT != HERE.parents[1]: git("checkout", "--detach", "--quiet", "origin/main", check=False)
                    ultimo_fetch = time.monotonic()
                try: r = paso_servicio(c)
                except Exception as e:
                    marcar(ultimo_error=f"{now()} {str(e)[:200]}"); print(f"{now()} ERROR en el paso: {e}"); dormir(60); continue
                if r is True:
                    vacias = 0
                    try: stage(c)
                    except Exception as e: marcar(ultimo_error=f"{now()} stage: {str(e)[:200]}"); print(f"stage: {e}")
                    limpiar_pestanas_cdp()
                    try: edge_asegurar()  # entre peticiones: sin generacion activa
                    except Exception as e: print(f"edge: {e}")
                elif r == "limite":
                    n = json.loads(SVC.read_text(encoding="utf-8")).get("limite_n", 0); mins = min(180, 30 * 2 ** n)
                    hasta = (_ahora() + dt.timedelta(minutes=mins)).isoformat(timespec="seconds")
                    marcar(estado="pausado_limite", limite_n=n + 1, hasta=hasta, ultimo_error=f"{now()} limite de uso de ChatGPT")
                    print(f"{now()} Limite de ChatGPT: espera {mins} min (hasta {hasta})"); dormir(mins * 60); (STATE / "limite").unlink(missing_ok=True)
                elif isinstance(r, tuple):
                    marcar(estado="login", hasta=None, ultimo_error=f"{now()} {r[1][:160]}"); print(f"{now()} Sin sesion de ChatGPT: reintento en 5 min"); dormir(300)
                else:  # nada ejecutable ahora: backoff de jobs o todo cubierto
                    vacias += 1
                    prox = c.execute("SELECT MIN(no_antes) FROM jobs WHERE estado='pendiente'").fetchone()[0]
                    seg = 600 if not prox else max(15, min(600, (dt.datetime.fromisoformat(prox) - _ahora()).total_seconds()))
                    c.commit()  # no dormir con una transaccion abierta: bloquearia a EJECUTAR
                    marcar(estado="esperando", tarea=None, area=None, hasta=(_ahora() + dt.timedelta(seconds=seg)).isoformat(timespec="seconds"))
                    if vacias == 1: print(f"{now()} Sin trabajo util ahora: espera {int(seg)} s")
                    dormir(seg)
        finally:
            marcar(estado="parado", tarea=None, area=None, parado=now()); gpt_browser.PARADA = None; c.close()
            print(f"{now()} SERVICIO detenido")
    return 0

def cmd_iniciar(a):
    """INICIAR-QA-GPT.bat: arranca el servicio continuo desvinculado de esta consola. No ejecuta tests ni Actions."""
    STATE.mkdir(parents=True, exist_ok=True)
    pid = trabajador_vivo()
    if pid: print(f"El servicio YA esta en marcha (pid {pid}). No se arranca otro."); return 0
    db().close()
    import edge_launcher
    if edge_launcher.alive() is None: print("Abriendo Edge 9230 (perfil con la sesion de ChatGPT)..."); edge_launcher.main()
    cmd_flag("pause", False); (STATE / "stop").unlink(missing_ok=True)
    sh(["schtasks", "/Change", "/TN", TASK, "/DISABLE"], check=False)
    py = Path(sys.executable).with_name("pythonw.exe"); py = py if py.exists() else Path(sys.executable)
    subprocess.Popen([str(py), str(HERE / "qa_gpt.py"), "servicio"], cwd=str(STATE), close_fds=True,
                     creationflags=0x00000008 | 0x00000200 | 0x08000000)  # DETACHED_PROCESS | NEW_PROCESS_GROUP | NO_WINDOW
    for _ in range(40):
        time.sleep(0.5)
        pid = trabajador_vivo()
        if pid: break
    if not pid: print(f"El servicio no arranco. Mira {STATE / 'servicio.log'}"); return 1
    print(f"SERVICIO QA-GPT EN MARCHA (pid {pid}). Trabaja sin parar hasta que lo pares con PARAR-QA-GPT.bat.\nNo ejecuta tests ni GitHub Actions. Estado: ESTADO-QA-GPT.bat. Registro: {STATE / 'servicio.log'}")
    return 0

def cmd_parar(a):
    """PARAR-QA-GPT.bat: parada ordenada y acotada. Solo toca el worker de qa-gpt; Edge se deja abierto (perfil intacto)."""
    cmd_flag("stop", True)
    sh(["schtasks", "/Change", "/TN", TASK, "/DISABLE"], check=False)
    pid = trabajador_vivo()
    if not pid: print("El servicio no estaba en marcha. Marcado como parado."); Lock.path.unlink(missing_ok=True); return 0
    limite = time.monotonic() + (CFG.get("parada_gracia_min", 3) + 3) * 60
    print(f"Parada solicitada (pid {pid}). Si hay una respuesta generandose se espera hasta {CFG.get('parada_gracia_min', 3)} min a capturarla; si no, queda reanudable.")
    while time.monotonic() < limite and pid_alive(pid): time.sleep(2)
    if pid_alive(pid):
        print("El servicio no termino a tiempo: se cierra SOLO su proceso (la cola y el chat quedan recuperables).")
        if es_qa_gpt(pid): sh(["taskkill", "/PID", str(pid), "/T", "/F"], check=False); time.sleep(1)
        Lock.path.unlink(missing_ok=True); marcar(estado="parado", parado=now(), tarea=None, area=None)
        print("PARADO (forzado, estado conservado)."); return 0
    print("PARADO correctamente. Progreso guardado; el siguiente INICIAR continua donde quedo."); return 0

def cmd_quitar_servicio(a):
    sh(["schtasks", "/Delete", "/TN", TASK, "/F"], check=False); print("Tarea programada eliminada.")

def cmd_review(a):
    c = db(); rows = c.execute("SELECT id,area,titulo,estado,rama,veredicto,tecnica FROM propuestas" + ("" if a.todas else " WHERE estado IN ('aceptada','preparada','aprobada','informe','revisar','propuesta')") + " ORDER BY id DESC LIMIT 40").fetchall()
    for r in rows:
        v = json.loads(r["veredicto"]) if r["veredicto"] and r["veredicto"].startswith("{") else {}
        print(f"#{r['id']} [{r['estado']}] {r['area']} · {r['tecnica']}: {r['titulo']}" + (f" -> {r['rama']}" if r["rama"] else "") + (f"\n    {'; '.join(v.get('motivos', []))[:200]}" if v else ""))
    if not rows: print("(nada pendiente de revisar)")

def cmd_pendientes(a):
    c = db(); rows = c.execute("SELECT id,area,titulo,tecnica,rama,datos FROM propuestas WHERE estado='preparada' ORDER BY rama,id").fetchall()
    print(f"{len(rows)} tests preparados esperando tu aprobacion (aprobar <id...|todas>):")
    for r in rows:
        d = json.loads(r["datos"]); print(f"#{r['id']} {r['area']} [{d.get('categoria')}/{r['tecnica']}] {r['titulo']}\n    ficheros: {', '.join(f['ruta'] for f in d.get('ficheros_nuevos', []))} | rama {r['rama']} | defecto {d.get('defecto')}")

def cmd_aprobar(a):
    c = db(); ids = [r[0] for r in c.execute("SELECT id FROM propuestas WHERE estado='preparada'")] if a.ids == ["todas"] else [int(x) for x in a.ids]
    for i in ids:
        r = c.execute("SELECT estado FROM propuestas WHERE id=?", (i,)).fetchone()
        if r and r[0] == "preparada": estado_prop(c, i, "aprobada", "aprobada manualmente por David"); print(f"#{i} aprobada")
    for r in c.execute("SELECT rama FROM ramas WHERE estado='preparada'").fetchall():
        if not c.execute("SELECT 1 FROM propuestas WHERE rama=? AND estado='preparada'", (r[0],)).fetchone() and c.execute("SELECT 1 FROM propuestas WHERE rama=? AND estado='aprobada'", (r[0],)).fetchone():
            c.execute("UPDATE ramas SET estado='aprobada' WHERE rama=?", (r[0],)); print(f"rama {r[0]} lista para el lote")
    c.commit()

def cmd_simular(a):
    """Reproduce decisiones del planificador sobre una COPIA en memoria del estado: cero peticiones a GPT, cero cambios."""
    src = db(); mem = sqlite3.connect(":memory:"); mem.row_factory = sqlite3.Row; src.backup(mem)
    head = git("rev-parse", "--short", "origin/main"); vistos = set()
    for i in range(a.rondas):
        el = elegir_modo(mem)
        if not el: print(f"{i + 1}: todo en descanso"); break
        modo, clave, pl = el
        print(f"{i + 1}: {modo:<9} {clave:<36} {pl['motivo'][:90]}" + ("   <-- REPETIDO" if clave in vistos else ""))
        vistos.add(clave); mem.execute("INSERT INTO analisis VALUES(?,?,?,?)", (clave, today(), head, pl.get("sha", "")))
    print(f"{len(vistos)} objetivos distintos en {a.rondas} rondas simuladas; modos: {sorted({v.split(':')[0] for v in vistos})}")

def cmd_reabrir(a):
    """Devuelve propuestas bloqueadas/atascadas a PASS B en UNA peticion (con contexto y verificacion local actuales).
    Si ya habia un job B pendiente para alguna, se cancela y se absorbe en el lote."""
    c = db(); ids = []
    for i in a.ids:
        r = c.execute("SELECT id,area,estado FROM propuestas WHERE id=?", (i,)).fetchone()
        if not r: print(f"#{i} inexistente"); continue
        if r["estado"] not in ("bloqueada", "revisar", "invalida", "propuesta"): print(f"#{i} esta en '{r['estado']}': no procede"); continue
        ids.append(r)
    if not ids: return 1
    for r in ids:
        for j in c.execute("SELECT id,payload FROM jobs WHERE tipo='B' AND estado='pendiente' AND chat_id IS NULL").fetchall():
            if r["id"] in json.loads(j["payload"]).get("ids", []):
                c.execute("UPDATE jobs SET estado='cancelado',error='absorbido en lote reabierto',actualizado=? WHERE id=?", (now(), j["id"]))
        estado_prop(c, r["id"], "propuesta", "reabierta manualmente para PASS B"); c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", ("PASS B reabierto", r["id"]))
    n = c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='B'").fetchone()[0]
    enqueue(c, "B", ids[0]["area"], {"ids": [r["id"] for r in ids]}, f"B:{ids[0]['area']}:{'-'.join(str(r['id']) for r in ids)}:reabierta{n}"); c.commit()
    print(f"reabiertas {[r['id'] for r in ids]}: 1 job PASS B en cola")

def cmd_migrar_datos(a):
    """Normaliza `como_ejecutar` historico a `pasos` validados en estado.db (copia previa, transaccion, idempotente). --ensayo no escribe."""
    import qa_migrar
    r = qa_migrar.migrar(DB_PATH, STATE / "backups", now(), aplicar=not a.ensayo)
    print(f"{'ENSAYO' if a.ensayo else 'MIGRACION'}: {'OK' if r['ok'] else 'FALLO ' + str(r['error'])} | propuestas a normalizar/normalizadas: {r['migradas']} | omitidas: {r['omitidas']} | copia previa: {r['backup'] or '(ninguna)'}")
    return 0 if r["ok"] else 1

def cmd_descartar(a):
    c = db()
    if not c.execute("SELECT 1 FROM propuestas WHERE id=?", (a.id,)).fetchone(): print("propuesta inexistente"); return 1
    estado_prop(c, a.id, "rechazada", f"descartada manualmente: {a.motivo}")
    c.execute("UPDATE propuestas SET siguiente=? WHERE id=?", (f"cerrada: {a.motivo}"[:200], a.id)); c.commit(); print(f"#{a.id} descartada")

def cmd_fallos(a):
    c = db()
    for r in c.execute("SELECT id,tipo,area,estado,intentos,chat_id,error,actualizado FROM jobs WHERE error IS NOT NULL OR estado='error' ORDER BY id DESC LIMIT 15"):
        print(f"job{r['id']} {r['tipo']} {r['area']} [{r['estado']}] intentos {r['intentos']} chat {str(r['chat_id'])[:8]} {r['actualizado']}\n    {r['error']}")
    for r in c.execute("SELECT id,titulo,veredicto FROM propuestas WHERE estado='invalida'"): print(f"propuesta #{r['id']} invalida: {r['titulo'][:60]} :: {r['veredicto']}")
    print("(sin fallos)" if not c.execute("SELECT 1 FROM jobs WHERE error IS NOT NULL OR estado='error'").fetchone() else "")

def cmd_recuperar(a):
    """Reanuda/recupera un job desde su chat (sin reenviar): --chat adopta una conversacion existente."""
    c = db(); job = c.execute("SELECT * FROM jobs WHERE id=?", (a.job,)).fetchone()
    if not job: print("job inexistente"); return 1
    cid = a.chat or job["chat_id"]
    if not cid: print("el job no tiene chat que recuperar (se reenviara normalmente)"); return 1
    c.execute("UPDATE jobs SET chat_id=?,fase='generando',estado='pendiente',respuesta=NULL,no_antes=?,error=NULL WHERE id=?", (cid, now(), a.job)); c.commit()
    print(f"job{a.job} marcado para reanudar el chat {cid[:8]}; ejecuta scan-once (no se reenvia el prompt)")

def cmd_ingest(a):
    c = db(); job = c.execute("SELECT * FROM jobs WHERE id=?", (a.job,)).fetchone()
    ingest_answer(c, job, Path(a.fichero).read_text(encoding="utf-8"), None)
    if job["tipo"] == "B" or (job["tipo"] == "A" and lote_activo()): stage(c)


# ---------- noche y manana: SOLO manual ----------
AUTORIZ = STATE / "ejecucion_autorizada"

def autorizada():
    return AUTORIZ.exists() and AUTORIZ.read_text().split()[0] == today()

def lote_congelado():
    """Ramas (rama, sha) fijadas por autorizar-noche; nada generado o aprobado despues entra."""
    return {l.split()[0]: l.split()[1] for l in AUTORIZ.read_text().splitlines()[1:] if len(l.split()) == 2} if autorizada() else {}

def cmd_autorizar(a):
    c = db(); ramas = c.execute("SELECT rama,sha FROM ramas WHERE estado='aprobada'").fetchall(); c.close()
    if not ramas: print("No hay ramas aprobadas: nada que autorizar (usa pendientes / aprobar)."); return 1
    STATE.mkdir(parents=True, exist_ok=True)
    lineas = [f"{today()} autorizado manualmente {now()}", *(f"{r['rama']} {r['sha']}" for r in ramas)]
    AUTORIZ.write_text(chr(10).join(lineas) + chr(10))
    print(f"Autorizado SOLO hoy ({today()}) este lote congelado:"); [print(f"  {r['rama']} {r['sha'][:8]}") for r in ramas]
    print("Ahora: lote-nocturno --confirmar")

def gh_json(*args): return json.loads(sh(["gh", *args]) or "[]")

def cmd_nightly(a):
    """Publica ramas APROBADAS y lanza Actions. Exige autorizar-noche (valida hoy) Y --confirmar. Nunca lo invoca el servicio diurno."""
    c = db(); ramas = c.execute("SELECT * FROM ramas WHERE estado IN ('aprobada','publicada')").fetchall()
    if a.confirmar and autorizada():
        fijo = lote_congelado(); ramas = [r for r in ramas if fijo.get(r["rama"]) == r["sha"]]
    if not ramas: print("No hay ramas aprobadas (usa pendientes / aprobar)."); return 0
    print("Lote congelado:"); [print(f"  {r['rama']} {r['sha'][:8]} ({r['estado']})") for r in ramas]
    if not (a.confirmar and autorizada()):
        print("\nSOLO PLAN: la ejecucion esta DESACTIVADA. Requiere `autorizar-noche` (hoy) y `lote-nocturno --confirmar`."); return 0
    git("fetch", "origin", "main"); repo = CFG["repo"]; out = []
    for r in ramas:
        wt = r["ruta"]
        if cob.run(["git", "merge-base", "--is-ancestor", "origin/main", r["rama"]], cwd=ROOT).returncode:
            if cob.run(["git", "rebase", "origin/main"], cwd=wt, capture_output=True, text=True).returncode:
                git("rebase", "--abort", cwd=wt, check=False); print(f"  CONFLICTO {r['rama']}: no se publica")
                c.execute("UPDATE ramas SET estado='conflicto' WHERE rama=?", (r["rama"],)); c.commit(); continue
        sha = git("rev-parse", "HEAD", cwd=wt)
        git("push", "-u", "origin", r["rama"], cwd=wt)
        prs = gh_json("pr", "list", "--head", r["rama"], "--json", "number,url", "-R", repo)
        if prs: num, url = prs[0]["number"], prs[0]["url"]
        else:
            props = c.execute("SELECT titulo FROM propuestas WHERE rama=?", (r["rama"],)).fetchall()
            body = (f"Tests preparados por revision GPT (PASS A + PASS B) para **{r['area']}**.\nPadre: #{CFG['pr_padre']}\n\n"
                    + "\n".join("- " + p[0] for p in props) + "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)")
            url = sh(["gh", "pr", "create", "-R", repo, "--base", "main", "--head", r["rama"], "--title", f"GPT QA — {r['area']}: {len(props)} tests", "--body", body])
            num = int(url.rstrip("/").split("/")[-1])
        c.execute("UPDATE ramas SET estado='publicada',pr=?,url=?,sha=? WHERE rama=?", (num, url, sha, r["rama"]))
        c.execute("UPDATE propuestas SET estado='publicada' WHERE rama=? AND estado='aprobada'", (r["rama"],)); c.commit(); out.append((r, num, sha))
    time.sleep(40)
    for r, num, sha in out:
        runs = gh_json("run", "list", "-R", repo, "--branch", r["rama"], "--commit", sha, "--json", "workflowName,databaseId")
        have = {x["workflowName"] for x in runs}
        wfs = {Path(w).name for w in (json.loads(p["datos"]).get("workflow") for p in c.execute("SELECT datos FROM propuestas WHERE rama=?", (r["rama"],))) if w and w != "null"}
        for wf in sorted(wfs):
            f = ROOT / ".github/workflows" / wf
            if not f.exists(): print(f"  workflow desconocido {wf}"); continue
            nm = re.search(r"^name:\s*(.+)$", f.read_text(encoding="utf-8"), re.M)
            if nm and nm.group(1).strip().strip("'\"") in have: continue
            sh(["gh", "workflow", "run", wf, "-R", repo, "--ref", r["rama"]], check=False); print(f"  dispatch {wf} en {r['rama']}")
        print(f"  PR #{num} {r['rama']} {sha[:8]}: {len(runs)} runs por pull_request")
    AUTORIZ.unlink(missing_ok=True)
    print(f"Publicadas {len(out)}. Autorizacion consumida. Informe: informe-matinal")
    return 0

def classify(log):
    if re.search(r"ECONNRESET|ETIMEDOUT|rate limit|\b503\b|\b429\b|Could not resolve host|runner.*lost|npm ERR! network", log, re.I): return "entorno/transitorio"
    if re.search(r"AssertionError|expect\(|assert ", log): return "regresion real o defecto del test (revisar)"
    return "desconocido"

def cmd_morning(a):
    c = db(); repo = CFG["repo"]; lines = [f"# GPT QA — informe {today()}", "", f"Padre: #{CFG['pr_padre']}", "", "## Descubrimiento"]
    q = lambda s, *p: c.execute(s, p).fetchall()
    hoy = {r[0]: r[1] for r in q("SELECT estado,COUNT(*) FROM propuestas GROUP BY estado")}
    lines += [f"- Propuestas por estado: {hoy}", f"- Peticiones hoy: {c.execute('SELECT COUNT(*) FROM peticiones WHERE fecha=?', (today(),)).fetchone()[0]}"]
    for r in q("SELECT id,area,titulo,estado,tecnica FROM propuestas ORDER BY id DESC LIMIT 15"): lines.append(f"  - #{r['id']} [{r['estado']}] {r['area']} · {r['tecnica']}: {r['titulo']}")
    fall = q("SELECT id,tipo,area,error FROM jobs WHERE estado='error' OR error IS NOT NULL ORDER BY id DESC LIMIT 5")
    if fall: lines += ["", "## Fallos a inspeccionar"] + [f"- job{r['id']} {r['tipo']} {r['area']}: {r['error']}" for r in fall]
    lines += ["", "## Esperan tu aprobacion (preparadas, NO ejecutadas)"]
    prep = q("SELECT id,area,titulo,rama FROM propuestas WHERE estado='preparada'")
    lines += [f"- #{r['id']} {r['area']}: {r['titulo']} ({r['rama']})" for r in prep] or ["- (ninguna)"]
    lines += ["", "## Ejecucion", f"- Autorizacion hoy: {'SI' if autorizada() else 'NO (nada se ha ejecutado)'}"]
    for r in c.execute("SELECT * FROM ramas WHERE estado='publicada'").fetchall():
        runs = gh_json("run", "list", "-R", repo, "--branch", r["rama"], "--json", "databaseId,workflowName,status,conclusion,headSha,url", "--limit", "40")
        runs = [x for x in runs if x["headSha"] == r["sha"]] or runs
        tests = [json.loads(p["datos"]) for p in c.execute("SELECT datos FROM propuestas WHERE rama=?", (r["rama"],))]
        lines += [f"## PR #{r['pr']} — {r['area']}", f"{r['url']}", f"Commit original: `{r['sha'][:10]}` rama `{r['rama']}`", "Tests nuevos:"]
        for d in tests: lines.append(f"- {d.get('titulo')} → {', '.join(f['ruta'] for f in d.get('ficheros_nuevos', []))} ({d.get('categoria')}, defecto {d.get('defecto')})")
        cnt = {"success": 0, "failure": 0, "cancelled": 0, "pendiente": 0}
        for x in runs:
            k = x["conclusion"] if x["status"] == "completed" else "pendiente"; cnt[k if k in cnt else "failure"] += 1
        lines.append(f"Resultado: {cnt}")
        for x in runs:
            lines.append(f"- {x['workflowName']}: {x['conclusion'] or x['status']} {x['url']}")
            if x["conclusion"] == "failure":
                log = sh(["gh", "run", "view", str(x["databaseId"]), "-R", repo, "--log-failed"], check=False)
                tail = "\n".join(log.splitlines()[-25:])[-1800:]
                lines += [f"  - Clasificacion (heuristica): {classify(log)}", "  ```", *("  " + l for l in tail.splitlines()), "  ```"]
        lines.append("")
    lines += ["## Siguiente cobertura", *[f"- {k} ({d['ficheros']} ficheros, {len(d['huecos'])} huecos)" for k, d in sorted(matriz(c).items(), key=lambda t: -len(t[1]["huecos"]))[:5]]]
    out = STATE / f"qa-gpt-morning-{today()}.md"; out.write_text("\n".join(lines), encoding="utf-8"); print(f"Informe: {out}")


def cmd_contratos(a):
    import qa_contratos
    if getattr(a, "completo", False):
        import qa_viaa; qa_viaa.ejecutar(db(), sys.modules[__name__], ROOT, forzar=True); return
    res = qa_contratos.ejecutar(ROOT); out = STATE / "auditoria"; out.mkdir(parents=True, exist_ok=True)
    (out / f"contratos-{today()}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(qa_contratos.informe(res)); print(f"JSON: {out / f'contratos-{today()}.json'}")


def main():
    ap = argparse.ArgumentParser(prog="qa-gpt"); sp = ap.add_subparsers(dest="cmd", required=True)
    ALIAS = {}
    def add(names, fn, *args):
        p = sp.add_parser(names[0], aliases=names[1:])
        for ar, kw in args: p.add_argument(*ar, **kw)
        for n in names: ALIAS[n] = fn
        return p
    add(["setup"], cmd_setup)
    add(["status", "estado"], cmd_status)
    add(["informe"], cmd_informe, (["--copiar"], dict(action="store_true")))
    add(["pause", "pausa"], lambda a: cmd_flag("pause", True))
    add(["resume", "reanudar"], lambda a: (cmd_flag("pause", False), cmd_flag("stop", False)))
    add(["stop", "parar"], cmd_parar)
    add(["review-queue", "revisar-aceptadas", "aceptadas"], cmd_review, (["--todas"], dict(action="store_true")))
    add(["pendientes"], cmd_pendientes)
    add(["aprobar"], cmd_aprobar, (["ids"], dict(nargs="+")))
    add(["fallos"], cmd_fallos)
    add(["reabrir"], cmd_reabrir, (["ids"], dict(type=int, nargs="+")))
    add(["descartar"], cmd_descartar, (["id"], dict(type=int)), (["--motivo"], dict(required=True)))
    add(["simular"], cmd_simular, (["--rondas"], dict(type=int, default=6)))
    add(["inventario"], cmd_inventario, (["--forzar"], dict(action="store_true")), (["--top"], dict(type=int, default=25)))
    add(["recuperar"], cmd_recuperar, (["--job"], dict(type=int, required=True)), (["--chat"], dict(default=None)))
    add(["scan-once"], cmd_scan_once, (["--manual"], dict(action="store_true")))
    add(["start-discovery"], cmd_start, (["--rondas"], dict(type=int, default=3)), (["--intervalo"], dict(type=int, default=0)))
    add(["iniciar"], cmd_iniciar)
    add(["servicio"], cmd_servicio)
    add(["quitar-servicio"], cmd_quitar_servicio)
    add(["ingest"], cmd_ingest, (["job"], dict(type=int)), (["fichero"], {}))
    add(["autorizar-noche"], cmd_autorizar)
    add(["nightly-run", "lote-nocturno"], cmd_nightly, (["--confirmar"], dict(action="store_true")))
    add(["morning-report", "informe-matinal"], cmd_morning)
    add(["ejecutar-actions"], lambda a: __import__("qa_lote").main(sys.modules[__name__], a), (["--limite"], dict(type=int, default=None)), (["--continuo"], dict(action="store_true")))
    add(["pr"], lambda a: __import__("qa_pr").cmd_pr(sys.modules[__name__], a), (["--demo"], dict(action="store_true")), (["--local"], dict(action="store_true")))
    add(["triaje"], lambda a: __import__("qa_triaje").cmd_triaje(sys.modules[__name__], a))
    add(["contratos"], cmd_contratos, (["--completo"], dict(action="store_true")))
    add(["coste-actions"], lambda a: __import__("qa_coste").main(sys.modules[__name__], a))
    add(["migrar-datos"], cmd_migrar_datos, (["--ensayo"], dict(action="store_true")))
    a = ap.parse_args()
    return ALIAS[a.cmd](a)

if __name__ == "__main__":
    sys.exit(main() or 0)
