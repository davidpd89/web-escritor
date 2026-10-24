"""PR automaticas a partir del analisis GPT. Todo lo que devuelve GPT es una PROPUESTA: aqui se valida y solo se aplica en un worktree
aislado creado desde origin/main. Nunca toca main, nunca fusiona ni activa auto-merge, nunca ejecuta comandos que haya escrito GPT.
La PR se abre en borrador salvo que el test que descubrio el fallo pase tras el parche Y el que ya pasaba siga pasando."""
import json, os, re, shutil
from pathlib import Path

MAX_FICHEROS = 5
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
    a = json.loads(row["analisis"] or "{}")
    lista = lambda xs: "\n".join(f"- `{x}`" for x in xs) or "- (ninguno)"
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

    def candidatas(self, c):
        return c.execute("""SELECT * FROM triaje WHERE parche IS NOT NULL AND clase IN ('defecto_web','test_roto')
          AND COALESCE(pr_estado,'') IN ('','reintentar') ORDER BY id""").fetchall()

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
        norm = json.loads(row["parche"])
        wt = Path(self.q.STATE) / "pr" / rama.replace("/", "_")
        try:
            rc, o = self.git("fetch", "origin", "main", timeout=180)
            if rc: self._marca(c, row, "reintentar", f"fetch fallo: {o[-200:]}"); return "reintentar"
            if wt.exists(): self.limpiar(wt, rama)
            wt.parent.mkdir(parents=True, exist_ok=True)
            rc, o = self.git("worktree", "add", "-B", rama, str(wt), "origin/main")
            if rc: self._marca(c, row, "reintentar", f"worktree fallo: {o[-200:]}"); return "reintentar"
            try: tocados = aplicar_parche(wt, norm)
            except ValueError as e: self._marca(c, row, "parche_no_encaja", str(e)); return "parche_no_encaja"
            tests = self._rutas_tests(c, json.loads(row["propuestas"] or "[]"))
            verif, verde = self._verificar(wt, tests, tocados)
            if not any((wt / t).exists() for t in tests) and tests:  # el test vive en la rama gpt-qa, no en main: se trae como regresion
                self._traer_tests(c, row, wt, tests)
                verif, verde = self._verificar(wt, tests, tocados)
            self.git("add", "-A", cwd=wt)
            if self.git("diff", "--cached", "--quiet", cwd=wt)[0] == 0: self._marca(c, row, "sin_cambios", "el parche no cambia nada"); return "sin_cambios"
            tit = ("[DEMO] " if demo else "") + f"fix(qa-gpt): {row['causa_raiz'][:70]}"
            rc, o = self.git("-c", "user.name=qa-gpt", "-c", "user.email=qa-gpt@users.noreply.github.com", "commit", "-q", "-m", tit + f"\n\nfirma {firma}", cwd=wt)
            if rc: self._marca(c, row, "reintentar", f"commit fallo: {o[-200:]}"); return "reintentar"
            if not push: self._marca(c, row, "listo_local", verif); return "listo_local"
            sha = self.git("rev-parse", "HEAD", cwd=wt)[1].strip()
            try: self.gh.push(sha, rama)
            except RuntimeError as e:
                if "rejected" in str(e) or "non-fast" in str(e): self._marca(c, row, "rama_existente", f"{rama} ya existe en origin con otro historial: revisar la PR existente"); return "rama_existente"
                raise
            url = self.gh.pr_crear(rama, tit, cuerpo_pr(row, tests, verif, demo), borrador=(not verde) or demo)
            self._marca(c, row, "pr_borrador" if (not verde or demo) else "pr_abierta", verif, url)
            return "pr_borrador" if (not verde or demo) else "pr_abierta"
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
        if not tests: return "Sin test automatico asociado: PR en borrador.", False
        res, verde = [], True
        for t in tests:
            cmd = self.comando_test(t)
            if not cmd or not (wt / t).exists(): res.append(f"- `{t}`: no ejecutable aqui"); verde = False; continue
            rc, o = self.run(cmd, str(wt), timeout=240)
            res.append(f"- `{t}`: {'PASA' if rc == 0 else 'FALLA'} (exit {rc})"); verde = verde and rc == 0
        return "Tests tras el parche:\n" + "\n".join(res), verde

    def limpiar(self, wt, rama):
        if Path(wt).exists():
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
