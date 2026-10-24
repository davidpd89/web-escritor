"""PR automaticas a partir del analisis GPT. Todo lo que devuelve GPT es una PROPUESTA: aqui se valida y solo se aplica en un worktree
aislado creado desde origin/main. Nunca ejecuta comandos que haya escrito GPT.
Solo se desarrollan causas que Claude aprobo (decision='corregir'). Una PR solo se abre si el defecto se reproduce en main (baseline), el parche
lo corrige, pasan los verificadores del repo y no hay cambios fuera de alcance; si algo falla NO hay PR (ni en borrador): queda el motivo en
`pr_estado` y el ciclo reintenta de forma acotada. Despues, `Ciclo` gestiona presupuesto, CI, revision final de Claude e integracion."""
import json, os, re, shutil, socket, subprocess, sys
from pathlib import Path

MAX_FICHEROS = 5
RC_INFRA = 125
INFRA = re.compile(r"ERR_MODULE_NOT_FOUND|ECONNREFUSED|Executable doesn't exist|browserType.launch")
MAX_REEMPLAZOS = 8
PROHIBIDAS = re.compile(r"(^|/)(\.github|\.git|node_modules|scripts/qa-gpt|\.ci)(/|$)|(^|/)(package(-lock)?\.json|wrangler[\w.-]*|\.env[\w.]*|\.dev\.vars)$"
                        r"|stripe|paypal|payment|(^|[/_.-])pagos?([/_.-]|$)|secret|credential|cloudflare", re.I)
SECRETO = re.compile(r"sk_(live|test)_\w+|AKIA[0-9A-Z]{12,}|ghp_\w{20,}|(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}", re.I)
SECCIONES = ("Resumen", "Comportamiento esperado", "Comportamiento observado", "Causa raiz", "Tests afectados", "Evidencia", "Solucion",
             "Verificacion", "Riesgos", "Componentes afectados", "Origen")


def ruta_segura(ruta):
    if not isinstance(ruta, str) or not ruta or ruta.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", ruta): return "ruta no relativa"
    partes = ruta.replace("\\", "/").split("/")
    if ".." in partes or "" in partes: return "ruta con .. o vacia"
    if PROHIBIDAS.search(ruta.replace("\\", "/")): return "ruta sensible (workflows, credenciales, pagos, configuracion o qa-gpt)"
    return None


def validar_parche(parche, leer):
    """-> (ok, problemas, normalizado). `leer(ruta)` devuelve el texto actual del fichero o None. No escribe nada."""
    problemas, norm = [], {"ficheros": []}
    fich = (parche or {}).get("ficheros") if isinstance(parche, dict) else None
    if not isinstance(fich, list) or not fich: return False, ["parche sin ficheros"], None
    if len(fich) > MAX_FICHEROS: return False, [f"mas de {MAX_FICHEROS} ficheros"], None
    vistos = set()
    for f in fich:
        ruta = f.get("ruta") if isinstance(f, dict) else None
        if (m := ruta_segura(ruta)): problemas.append(f"{ruta}: {m}"); continue
        if ruta in vistos: problemas.append(f"{ruta}: repetido"); continue
        vistos.add(ruta)
        texto = leer(ruta)
        if texto is None: problemas.append(f"{ruta}: no existe en main"); continue
        reps = f.get("reemplazos")
        if not isinstance(reps, list) or not reps or len(reps) > MAX_REEMPLAZOS: problemas.append(f"{ruta}: reemplazos invalidos"); continue
        out = []
        for r in reps:
            b, p = (r.get("buscar"), r.get("por")) if isinstance(r, dict) else (None, None)
            if not isinstance(b, str) or not b.strip() or not isinstance(p, str): problemas.append(f"{ruta}: reemplazo mal formado"); break
            if b == p: problemas.append(f"{ruta}: reemplazo sin cambios"); break
            if SECRETO.search(p): problemas.append(f"{ruta}: el reemplazo parece contener un secreto"); break
            n = texto.count(b)
            if n != 1: problemas.append(f"{ruta}: 'buscar' aparece {n} veces (debe ser 1)"); break
            texto = texto.replace(b, p, 1); out.append({"buscar": b, "por": p})
        else:
            norm["ficheros"].append({"ruta": ruta, "reemplazos": out})
    return (not problemas), problemas, (norm if not problemas else None)


def aplicar_parche(root, norm):
    """Aplica un parche YA validado dentro de `root` (worktree). Vuelve a comprobar contra el disco; lanza ValueError si no encaja."""
    root = Path(root)
    ok, problemas, n2 = validar_parche(norm, lambda r: (root / r).read_text(encoding="utf-8") if (root / r).is_file() else None)
    if not ok: raise ValueError("; ".join(problemas))
    tocados = []
    for f in n2["ficheros"]:
        p = root / f["ruta"]; t = p.read_text(encoding="utf-8")
        for r in f["reemplazos"]: t = t.replace(r["buscar"], r["por"], 1)
        p.write_text(t, encoding="utf-8", newline=""); tocados.append(f["ruta"])
    return tocados


def cuerpo_pr(row, tests, verif, demo=False):
    d = json.loads(row["decision_json"] or "{}") if "decision_json" in row.keys() else {}
    a = json.loads(row["analisis"] or "{}")
    v = json.loads(row["validacion"] or "{}") if (row["validacion"] or "").startswith("{") else {}
    lista = lambda xs: "\n".join(f"- `{x}`" for x in xs) or "- (ninguno)"
    if d.get("decision") == "corregir":
        partes = [("Resumen", f"{row['causa_raiz']}\n\nClase: **{row['clase']}** · prioridad {d.get('prioridad', '?')} · confianza de Claude: {d.get('confianza', '?')} · expediente #{row['id']}"),
                  ("Causa probable (aprobada por Claude)", d.get("causa_probable") or row["causa_raiz"]),
                  ("Justificacion de la decision", d.get("justificacion") or "(no indicada)"),
                  ("Criterio de aceptacion", d.get("criterio_aceptacion") or "(no indicado)"),
                  ("Cambio realizado (GPT)", v.get("explicacion") or "(GPT no aporto explicacion)"),
                  ("Archivos tocados", lista(d.get("archivos") or [])),
                  ("Tests afectados", lista(tests)),
                  ("Evidencia original", "```\n" + (row["evidencia"] or "")[:1500] + "\n```"),
                  ("Verificacion local", verif),
                  ("Riesgos", "El criterio lo fijo Claude antes del desarrollo; tras el CI, Claude revisa el diff contra ese criterio. No hay auto-merge salvo calibracion completada."),
                  ("Origen", "GPT QA: Actions -> agrupacion -> decision de Claude -> desarrollo GPT -> baseline en main -> parche -> verificadores.")]
    else:
        partes = [("Resumen", f"{row['causa_raiz']}\n\nClase: **{row['clase']}** · firma `{row['firma']}` · confianza GPT: {a.get('confianza', '?')}"),
                  ("Comportamiento esperado", a.get("comportamiento_esperado") or "(no indicado)"),
                  ("Comportamiento observado", a.get("comportamiento_observado") or "(no indicado)"),
                  ("Causa raiz", a.get("hipotesis") or row["causa_raiz"]),
                  ("Tests afectados", lista(tests)),
                  ("Evidencia", "```\n" + (row["evidencia"] or "")[:1500] + "\n```"),
                  ("Solucion", row["arreglo"] or ""),
                  ("Verificacion", verif),
                  ("Riesgos", "Propuesta de GPT validada solo por sustitucion exacta y por los tests citados. Revisar a mano; no fusionar sin leer el diff."),
                  ("Componentes afectados", lista(a.get("componentes_afectados") or [])),
                  ("Origen", "Generada por la automatizacion GPT QA (analizador -> parche validado -> worktree aislado). Sin auto-merge.")]
    head = "> **DEMOSTRACION DE LA AUTOMATIZACION. NO FUSIONAR.** Se cierra sin merge.\n\n" if demo else ""
    return head + "\n\n".join(f"## {t}\n{c}" for t, c in partes) + "\n"


# Verificadores del repo segun lo que toca el parche: errores ya vistos en las PR qa-fix (version de recurso sin subir, pagefind/shell/indices obsoletos).
HTML = (".html", ".htm")
VERIF_ACTIVOS = ("script.js", "styles.css")


def verificadores(wt, tocados):
    """Comandos `python scripts/<check>` (existentes en el repo) que corresponden a los ficheros tocados. Solo se ejecutan los que existen."""
    t = [str(x).replace("\\", "/") for x in tocados]
    html = any(x.endswith(HTML) for x in t)
    activo = any(x in VERIF_ACTIVOS or x.startswith("assets/") for x in t)
    gen = any(x.startswith("scripts/build-") or x.startswith("data/") for x in t)
    cmds = []
    if activo: cmds += [["python", "scripts/check-asset-versions.py"]]
    if html or activo or gen:
        cmds += [["python", "scripts/build-site-shell.py", "--check"], ["python", "scripts/build-pagefind-index.py", "--check"],
                 ["python", "scripts/check-local-assets.py"], ["python", "scripts/check-public-html-safety.py"], ["python", "scripts/check-heading-structure.py"],
                 ["python", "scripts/check-internal-graph.py"]]
    if gen: cmds += [["python", "scripts/build-feed.py", "--check"], ["python", "scripts/build-sitemap.py", "--check"]]
    return [c for c in cmds if (Path(wt) / c[1]).exists()]


class Pr:
    def __init__(self, q, gh, runner, out=print):
        self.q, self.gh, self.run, self.out = q, gh, runner, out
        self.root = q.ROOT

    def git(self, *a, cwd=None, timeout=300):
        return self.run(["git", *a], str(cwd or self.root), timeout=timeout)

    def _rutas_tests(self, c, ids):
        res = []
        for pid in ids:
            r = c.execute("SELECT datos FROM propuestas WHERE id=?", (pid,)).fetchone()
            if r: res += [f["ruta"] for f in json.loads(r[0]).get("ficheros_nuevos", [])]
        return sorted(set(res))

    @staticmethod
    def comando_test(ruta):
        e = Path(ruta).suffix
        return ["node", ruta] if e in (".mjs", ".js") else ["python", ruta] if e == ".py" else None

    def _test(self, wt, t):
        """Ejecuta un test conocido. Los .mjs/.js (Playwright) necesitan node_modules y un servidor estatico del worktree: se levanta uno propio en un puerto libre y se cierra al terminar."""
        cmd = self.comando_test(t)
        if cmd[0] != "node": return self.run(cmd, str(wt), timeout=240)
        nm = Path(flujo(self.q).get("node_modules") or r"C:\GIT\web-escritor\node_modules")
        dst = Path(wt) / "node_modules"
        if nm.exists() and not dst.exists():
            self.run(["cmd", "/c", "mklink", "/J", str(dst), str(nm)], str(wt), timeout=30)
        with socket.socket() as s: s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "-d", str(wt)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import time; time.sleep(1)
            rc, o = self.run(cmd, str(wt), env={"QA_ORIGIN": f"http://127.0.0.1:{port}"}, timeout=240)
        finally:
            srv.terminate()
            try: srv.wait(10)
            except subprocess.TimeoutExpired: srv.kill()
        if rc and INFRA.search(o): rc = RC_INFRA
        return rc, o

    @staticmethod
    def relacionados(wt, tocados, criterio, ya):
        """Tests ya existentes que el criterio de aceptacion cita o que son hermanos de un modulo .py tocado (tests/test_<modulo>*.py)."""
        cand = set(re.findall(r"tests?/[\w./-]+\.(?:py|mjs|js)", criterio or ""))
        for t in tocados:
            st = Path(t).stem
            if t.endswith(".py"): cand |= {str(x.relative_to(wt)).replace("\\", "/") for x in (Path(wt) / "tests").glob(f"test_{st.replace('-', '_')}*.py")}
        return sorted(x for x in cand if x not in ya and (Path(wt) / x).exists() and Pr.comando_test(x))

    def candidatas(self, c):
        """Solo causas APROBADAS por Claude (decision='corregir'): sin aprobacion no hay desarrollo ni PR."""
        return c.execute("""SELECT * FROM triaje WHERE parche IS NOT NULL AND decision='corregir' AND clase IN ('defecto_web','test_roto')
          AND COALESCE(pr_estado,'') IN ('','reintentar') ORDER BY COALESCE(prioridad,'3'), id""").fetchall()

    FALLOS_SIN_PR = ("no_reproduce", "validacion_fallida", "sin_test", "parche_no_encaja", "conflicto_main")

    def _marca(self, c, row, estado, detalle="", url=None):
        c.execute("UPDATE triaje SET pr_estado=?,pr_detalle=?,pr_url=COALESCE(?,pr_url),actualizado=? WHERE id=?", (estado, detalle[:900], url, self.q.now(), row["id"])); c.commit()

    def preparar(self, c, row, demo=False, push=True):
        """Parche validado -> rama qa-fix/* en worktree aislado desde origin/main -> prueba -> PR (sin merge). Devuelve el estado final."""
        firma = row["firma"] or f"t{row['id']}"
        rama = f"qa-fix/{re.sub(r'[^0-9a-zA-Z]', '', firma)[:12]}" + ("-demo" if demo else "")
        if not rama.startswith("qa-fix/") or rama in ("main", "master"): return "bloqueada"
        otra = c.execute("SELECT pr_url FROM triaje WHERE firma=? AND id<>? AND pr_url IS NOT NULL AND pr_estado IN ('pr_abierta','pr_borrador') ORDER BY id LIMIT 1", (row["firma"], row["id"])).fetchone()
        if otra and not demo:  # misma causa que otra fila con PR viva: se vincula, no se duplica ni se reescribe su rama
            self._marca(c, row, "duplicada", f"cubierta por {otra[0]}", otra[0]); return "duplicada"
        if not demo and row["decision"] != "corregir":
            self._marca(c, row, "sin_aprobacion", "sin decision 'corregir' de Claude: no se desarrolla ni se abre PR"); return "sin_aprobacion"
        norm = json.loads(row["parche"])
        wt = Path(self.q.STATE) / "pr" / rama.replace("/", "_")
        try:
            rc, o = self.git("fetch", "origin", "main", timeout=180)
            if rc: self._marca(c, row, "reintentar", f"fetch fallo: {o[-200:]}"); return "reintentar"
            if wt.exists(): self.limpiar(wt, rama)
            wt.parent.mkdir(parents=True, exist_ok=True)
            rc, o = self.git("worktree", "add", "-B", rama, str(wt), "origin/main")
            if rc: self._marca(c, row, "reintentar", f"worktree fallo: {o[-200:]}"); return "reintentar"
            base = self.git("rev-parse", "HEAD", cwd=wt)[1].strip()
            tests = self._rutas_tests(c, json.loads(row["propuestas"] or "[]"))
            existian = {t for t in tests if (wt / t).exists()}
            if tests and len(existian) < len(tests): self._traer_tests(c, row, wt, tests)  # el test vive en la rama gpt-qa, no en main: entra como regresion
            if not tests or not all((wt / t).exists() and self.comando_test(t) for t in tests):
                self._marca(c, row, "sin_test", "sin test automatico ejecutable que reproduzca el defecto: no se abre PR"); return "sin_test"
            # 1) el defecto se reproduce en main (baseline): si todos los tests ya pasan, no hay nada que corregir
            antes = [(t, self._test(wt, t)) for t in tests]
            if any(rc == RC_INFRA for _, (rc, _o) in antes):
                self._marca(c, row, "reintentar", "entorno de test no disponible (modulo/navegador/servidor): " + antes[0][1][1][-200:]); return "reintentar"
            if all(rc == 0 for _, (rc, _o) in antes):
                self._marca(c, row, "no_reproduce", "en main los tests ya pasan: defecto no reproducible o ya resuelto"); return "no_reproduce"
            try: tocados = aplicar_parche(wt, norm)
            except ValueError as e: self._marca(c, row, "parche_no_encaja", str(e)); return "parche_no_encaja"
            # 2) tras el parche pasan los tests, los verificadores del repo y no hay cambios fuera de alcance
            crit = (json.loads(row["decision_json"] or "{}") or {}).get("criterio_aceptacion", "")
            rel = self.relacionados(wt, tocados, crit, set(tests))
            verif, verde = self._verificar(wt, tests + rel, tocados)
            if not verde: self._marca(c, row, "validacion_fallida", verif); return "validacion_fallida"
            for cmd in verificadores(wt, tocados):
                rc, o = self.run(cmd, str(wt), timeout=300)
                if rc: self._marca(c, row, "validacion_fallida", f"{' '.join(cmd[1:])} fallo (exit {rc}): {o[-300:]}"); return "validacion_fallida"
                verif += f"\n- `{' '.join(cmd[1:])}`: OK"
            verif = "Baseline en main: " + ", ".join(f"`{t}` falla (exit {rc})" if rc else f"`{t}` pasa" for t, (rc, _o) in antes) + "\n" + verif
            self.git("add", "-A", cwd=wt)
            extra = [x for x in self.git("diff", "--cached", "--name-only", cwd=wt)[1].split() if x not in set(tocados) | set(tests) and "__pycache__" not in x and not x.endswith(".pyc")]
            if extra: self._marca(c, row, "validacion_fallida", f"cambios fuera de alcance: {', '.join(extra)[:300]}"); return "validacion_fallida"
            if self.git("diff", "--cached", "--quiet", cwd=wt)[0] == 0: self._marca(c, row, "sin_cambios", "el parche no cambia nada"); return "sin_cambios"
            tit = ("[DEMO] " if demo else "") + f"fix(qa-gpt): {row['causa_raiz'][:70]}"
            rc, o = self.git("-c", "user.name=qa-gpt", "-c", "user.email=qa-gpt@users.noreply.github.com", "commit", "-q", "-m", tit + f"\n\nfirma {firma}", cwd=wt)
            if rc: self._marca(c, row, "reintentar", f"commit fallo: {o[-200:]}"); return "reintentar"
            if not push: self._marca(c, row, "listo_local", verif); return "listo_local"
            # 3) main no se movio con conflicto mientras validabamos
            self.git("fetch", "origin", "main", timeout=180)
            if self.git("rev-parse", "origin/main")[1].strip() != base and self.git("rebase", "origin/main", cwd=wt)[0]:
                self.git("rebase", "--abort", cwd=wt); self._marca(c, row, "conflicto_main", "main cambio y el parche ya no se aplica limpio"); return "conflicto_main"
            sha = self.git("rev-parse", "HEAD", cwd=wt)[1].strip()
            try: self.gh.push(sha, rama)
            except RuntimeError as e:
                if "rejected" in str(e) or "non-fast" in str(e): self._marca(c, row, "rama_existente", f"{rama} ya existe en origin con otro historial: revisar la PR existente"); return "rama_existente"
                raise
            url = self.gh.pr_crear(rama, tit, cuerpo_pr(row, tests, verif, demo), borrador=demo)
            estado = "pr_borrador" if demo else "pr_abierta"
            self._marca(c, row, estado, verif, url)
            m = re.search(r"/pull/(\d+)", url or "")
            if not demo: c.execute("UPDATE triaje SET pr_numero=?,pr_nueva=1,pr_head=?,dev_estado='pr_abierta' WHERE id=?", (int(m.group(1)) if m else 0, sha, row["id"])); c.commit()
            return estado
        finally:
            self.limpiar(wt, None)

    def _traer_tests(self, c, row, wt, tests):
        for it in json.loads(row["items"] or "[]"):
            rama, _, sha = it.partition("@")
            for t in tests:
                rc, o = self.git("show", f"{rama}:{t}")
                if rc == 0:
                    p = wt / t; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(o, encoding="utf-8", newline="")

    def _verificar(self, wt, tests, tocados):
        """Ejecuta SOLO los tests conocidos (rutas de propuestas) con interprete fijo; nunca algo que haya escrito GPT."""
        if not tests: return "Sin test automatico asociado.", False
        res, verde = [], True
        for t in tests:
            cmd = self.comando_test(t)
            if not cmd or not (wt / t).exists(): res.append(f"- `{t}`: no ejecutable aqui"); verde = False; continue
            rc, o = self._test(wt, t)
            res.append(f"- `{t}`: {'PASA' if rc == 0 else 'FALLA'} (exit {rc})" + ("" if rc == 0 else f"\n  {o[-300:].strip()}")); verde = verde and rc == 0
        return "Tests tras el parche:\n" + "\n".join(res), verde

    def limpiar(self, wt, rama):
        if Path(wt).exists():
            nmj = Path(wt) / "node_modules"
            if nmj.exists():
                try: os.rmdir(nmj)  # junction: quita solo el enlace, nunca el contenido
                except OSError: pass
            self.git("worktree", "remove", "--force", str(wt))
            shutil.rmtree(wt, ignore_errors=True)
        self.git("worktree", "prune")
        if rama: self.git("branch", "-D", rama)


def correr(q, c, push=True, demo=False, limite=2, out=print):
    """Prepara PR para las causas con parche validado aun sin PR. Como mucho `limite` por pasada; nunca fusiona."""
    import qa_lote as L
    pr = Pr(q, L.Gh(q), L.run_cmd, out)
    for row in pr.candidatas(c)[:limite]:
        est = pr.preparar(c, row, demo=demo, push=push); out(f"  PR {row['firma']}: {est}")


def cmd_pr(q, a):
    c = q.db(); correr(q, c, push=not getattr(a, "local", False), demo=getattr(a, "demo", False))
    for r in c.execute("SELECT firma,clase,pr_estado,pr_url FROM triaje WHERE pr_estado IS NOT NULL"): print(" ", r["firma"], r["clase"], r["pr_estado"], r["pr_url"] or "")


# ---------- ciclo continuo: presupuesto -> desarrollo -> PR -> CI -> revision de Claude -> integracion ----------
FLUJO = {"activo": True, "max_pr_activas": 3, "max_desarrollos": 1, "max_revisiones": 1, "max_consultas_gpt": 2, "max_intentos": 2, "claude_lote": 4,
         "ciclo_s": 120, "flujo_desde": None, "integracion": {"modo": "recomendacion", "calibracion_min": 10, "riesgo_max": "bajo"}}
RIESGOS = ("bajo", "medio", "alto")
TERMINALES = "'integrada','cerrada','no_reproduce','sin_test','descartada','duplicada'"
SISTEMA_REVISION = ("Eres el revisor tecnico final de una PR generada por automatizacion en un sitio web estatico. Recibes el criterio de aceptacion aprobado, "
                    "la causa, el resultado de CI y el diff. Decide: 'integrar' (corrige la causa con alcance minimo y sin riesgo evidente), 'revisar' (dudas concretas "
                    "que un humano debe mirar), 'rechazar' (no corrige, es incorrecta o excede el alcance) o 'intervencion' (toca algo sensible o no se puede juzgar). "
                    "CI verde no basta: valora si el diff cumple el criterio y no rompe otras partes. Se breve. Responde SOLO con el JSON del esquema.")
ESQUEMA_REVISION = {"type": "object", "required": ["veredicto", "riesgo", "cumple_criterio", "motivos"], "properties": {
    "veredicto": {"type": "string", "enum": ["integrar", "revisar", "rechazar", "intervencion"]}, "riesgo": {"type": "string", "enum": list(RIESGOS)},
    "cumple_criterio": {"type": "boolean"}, "motivos": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    "cambios_pedidos": {"type": "array", "items": {"type": "string"}, "maxItems": 6}}}


def flujo(q):
    cfg = q.CFG.get("flujo") or {}
    return {**FLUJO, **cfg, "integracion": {**FLUJO["integracion"], **(cfg.get("integracion") or {})}}


def ci_estado(roll):
    """verde / rojo / pendiente a partir de statusCheckRollup de GitHub."""
    if not roll: return "pendiente"
    mal = any(x.get("conclusion") in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE") or x.get("state") in ("FAILURE", "ERROR") for x in roll)
    if mal: return "rojo"
    pend = any((x.get("status") not in (None, "COMPLETED")) or x.get("state") in ("PENDING", "EXPECTED") for x in roll)
    return "pendiente" if pend else "verde"


class Ciclo:
    """Un paso idempotente del flujo; cada hilo usa su propia conexion. Si GitHub falla, el error sube al llamador (se reintenta en el siguiente paso)."""
    def __init__(self, q, gh, runner, out=print):
        self.q, self.gh, self.out = q, gh, out
        self.pr = Pr(q, gh, runner, out)

    @staticmethod
    def _archivos_parche(row):
        try: return {f["ruta"] for f in json.loads(row["parche"])["ficheros"]}
        except (TypeError, ValueError, KeyError): return set()

    def paso(self, c):
        import qa_triaje
        q, cfg = self.q, flujo(self.q); r = {}
        prs = self.gh.prs_abiertas(); abiertas = {p["number"]: p for p in prs}
        # PR nuevas que ya no estan abiertas: integradas (a mano o por el sistema) o cerradas
        activas = []
        for row in c.execute("SELECT * FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'").fetchall():
            if row["pr_numero"] in abiertas: activas.append(row); continue
            st = self.gh.pr_ver(row["pr_numero"]).get("state")
            if st == "MERGED": c.execute("UPDATE triaje SET pr_estado='integrada',integracion=CASE WHEN integracion='recomendada' THEN 'integrada_acierto' ELSE COALESCE(integracion,'integrada') END,actualizado=? WHERE id=?", (q.now(), row["id"]))
            else: c.execute("UPDATE triaje SET pr_estado='cerrada',integracion=CASE WHEN integracion='recomendada' THEN 'cerrada_desacuerdo' ELSE COALESCE(integracion,'cerrada') END,actualizado=? WHERE id=?", (q.now(), row["id"]))
            c.commit(); self.out(f"  PR #{row['pr_numero']}: {st}")
        libres = cfg["max_pr_activas"] - len(activas)
        # 1) decisiones de Claude, solo mientras el backlog aprobado no llene el presupuesto (no se gasta en decidir lo que no se podra desarrollar)
        aprobadas = c.execute(f"SELECT COUNT(*) FROM triaje WHERE decision='corregir' AND COALESCE(pr_estado,'') NOT IN ({TERMINALES})").fetchone()[0]
        if aprobadas < cfg["max_pr_activas"] * 2: r["decididas"] = qa_triaje.decidir_pendientes(q, c, prs, cfg["claude_lote"], self.out)
        # 2) desarrollo GPT: causas aprobadas sin parche, o con intento fallido (acotado por max_intentos)
        en_cola = c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='T' AND clave LIKE 'D:%' AND estado IN ('pendiente','en_curso')").fetchone()[0]
        for row in c.execute(f"""SELECT * FROM triaje WHERE decision='corregir' AND clase IN ('defecto_web','test_roto') AND COALESCE(dev_estado,'')<>'en_desarrollo' AND
                (parche IS NULL OR pr_estado IN ('validacion_fallida','parche_no_encaja','conflicto_main') OR dev_estado IN ('parche_invalido','sin_parche'))
                AND COALESCE(pr_estado,'') NOT IN ({TERMINALES},'pr_abierta') ORDER BY COALESCE(prioridad,'3'), id""").fetchall():
            if en_cola >= cfg["max_consultas_gpt"]: break
            if (row["intentos_dev"] or 0) >= cfg["max_intentos"]:
                c.execute("UPDATE triaje SET dev_estado='agotado',pr_estado='descartada',actualizado=? WHERE id=?", (q.now(), row["id"])); c.commit(); r["agotadas"] = r.get("agotadas", 0) + 1; continue
            if qa_triaje.encolar_desarrollo(q, c, row, row["pr_detalle"] or row["validacion"] or ""):
                c.execute("UPDATE triaje SET pr_estado='esperando_desarrollo' WHERE id=?", (row["id"],)); c.commit(); en_cola += 1; r["desarrollos"] = r.get("desarrollos", 0) + 1
        # 3) admision de PR nuevas: presupuesto y sin solape de archivos con PR abiertas ni entre si
        # solo bloquea el solape con PR del flujo nuevo (se serializan); el backlog heredado no frena correcciones buenas: se anota y Claude lo valora en la revision
        nuevas = {r_["pr_numero"] for r_ in c.execute("SELECT pr_numero FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'")}
        ocupados = {f["path"] for p in prs if p["number"] in nuevas for f in p.get("files", [])}
        self._prs = prs
        hechas = 0
        for row in self.pr.candidatas(c):
            if libres <= 0 or hechas >= cfg["max_desarrollos"]: break
            if self._archivos_parche(row) & ocupados: r["solapadas"] = r.get("solapadas", 0) + 1; continue
            est = self.pr.preparar(c, row); self.out(f"  PR {row['firma']}: {est}"); hechas += 1
            if est == "pr_abierta": libres -= 1; ocupados |= self._archivos_parche(row); r["pr_nuevas"] = r.get("pr_nuevas", 0) + 1
        # 4) CI y revision final de Claude (una vez por commit)
        revisadas = 0
        for row in c.execute("SELECT * FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'").fetchall():
            v = self.gh.pr_ver(row["pr_numero"]); head = v.get("headRefOid"); ci = ci_estado(v.get("statusCheckRollup"))
            if v.get("mergeable") == "CONFLICTING": c.execute("UPDATE triaje SET integracion='conflicto',pr_head=? WHERE id=?", (head, row["id"])); c.commit(); continue
            if ci == "rojo": c.execute("UPDATE triaje SET integracion='ci_rojo',pr_head=? WHERE id=?", (head, row["id"])); c.commit(); r["ci_rojo"] = r.get("ci_rojo", 0) + 1; continue
            if ci != "verde" or v.get("isDraft") or row["revision_hash"] == head or revisadas >= cfg["max_revisiones"]: continue
            rev = self.revisar(c, row, head); revisadas += 1; r["revisadas"] = revisadas
            if rev and rev["veredicto"] == "integrar" and rev["cumple_criterio"] and RIESGOS.index(rev["riesgo"]) <= RIESGOS.index(cfg["integracion"]["riesgo_max"]):
                c.execute("UPDATE triaje SET integracion='recomendada' WHERE id=?", (row["id"],)); self._integrar(c, row, head, v, cfg)
            elif rev: c.execute("UPDATE triaje SET integracion=? WHERE id=?", ("revisar" if rev["veredicto"] == "integrar" else rev["veredicto"], row["id"]))
            c.commit()
        r["pr_activas"] = c.execute("SELECT COUNT(*) FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'").fetchone()[0]
        r["pr_legado"] = len(abiertas) - r["pr_activas"]; r["fecha"] = q.now()
        try: (q.STATE / "lote" / "ciclo.json").write_text(json.dumps(r), encoding="utf-8")
        except OSError: pass
        return r

    def revisar(self, c, row, head):
        import qa_claude, qa_triaje
        d = qa_triaje._j(row["decision_json"], {}) or {}
        try: diff = self.gh.pr_diff(row["pr_numero"])[:14000]
        except Exception as e: self.out(f"  revision omitida (diff no disponible: {str(e)[:80]})"); return None
        mios = {m for m in re.findall(r"^diff --git a/(\S+)", diff, re.M)}
        solapes = sorted({p["number"] for p in getattr(self, "_prs", []) if p["number"] != row["pr_numero"] and mios & {f["path"] for f in p.get("files", [])}})[:10]
        entrada = json.dumps({"causa": row["causa_raiz"], "criterio_aceptacion": d.get("criterio_aceptacion"), "ci": "verde", "prioridad": d.get("prioridad"),
                              "solapa_con_prs_abiertas": solapes, "diff": diff}, ensure_ascii=False)
        try: rev, _ = qa_claude.llamar(self.q, c, f"revision:{row['id']}@{head}", "revision", SISTEMA_REVISION, entrada, ESQUEMA_REVISION)
        except qa_claude.ClaudeError as e: self.out(f"  Claude revision: {str(e)[:120]}"); return None
        c.execute("UPDATE triaje SET revision=?,revision_hash=?,pr_head=?,actualizado=? WHERE id=?", (json.dumps(rev, ensure_ascii=False), head, head, self.q.now(), row["id"])); c.commit()
        self.out(f"  Claude revisa PR #{row['pr_numero']}: {rev['veredicto']} (riesgo {rev['riesgo']})")
        return rev

    def _integrar(self, c, row, head, v, cfg):
        """Solo en modo 'auto', tras la calibracion (suficientes recomendaciones que un humano confirmo) y con GitHub en CLEAN: merge atado al commit revisado."""
        ig = cfg["integracion"]
        if ig["modo"] != "auto": return
        aciertos = c.execute("SELECT COUNT(*) FROM triaje WHERE integracion='integrada_acierto'").fetchone()[0]
        if aciertos < ig["calibracion_min"] or v.get("mergeStateStatus") != "CLEAN": return
        self.gh.pr_merge(row["pr_numero"], head)
        c.execute("UPDATE triaje SET pr_estado='integrada',integracion='integrada_auto' WHERE id=?", (row["id"],)); c.commit()
        self.out(f"  PR #{row['pr_numero']} integrada por el sistema")
