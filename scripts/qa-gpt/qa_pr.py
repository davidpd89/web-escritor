"""PR automaticas a partir del analisis GPT. Todo lo que devuelve GPT es una PROPUESTA: aqui se valida y solo se aplica en un worktree
aislado creado desde origin/main. Nunca ejecuta comandos que haya escrito GPT.
Solo se desarrollan causas que Claude aprobo (decision='corregir'). Una PR solo se abre si el defecto se reproduce en main (baseline), el parche
lo corrige, pasan los verificadores del repo y no hay cambios fuera de alcance; si algo falla NO hay PR (ni en borrador): queda el motivo en
`pr_estado` y el ciclo reintenta de forma acotada. Despues, `Ciclo` gestiona presupuesto, CI, revision final de Claude e integracion."""
import json, os, re, shutil, socket, subprocess, sys
from pathlib import Path

MAX_FICHEROS = 5
RC_INFRA = 125
RC_ABORTADO = 130


class Interrumpido(Exception):
    """Parada solicitada (Q/Ctrl+C) durante una validacion: no es un fallo del parche ni consume intento."""
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
                  ("Riesgos", "El criterio lo fijo Claude antes del desarrollo; tras el CI, Claude revisa el diff contra ese criterio. Si Claude recomienda integrar (riesgo bajo, cumple criterio), el CI es verde y GitHub la da por CLEAN, el sistema la fusiona atada al commit revisado."),
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


GIT_LOCK = __import__("threading").RLock()  # git del repo compartido (fetch/worktree/push) en serie; los tests de cada worktree corren en paralelo


class Pr:
    def __init__(self, q, gh, runner, out=print):
        self.q, self.gh, self.out = q, gh, out
        def run(*a, **k):
            rc, o = runner(*a, **k)
            if rc == RC_ABORTADO: raise Interrumpido()
            return rc, o
        self.run = run
        self.root = q.ROOT

    def git(self, *a, cwd=None, timeout=300):
        with GIT_LOCK: return self.run(["git", "-c", "core.autocrlf=false", *a], str(cwd or self.root), timeout=timeout)  # LF como en CI: con autocrlf=true los artefactos generados (feed.xml...) difieren byte a byte y los --check fallan

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
          AND COALESCE(pr_estado,'') IN ('','reintentar') ORDER BY (pr_estado='reintentar'), COALESCE(prioridad,'3'), id""").fetchall()

    FALLOS_SIN_PR = ("test_no_fiable", "no_reproduce", "validacion_fallida", "sin_test", "parche_no_encaja", "conflicto_main")

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
            if any(rc == RC_INFRA and "ERR_MODULE_NOT_FOUND" in _o and "/pr/qa-fix_" in _o.replace("\\", "/") for _, (rc, _o) in antes):
                # el test importa un fichero auxiliar del repo que no esta en main ni viajo con el test: reintentar no lo arregla
                self._marca(c, row, "test_no_fiable", "el test importa un modulo auxiliar inexistente en main (" + antes[0][1][1][-160:].strip() + ")"); return "test_no_fiable"
            if any(rc == RC_INFRA for _, (rc, _o) in antes):
                self._marca(c, row, "reintentar", "entorno de test no disponible (modulo/navegador/servidor): " + antes[0][1][1][-200:]); return "reintentar"
            if all(rc == 0 for _, (rc, _o) in antes):
                self._marca(c, row, "no_reproduce", "en main los tests ya pasan: defecto no reproducible o ya resuelto"); return "no_reproduce"
            # un fallo por timeout sin ninguna asercion no demuestra el defecto: el test no llega a comprobarlo (p. ej. espera un estado que nunca se da)
            fallan = [o for _, (rc, o) in antes if rc]
            if fallan and all("TimeoutError" in o and "AssertionError" not in o for o in fallan):
                self._marca(c, row, "test_no_fiable", "en main el test agota el tiempo sin llegar a ninguna aserción: no demuestra el defecto. " + fallan[0][-300:]); return "test_no_fiable"
            prev = {" ".join(cm): self.run(cm, str(wt), timeout=300)[0] for cm in verificadores(wt, [f["ruta"] for f in norm["ficheros"]])}
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
            if not demo and flujo(self.q)["modo_pr"] == "lote":  # la PR se abre despues, agrupada con otras correcciones ya validadas (un solo CI pesado)
                self.git("fetch", "origin", rama, timeout=120)
                if self.git("rev-parse", f"origin/{rama}")[1].strip() != sha:
                    try: self.gh.push(sha, rama)
                    except RuntimeError as e:
                        if "rejected" in str(e) or "non-fast" in str(e): self._marca(c, row, "rama_existente", f"{rama} ya existe en origin con otro historial"); return "rama_existente"
                        raise
                self._marca(c, row, "listo_lote", verif)
                c.execute("UPDATE triaje SET pr_head=?,dev_estado='listo_lote' WHERE id=?", (sha, row["id"])); c.commit(); return "listo_lote"
            # reanudacion tras un corte: si ya hay PR abierta para esta rama se vincula (nunca se crea otra); si la rama remota tiene el mismo arbol, no se reescribe
            previa = self.gh.pr_de_rama(rama) if not demo and hasattr(self.gh, "pr_de_rama") else None
            if previa:
                url = previa["url"]; self._marca(c, row, "pr_abierta", verif, url)
                c.execute("UPDATE triaje SET pr_numero=?,pr_nueva=1,pr_head=?,dev_estado='pr_abierta' WHERE id=?", (previa["number"], previa.get("headRefOid") or sha, row["id"])); c.commit()
                self.out(f"  PR ya existente #{previa['number']}: vinculada sin duplicar"); return "pr_abierta"
            self.git("fetch", "origin", rama, timeout=120)
            remoto = self.git("rev-parse", f"origin/{rama}^{{tree}}")
            if remoto[0] == 0 and remoto[1].strip() == self.git("rev-parse", "HEAD^{tree}", cwd=wt)[1].strip(): sha = self.git("rev-parse", f"origin/{rama}")[1].strip()
            else:
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
        except Interrumpido:
            self.out("  validacion interrumpida por parada: sin cambios de estado, se repite al reanudar"); return "interrumpida"
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
            try: self.git("worktree", "remove", "--force", str(wt))
            except Interrumpido: pass  # con la parada activa no se ejecuta nada; el borrado de carpeta basta y `prune` lo reconcilia al reanudar
            shutil.rmtree(wt, ignore_errors=True)
        try:
            self.git("worktree", "prune")
            if rama: self.git("branch", "-D", rama)
        except Interrumpido: pass


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
CI_REQUERIDOS_RULESET = ("Required merge gate", "public-artifact-contract", "reflow-sitewide", "pa11y-baseline", "lighthouse", "Compare against committed baselines")

FLUJO = {"activo": True, "max_pr_activas": 3, "max_desarrollos": 1, "max_revisiones": 1, "max_consultas_gpt": 2, "max_intentos": 2, "claude_lote": 4,
         "ciclo_s": 120, "flujo_desde": None, "modo_pr": "pr", "lote": {"min": 3, "max": 8, "espera_h": 8, "max_activos": 3}, "integracion": {"modo": "auto", "calibracion_min": 0, "riesgo_max": "bajo"}, "ci_requeridos": [], "max_validaciones": 8, "validadores": 4}
RIESGOS = ("bajo", "medio", "alto")
TERMINALES = "'rechazada_revision','integrada','cerrada','no_reproduce','test_no_fiable','sin_test','descartada','duplicada'"
SISTEMA_REVISION = ("Eres el revisor tecnico final de una PR generada por automatizacion en un sitio web estatico. Recibes el criterio de aceptacion aprobado, "
                    "la causa, el resultado de CI y el diff. Decide: 'integrar' (corrige la causa con alcance minimo y sin riesgo evidente), 'revisar' (dudas concretas "
                    "que un humano debe mirar), 'rechazar' (no corrige, es incorrecta o excede el alcance) o 'intervencion' (toca algo sensible o no se puede juzgar). "
                    "CI verde no basta: valora si el diff cumple el criterio y no rompe otras partes. Se breve. Responde SOLO con el JSON del esquema. "
                    "Contexto: una PR puede agrupar varias causas independientes A PROPOSITO (lote); eso no es motivo para 'revisar'. Cada causa ya fue reproducida (el test falla en main y pasa con el parche) "
                    "y el CI completo del repo esta en verde. El diff puede venir truncado y el solape con otras PR abiertas es normal: no pidas 'revisar' por no ver todo el diff ni por solapes, "
                    "solo por un defecto concreto y visible en lo que se muestra. Sugerencias de estilo o refactor no cambian el veredicto 'integrar'. "
                    "Si el lote contiene una o varias causas DEFECTUOSAS (cada causa lleva su id entre corchetes), pon esos ids en excluir_ids: se sacan del lote y las demas siguen; no bloquees el lote entero por una.")
ESQUEMA_REVISION = {"type": "object", "required": ["veredicto", "riesgo", "cumple_criterio", "motivos"], "properties": {
    "veredicto": {"type": "string", "enum": ["integrar", "revisar", "rechazar", "intervencion"]}, "riesgo": {"type": "string", "enum": list(RIESGOS)},
    "cumple_criterio": {"type": "boolean"}, "motivos": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    "cambios_pedidos": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
    "excluir_ids": {"type": "array", "items": {"type": "integer"}}}}


def flujo(q):
    cfg = q.CFG.get("flujo") or {}
    return {**FLUJO, **cfg, "integracion": {**FLUJO["integracion"], **(cfg.get("integracion") or {})}, "lote": {**FLUJO["lote"], **(cfg.get("lote") or {})}}


def ci_estado(roll, requeridos=None):
    """verde / rojo / pendiente a partir de statusCheckRollup de GitHub. Con `requeridos` (nombres del ruleset) un check lento NO requerido pendiente no bloquea; uno rojo si."""
    if not roll: return "pendiente"
    mal = any(x.get("conclusion") in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE") or x.get("state") in ("FAILURE", "ERROR") for x in roll)
    if mal: return "rojo"
    pend = any(((x.get("status") not in (None, "COMPLETED")) or x.get("state") in ("PENDING", "EXPECTED")) and (not requeridos or (x.get("name") or x.get("context")) in requeridos) for x in roll)
    if requeridos and not pend and not {x.get("name") or x.get("context") for x in roll} >= set(requeridos): return "pendiente"
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

    def _dev_claude(self):
        import qa_dev_claude
        c = self.q.db()
        try:
            for row in qa_dev_claude.elegible(c, 1):
                self.out(f"  dev Claude #{row['id']}: {qa_dev_claude.desarrollar(self.q, c, self.pr, row)}")
        except Interrumpido: pass
        except Exception as e: self.out(f"  dev Claude fallo: {str(e)[:200]}")
        finally: c.close()

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
        aprobadas = c.execute(f"SELECT COUNT(*) FROM triaje WHERE decision='corregir' AND COALESCE(pr_estado,'') NOT IN ({TERMINALES},'pr_abierta','pr_borrador')").fetchone()[0]  # las que ya tienen PR no ocupan cola de desarrollo
        if aprobadas < cfg["max_pr_activas"] * 3: r["decididas"] = qa_triaje.decidir_pendientes(q, c, prs, cfg["claude_lote"], self.out)
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
        # 2b) desarrollador Claude en segundo plano (una correccion cada vez, un intento por causa) para lo que el parche GPT no consiguio
        h = getattr(self, "_dev_hilo", None)
        if cfg.get("dev_claude", False) and (h is None or not h.is_alive()):
            self._dev_hilo = __import__("threading").Thread(target=self._dev_claude, daemon=True, name="DevClaude"); self._dev_hilo.start()
        # 3) admision de PR nuevas: presupuesto y sin solape de archivos con PR abiertas ni entre si
        # solo bloquea el solape con PR del flujo nuevo (se serializan); el backlog heredado no frena correcciones buenas: se anota y Claude lo valora en la revision
        nuevas = {r_["pr_numero"] for r_ in c.execute("SELECT pr_numero FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'")}
        ocupados = {f["path"] for p in prs if p["number"] in nuevas for f in p.get("files", [])}
        self._prs = prs
        if cfg["modo_pr"] == "lote":
            r["adoptadas"] = self._adoptar_legado(c, abiertas)
            r["cerradas"] = self._cerrar_superadas(c, prs)
        hechas = 0
        if cfg["modo_pr"] == "lote":  # validacion determinista en paralelo (worktrees aislados); el lote se forma despues
            cands = self.pr.candidatas(c)[:cfg["max_validaciones"]]
            if cands:
                from concurrent.futures import ThreadPoolExecutor
                def _val(row):
                    cc = q.db(); cc.execute("PRAGMA busy_timeout=180000")
                    try: return row, self.pr.preparar(cc, row)
                    except Exception as e: return row, "error: " + str(e)[:120]
                    finally: cc.close()
                with ThreadPoolExecutor(max_workers=cfg["validadores"]) as ex:
                    for row, est in ex.map(_val, cands): self.out(f"  PR {row['firma']}: {est}"); hechas += 1
                r["validadas"] = hechas
        else:
            for row in self.pr.candidatas(c):
                if libres <= 0 or hechas >= cfg["max_desarrollos"]: break
                if self._archivos_parche(row) & ocupados: r["solapadas"] = r.get("solapadas", 0) + 1; continue
                est = self.pr.preparar(c, row); self.out(f"  PR {row['firma']}: {est}"); hechas += 1
                if est == "pr_abierta": libres -= 1; ocupados |= self._archivos_parche(row); r["pr_nuevas"] = r.get("pr_nuevas", 0) + 1
        if cfg["modo_pr"] == "lote": self._lote(c, cfg, r)
        # 4) CI y revision final de Claude (una vez por commit y por PR, aunque agrupe varias causas)
        revisadas = 0; vistas = set()
        for row in c.execute("SELECT * FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta' ORDER BY id").fetchall():
            if row["pr_numero"] in vistas: continue
            vistas.add(row["pr_numero"])
            v = self.gh.pr_ver(row["pr_numero"]); head = v.get("headRefOid"); ci = ci_estado(v.get("statusCheckRollup"), cfg.get("ci_requeridos") or None)
            if v.get("mergeable") == "CONFLICTING" and cfg["modo_pr"] == "lote":
                # otro lote entro en main y este ya no aplica: se cierra y sus correcciones vuelven a la cola para rehacerse sobre el main actual
                try: self.gh.pr_cerrar(row["pr_url"], "Conflicto con main tras fusionarse otro lote: las correcciones vuelven a la cola y se reagrupan sobre el main actual")
                except Exception as e: self.out(f"  lote #{row['pr_numero']}: no se pudo cerrar ({str(e)[-80:]})")
                else:
                    c.execute("UPDATE triaje SET pr_estado='listo_lote',integracion=NULL,pr_nueva=0,pr_numero=0,dev_estado='listo_lote',revision=NULL,revision_hash=NULL,actualizado=? WHERE pr_numero=? AND pr_nueva=1", (q.now(), row["pr_numero"])); c.commit()
                    r["lotes_reencolados"] = r.get("lotes_reencolados", 0) + 1; self.out(f"  lote #{row['pr_numero']} en conflicto: reencolado"); continue
            if v.get("mergeable") == "CONFLICTING": c.execute("UPDATE triaje SET integracion='conflicto',pr_head=? WHERE pr_numero=? AND pr_nueva=1", (head, row["pr_numero"])); c.commit(); continue
            if ci == "rojo" and cfg["modo_pr"] == "lote" and c.execute("SELECT COUNT(*) FROM triaje WHERE pr_numero=? AND pr_nueva=1", (row["pr_numero"],)).fetchone()[0] > 1:
                try: self.gh.pr_cerrar(row["pr_url"], "CI rojo en el lote: se divide en mitades para localizar la correccion culpable (biseccion)")
                except Exception as e: self.out(f"  lote #{row['pr_numero']}: no se pudo cerrar ({str(e)[-80:]})")
                else:
                    c.execute("UPDATE triaje SET pr_estado='listo_lote',integracion='ci_rojo_lote',pr_nueva=0,pr_numero=0,dev_estado='listo_lote',actualizado=? WHERE pr_numero=? AND pr_nueva=1", (q.now(), row["pr_numero"])); c.commit()
                    r["lotes_divididos"] = r.get("lotes_divididos", 0) + 1; self.out(f"  lote #{row['pr_numero']} en rojo: dividido"); continue
            if ci == "rojo": c.execute("UPDATE triaje SET integracion='ci_rojo',pr_head=? WHERE pr_numero=? AND pr_nueva=1", (head, row["pr_numero"])); c.commit(); r["ci_rojo"] = r.get("ci_rojo", 0) + 1; continue
            if ci == "verde" and not v.get("isDraft") and row["revision_hash"] == head and row["integracion"] == "recomendada": self._integrar(c, row, head, v, cfg); continue  # ya revisada en este commit: solo falta fusionar (o actualizar la rama)
            if ci != "verde" or v.get("isDraft") or row["revision_hash"] == head or revisadas >= cfg["max_revisiones"]: continue
            rev = self.revisar(c, row, head); revisadas += 1; r["revisadas"] = revisadas
            if rev and rev["veredicto"] == "integrar" and rev["cumple_criterio"] and RIESGOS.index(rev["riesgo"]) <= RIESGOS.index(cfg["integracion"]["riesgo_max"]):
                c.execute("UPDATE triaje SET integracion='recomendada' WHERE pr_numero=? AND pr_nueva=1", (row["pr_numero"],)); self._integrar(c, row, head, v, cfg)
            elif rev: c.execute("UPDATE triaje SET integracion=? WHERE pr_numero=? AND pr_nueva=1", ("revisar" if rev["veredicto"] == "integrar" else rev["veredicto"], row["pr_numero"]))
            c.commit()
        r["pr_activas"] = c.execute("SELECT COUNT(*) FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'").fetchone()[0]
        r["pr_legado"] = len(abiertas) - r["pr_activas"]; r["fecha"] = q.now()
        try: (q.STATE / "lote" / "ciclo.json").write_text(json.dumps(r), encoding="utf-8")
        except OSError: pass
        return r

    def _adoptar_legado(self, c, abiertas):
        """PR individuales heredadas (pre-lote) con correccion aprobada: cada una exigiria su propio CI y quedaria BEHIND tras cada fusion.
        Se reutiliza su rama ya validada como candidata de lote (sin cerrar ni tocar la PR); el lote las rehace con cherry-pick y un solo CI."""
        n = 0
        for row in c.execute("SELECT * FROM triaje WHERE pr_nueva=0 AND pr_estado='pr_abierta' AND decision='corregir'").fetchall():
            m = re.search(r"/pull/(\d+)", row["pr_url"] or "")
            pr = abiertas.get(int(m.group(1))) if m else None
            if not pr or pr.get("isDraft") or not str(pr.get("headRefName", "")).startswith("qa-fix/") or "lote" in pr["headRefName"]: continue
            c.execute("UPDATE triaje SET pr_estado='listo_lote',dev_estado='listo_lote',pr_head=?,integracion=NULL,actualizado=? WHERE id=?", (pr["headRefName"], self.q.now(), row["id"])); n += 1
        if n: c.commit(); self.out(f"  legado: {n} PR heredadas pasan a candidatas de lote")
        return n

    def _cerrar_superadas(self, c, prs):
        """Cierra, una a una y con comentario, la PR individual heredada cuya correccion ya esta fusionada dentro de un lote (su rama ya no aporta nada)."""
        por_rama = {p["headRefName"]: p for p in prs if str(p.get("headRefName", "")).startswith("qa-fix/") and "lote" not in p["headRefName"]}
        n = 0
        for row in c.execute("SELECT * FROM triaje WHERE pr_estado='integrada' AND pr_nueva=1 ORDER BY id DESC LIMIT 60").fetchall():
            rama = f"qa-fix/{re.sub(r'[^0-9a-zA-Z]', '', row['firma'] or 't' + str(row['id']))[:12]}"
            pr = por_rama.pop(rama, None)
            if not pr or n >= 10: continue
            try: self.gh.pr_cerrar(pr["url"], f"Superada: esta correccion ya esta integrada en main mediante {row['pr_url']}. GPT QA cierra la PR individual para no duplicar el CI.")
            except Exception as e: self.out(f"  no se pudo cerrar #{pr['number']}: {str(e)[:80]}"); continue
            n += 1; self.out(f"  PR heredada #{pr['number']} cerrada (integrada en {row['pr_url']})")
        return n

    @staticmethod
    def _zona(row):
        """Tipo de cambio que domina la correccion: un lote de una sola zona se revisa y se prueba como una unidad y casi no solapa con otros."""
        rutas = Ciclo._archivos_parche(row)
        prod = [x for x in rutas if not re.match(r"(tests?|qa)/", x)] or list(rutas)
        for x in sorted(prod):
            if x.endswith(".css"): return "css"
            if x.startswith("scripts/build-") or x.startswith("scripts/"): return "generadores"
            if x.endswith(".js") or x.endswith(".mjs"): return "js"
            if x.endswith((".html", ".json", ".xml", ".txt")): return "contenido"
        return "tests" if rutas else "otros"

    def _lote(self, c, cfg, r):
        """Agrupa correcciones ya validadas (rama qa-fix/t* publicada) en UNA PR: un solo CI pesado en vez de uno por correccion.
        Se abre cuando hay `min` listas, la mas antigua lleva `espera_h` horas o no queda nada en el pipeline. Cada commit se aplica con cherry-pick sobre
        origin/main y se vuelve a verificar de forma acumulada; lo que no encaja queda para el siguiente lote (o vuelve a desarrollo si va solo)."""
        import datetime
        lc = cfg["lote"]
        listos = c.execute("SELECT * FROM triaje WHERE pr_estado='listo_lote' ORDER BY COALESCE(prioridad,'3'), id").fetchall()
        if not listos: return
        sosp = [x for x in listos if x["integracion"] == "ci_rojo_lote"]  # biseccion: un lote en rojo se reparte en mitades, las sospechosas primero
        if sosp: listos = sosp[:max(1, len(sosp) // 2)]
        else:
            # sin solape con lotes abiertos: dos lotes que tocan el mismo script se estorban (el que se fusiona segundo queda en conflicto y se rehace)
            nuevas = {r_["pr_numero"] for r_ in c.execute("SELECT pr_numero FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'")}
            ocupados = {f["path"] for p_ in (getattr(self, "_prs", None) or []) if p_["number"] in nuevas for f in p_.get("files", [])}
            libres = [x for x in listos if not (self._archivos_parche(x) & ocupados)]
            if len(libres) < len(listos): self.out(f"  lote: {len(listos) - len(libres)} listas esperan (tocan archivos de un lote abierto)")
            listos = libres
            if not listos: return
            zonas = {}
            for x in listos: zonas.setdefault(self._zona(x), []).append(x)
            z, listos = max(zonas.items(), key=lambda kv: len(kv[1]))  # la zona con mas correcciones listas: lote coherente y revision localizada
            self.out(f"  lote: zona {z} ({len(listos)} de {sum(len(v) for v in zonas.values())} listas; " + ", ".join(f"{k}={len(v)}" for k, v in sorted(zonas.items())) + ")")
        if c.execute("SELECT COUNT(DISTINCT pr_numero) FROM triaje WHERE pr_nueva=1 AND pr_estado='pr_abierta'").fetchone()[0] >= lc["max_activos"]: return
        pendientes = c.execute("SELECT COUNT(*) FROM triaje WHERE decision='corregir' AND (pr_estado IN ('esperando_desarrollo','reintentar') OR (parche IS NULL AND COALESCE(pr_estado,'') NOT IN (" + TERMINALES + ")) OR (parche IS NOT NULL AND COALESCE(pr_estado,'')=''))").fetchone()[0]
        try: edad_h = (datetime.datetime.now() - min(datetime.datetime.fromisoformat(x["actualizado"]) for x in listos if x["actualizado"])).total_seconds() / 3600
        except (ValueError, TypeError): edad_h = 0
        if not sosp and len(listos) < lc["min"] and edad_h < lc["espera_h"] and pendientes: return
        rama = "qa-fix/lote-" + datetime.datetime.now().strftime("%m%d%H%M")
        wt = Path(self.q.STATE) / "pr" / rama.replace("/", "_")
        P = self.pr; incl = []; tocados_all = []
        try:
            rc, o = P.git("fetch", "origin", "main", timeout=180)
            if rc: self.out(f"  lote: fetch fallo {o[-120:]}"); return
            if wt.exists(): P.limpiar(wt, rama)
            wt.parent.mkdir(parents=True, exist_ok=True)
            if P.git("worktree", "add", "-B", rama, str(wt), "origin/main")[0]: return
            for row in listos[:lc["max"]]:
                rama_item = row["pr_head"] if str(row["pr_head"] or "").startswith("qa-fix/") and "lote" not in row["pr_head"] else f"qa-fix/{re.sub(r'[^0-9a-zA-Z]', '', row['firma'] or 't' + str(row['id']))[:12]}"
                P.git("fetch", "origin", rama_item, timeout=120)
                orig = P.git("rev-parse", f"origin/{rama_item}")  # commit original de la correccion (pr_head se sobrescribe al abrir un lote)
                if P.git("cherry-pick", orig[1].strip() if orig[0] == 0 else row["pr_head"], cwd=wt)[0]:
                    P.git("cherry-pick", "--abort", cwd=wt)
                    if not incl and len(listos) == 1: self._marca(c, row, "conflicto_main", "no se aplica limpio sobre main actual")
                    continue
                tocados = list(self._archivos_parche(row) | {x for x in P.git("show", "--name-only", "--format=", "HEAD", cwd=wt)[1].split()})
                for cmd in verificadores(wt, tocados_all + tocados):
                    rc, o = P.run(cmd, str(wt), timeout=300)
                    if rc:
                        P.git("reset", "-q", "--hard", "HEAD~1", cwd=wt)
                        if not incl: self._marca(c, row, "validacion_fallida", f"en lote: {' '.join(cmd[1:])} fallo (exit {rc}): {o[-250:]}")
                        break
                else: incl.append(row); tocados_all += tocados
            if not incl: return
            sha = P.git("rev-parse", "HEAD", cwd=wt)[1].strip()
            # revision agregada de Claude ANTES de abrir la PR: lo dudoso se saca del lote y el CI pesado solo corre sobre contenido ya aprobado
            diff = P.git("diff", "origin/main..HEAD", cwd=wt)[1][:30000]
            rev = self._revisar_grupo(c, incl, diff, [], "lote:" + ",".join(str(x["id"]) for x in incl) + "@" + sha[:10], ci="aun no ejecutado: aprobacion PRELIMINAR del contenido; el CI y la revision final llegan despues")
            if rev is None: self.out("  lote: revision de Claude no disponible, se reintenta"); return
            malos = set(rev.get("excluir_ids") or []) & {x["id"] for x in incl}
            for row in incl:
                if row["id"] in malos: self._marca(c, row, "rechazada_revision", "excluida del lote por la revision de Claude: " + "; ".join(rev.get("motivos") or [])[:600])
            if malos: self.out(f"  lote: Claude excluye {sorted(malos)}; se reagrupa en el siguiente ciclo"); return
            self.gh.push(sha, rama)
            cuerpo = f"## Lote de {len(incl)} correcciones verificadas por GPT QA\n\nCada una fue reproducida en main (el test falla antes), corregida (pasa despues), verificada con los comprobadores del repo y revisada de forma agregada por Claude antes de abrir esta PR. Se agrupan para ejecutar el CI pesado una sola vez.\n"
            for i, row in enumerate(incl, 1):
                cuerpo += f"\n---\n### {i}. {row['causa_raiz'][:100]}\n" + cuerpo_pr(row, P._rutas_tests(c, json.loads(row["propuestas"] or "[]")), row["pr_detalle"] or "").replace("\n## ", "\n#### ")
            cuerpo += "\n\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n"
            url = self.gh.pr_crear(rama, f"fix(qa-gpt): lote de {len(incl)} correcciones verificadas", cuerpo, borrador=False)
            m = re.search(r"/pull/(\d+)", url or ""); num = int(m.group(1)) if m else 0
            for row in incl:
                integ = "preliminar"  # nunca fusionable: tras el CI verde `revisar` emite la revision final sobre el SHA
                c.execute("UPDATE triaje SET pr_estado='pr_abierta',pr_url=?,pr_numero=?,pr_nueva=1,pr_head=?,dev_estado='pr_abierta',integracion=?,revision=?,revision_hash=NULL,actualizado=? WHERE id=?", (url, num, sha, integ, json.dumps(rev, ensure_ascii=False), self.q.now(), row["id"]))
            c.commit(); r["lote_pr"] = num; r["lote_correcciones"] = len(incl); self.out(f"  lote: PR #{num} con {len(incl)} correcciones")
        except Interrumpido:
            self.out("  lote interrumpido por parada: se repite al reanudar")
        finally:
            P.limpiar(wt, None)

    def revisar(self, c, row, head):
        grupo = c.execute("SELECT * FROM triaje WHERE pr_numero=? AND pr_nueva=1 ORDER BY id", (row["pr_numero"],)).fetchall() or [row]
        try: diff = self.gh.pr_diff(row["pr_numero"])[:30000]
        except Exception as e: self.out(f"  revision omitida (diff no disponible: {str(e)[:80]})"); return None
        mios = {m for m in re.findall(r"^diff --git a/(\S+)", diff, re.M)}
        solapes = sorted({p["number"] for p in getattr(self, "_prs", []) if p["number"] != row["pr_numero"] and mios & {f["path"] for f in p.get("files", [])}})[:10]
        rev = self._revisar_grupo(c, grupo, diff, solapes, f"revision:{row['id']}@{head}")
        if rev is None: return None
        c.execute("UPDATE triaje SET revision=?,revision_hash=?,pr_head=?,actualizado=? WHERE pr_numero=? AND pr_nueva=1", (json.dumps(rev, ensure_ascii=False), head, head, self.q.now(), row["pr_numero"])); c.commit()
        self.out(f"  Claude revisa PR #{row['pr_numero']}: {rev['veredicto']} (riesgo {rev['riesgo']})")
        return rev

    def _revisar_grupo(self, c, grupo, diff, solapes, clave, ci="verde"):
        import qa_claude, qa_triaje
        row = grupo[0]; d = qa_triaje._j(row["decision_json"], {}) or {}
        crit = d.get("criterio_aceptacion") if len(grupo) == 1 else [f"[{g['id']}] {(qa_triaje._j(g['decision_json'], {}) or {}).get('criterio_aceptacion')}" for g in grupo]
        causa = row["causa_raiz"] if len(grupo) == 1 else [f"[{g['id']}] {g['causa_raiz']}" for g in grupo]
        entrada = json.dumps({"causa": causa, "criterio_aceptacion": crit, "ci": ci, "prioridad": d.get("prioridad"),
                              "solapa_con_prs_abiertas": solapes, "diff": diff}, ensure_ascii=False)
        try: rev, _ = qa_claude.llamar(self.q, c, clave, "revision", SISTEMA_REVISION, entrada, ESQUEMA_REVISION)
        except qa_claude.ClaudeError as e: self.out(f"  Claude revision: {str(e)[:120]}"); return None
        return rev

    def _integrar(self, c, row, head, v, cfg):
        """Solo en modo 'auto' (calibracion_min opcional) y con GitHub en CLEAN: merge atado al commit revisado. Si la rama va por detras de main se actualiza y el siguiente ciclo la revalida."""
        ig = cfg["integracion"]
        if ig["modo"] != "auto": return
        aciertos = c.execute("SELECT COUNT(*) FROM triaje WHERE integracion='integrada_acierto'").fetchone()[0]
        if aciertos < ig["calibracion_min"]: return
        if v.get("mergeStateStatus") == "BEHIND":
            try: self.gh.pr_actualizar(row["pr_numero"]); self.out(f"  PR #{row['pr_numero']} actualizada con main; se revalida")
            except Exception as e: self.out(f"  PR #{row['pr_numero']}: no se pudo actualizar ({str(e)[-100:]})")
            return
        if v.get("mergeStateStatus") not in ("CLEAN", "UNSTABLE"): return  # UNSTABLE = solo fallan/pendientes checks no requeridos (el ci ya filtro rojos)
        self.gh.pr_merge(row["pr_numero"], head)
        c.execute("UPDATE triaje SET pr_estado='integrada',integracion='integrada_auto' WHERE pr_numero=? AND pr_nueva=1", (row["pr_numero"],)); c.commit()
        self.out(f"  PR #{row['pr_numero']} integrada por el sistema")
