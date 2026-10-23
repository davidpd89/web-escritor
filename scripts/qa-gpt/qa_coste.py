"""qa_coste: estimacion del coste en GitHub Actions del lote pendiente (solo lectura: `git show` y `gh run list / api`).

No inventa duraciones: usa los runs reales anteriores de cada workflow (mediana de hasta 5 ejecuciones correctas). Distingue
reloj (startedAt->updatedAt), facturable (suma de minutos de cada job redondeados hacia arriba, como cobra GitHub) y cola (createdAt->startedAt).
"""
import json, re, statistics, subprocess
from pathlib import Path
import qa_lote as L


def jobs_de(texto):
    """Nombres de job de nivel superior (bajo `jobs:`)."""
    m = re.search(r"^jobs:\s*$", texto, re.M)
    if not m: return []
    out = []
    for linea in texto[m.end():].splitlines():
        if linea and not linea.startswith((" ", "\t", "#")): break
        k = re.match(r"^  ([\w-]+):\s*$", linea)
        if k: out.append(k.group(1))
    return out


def _gh(*a):
    r = subprocess.run(["gh", *a], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if r.returncode: raise RuntimeError((r.stderr or r.stdout)[:200])
    return json.loads(r.stdout or "null")


def _seg(a, b):
    from datetime import datetime as D
    try: return max(0, (D.fromisoformat(b.replace("Z", "+00:00")) - D.fromisoformat(a.replace("Z", "+00:00"))).total_seconds())
    except Exception: return None


def historial(repo, wf):
    """-> dict(n, reloj_s, cola_s, facturable_min) con medianas, o None si no hay runs correctos."""
    runs = _gh("run", "list", "-R", repo, "--workflow", wf, "--status", "success", "--limit", "5", "--json", "databaseId,createdAt,startedAt,updatedAt")
    if not runs: return None
    cola = [x for x in (_seg(r["createdAt"], r["startedAt"]) for r in runs) if x is not None]
    reloj, fact = [], []
    for r in runs[:3]:  # reloj y facturable salen de los jobs reales (run.updatedAt incluye eventos posteriores al ultimo job)
        try:
            js = [j for j in _gh("api", f"repos/{repo}/actions/runs/{r['databaseId']}/jobs", "--jq", "[.jobs[]|{s:.started_at,c:.completed_at}]") if j["s"] and j["c"]]
            if js: reloj.append(_seg(min(j["s"] for j in js), max(j["c"] for j in js))); fact.append(sum(-(-(_seg(j["s"], j["c"]) or 0) // 60) for j in js))
        except RuntimeError: pass
    if not reloj: reloj = [x for x in (_seg(r["startedAt"], r["updatedAt"]) for r in runs) if x is not None]
    med = lambda v: statistics.median(v) if v else None
    return {"n": len(runs), "reloj_s": med(reloj), "cola_s": med(cola), "facturable_min": med(fact)}


def estimar(q, ramas=None, hist=historial):
    """Una fila por rama pendiente: test, workflow, jobs, historial, estado. Los defectos/fallos locales ya conocidos no gastan Actions."""
    c = q.db(); filas, cache = [], {}
    for r in c.execute("SELECT * FROM ramas WHERE estado IN ('preparada','aprobada','publicada') ORDER BY rama"):
        if ramas and r["rama"] not in ramas: continue
        pend = c.execute("SELECT id,datos FROM propuestas WHERE rama=? AND estado IN ('preparada','aprobada')", (r["rama"],)).fetchall()
        if not pend: continue
        rutas, pref = [], set()
        for p in pend:
            d = json.loads(p["datos"]); pref.add(Path(d.get("workflow") or "").name)
            rutas += [x["ruta"] for x in d.get("ficheros_nuevos", []) if Path(x["ruta"]).suffix in (".py", ".mjs", ".js")]
        mods = {}
        for p in pend:
            for m in json.loads(p["datos"]).get("ficheros_modificados") or []:
                if m["ruta"].startswith(".github/workflows/"): mods[Path(m["ruta"]).name] = True
        nombres = q.git("ls-tree", "--name-only", r["sha"], ".github/workflows/", check=False).split()
        textos = {Path(n).name: q.git("show", f"{r['sha']}:{n}", check=False) for n in nombres if n.endswith(".yml")}
        # un test cableado por la propia rama (ficheros_modificados) cuenta aunque main aun no lo ejecute
        wf = L.workflows_que_ejecutan(rutas, textos, pref)
        fila = {"test": r["rama"].replace("gpt-qa/", ""), "propuestas": [p["id"] for p in pend], "workflow": wf[0] if wf else None, "toca_workflow": bool(mods)}
        if wf:
            fila["jobs"] = len(jobs_de(textos[wf[0]]))
            if wf[0] not in cache:
                try: cache[wf[0]] = hist(q.CFG["repo"], wf[0])
                except Exception as e: cache[wf[0]] = {"error": str(e)[:80]}
            fila["hist"] = cache[wf[0]]
        filas.append(fila)
    return filas


def tabla(filas, scopes=()):
    out = ["Test -> Workflow -> Jobs -> Reloj / Facturable / Cola (mediana de runs anteriores) -> Estado"]
    for f in filas:
        h = f.get("hist") or {}
        if not f["workflow"]: est = "SOLO LOCAL (ningun workflow lo ejecuta: revision humana)"; tiempos = "-"
        else:
            if "error" in h: tiempos = f"sin dato ({h['error']})"
            elif not h: tiempos = "sin historial de ejecuciones correctas: no se estima"
            else: tiempos = f"reloj ~{int(h['reloj_s'] // 60)}m{int(h['reloj_s'] % 60):02d}s / facturable ~{h['facturable_min']:.0f} min / cola ~{(h['cola_s'] or 0):.0f} s (n={h['n']})"
            est = "BLOQUEADO hasta `gh auth refresh -s workflow`" if f["toca_workflow"] and "workflow" not in scopes else "listo para Actions"
        out.append(f"  {f['test']} -> {f['workflow'] or '-'} -> {f.get('jobs', '-')} job(s) -> {tiempos} -> {est}")
    wfs = {f["workflow"] for f in filas if f["workflow"]}
    out.append(f"Resumen: {len(filas)} tests, {len([f for f in filas if f['workflow']])} aptos para Actions en {len(wfs)} workflow(s) distintos, {sum(f.get('jobs', 0) for f in filas)} jobs en total. "
               "Cada rama es un ref distinto: NO comparten ejecucion; el lote envia como maximo 2 a la vez (sin tormenta). Duraciones = datos reales anteriores, no garantia.")
    return "\n".join(out)


def main(q, a=None):
    scopes = L.Gh(q).scopes()
    print(tabla(estimar(q), scopes)); return 0
