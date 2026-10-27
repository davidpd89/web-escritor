"""parches: validacion y aplicacion de lo que GPT propone (parche buscar/por, ficheros nuevos, tests de aceptacion, codigo externo) y construccion
de la rama candidata en un WORKTREE separado derivado de origin/<rama_base>. Nada de lo que devuelve GPT se ejecuta como comando: solo se
valida y se escribe en el worktree; los tests se ejecutan con `python|node <ruta>` y la ruta la fija este modulo.

PROCEDENCIA: scripts/qa-gpt/qa_pr.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, blob aaa0a0404a8ef058c1c28543bc44f918d043c995:
`ruta_segura`, `validar_parche` y `aplicar_parche` son la logica del QA (sustituciones EXACTAS de un fragmento unico), con estos CAMBIOS:
- limites desde config.json ("parches"); PROHIBIDAS amplia con experimentos/ y con los workflows (el laboratorio no edita CI);
- `validar_parche` acepta ademas `ficheros_nuevos` (el QA solo editaba ficheros existentes) con tope de tamano, extension y escaneo de secretos;
- NO se copia nada de qa_pr.py que cree PR contra main, fusione, cierre/borre ramas ni relance workflows (Pr.preparar, Ciclo, _integrar*, _freno_main...).
"""
import json, os, re, shutil
from pathlib import Path

import mw
import verificar_upstream

PROHIBIDAS = re.compile(r"(^|/)(\.github|\.git|node_modules|scripts/qa-gpt|experimentos|\.ci)(/|$)|(^|/)(package(-lock)?\.json|wrangler[\w.-]*|\.env[\w.]*|\.dev\.vars)$"
                        r"|stripe|paypal|payment|(^|[/_.-])pagos?([/_.-]|$)|secret|credential|cloudflare", re.I)
SECRETO = re.compile(r"sk_(live|test)_\w+|AKIA[0-9A-Z]{12,}|ghp_\w{20,}|(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}", re.I)
EXT_NUEVOS = {".html", ".css", ".js", ".mjs", ".json", ".md", ".svg", ".txt", ".xml", ".webmanifest"}
EXT_TESTS = {".py": "python", ".mjs": "node", ".js": "node"}


def lim(nombre, defecto=None):
    return mw.CFG.get("parches", {}).get(nombre, defecto)


def ruta_segura(ruta):
    """None si la ruta es admisible; si no, el motivo. (Logica del QA; amplia PROHIBIDAS.)"""
    if not isinstance(ruta, str) or not ruta or ruta.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", ruta): return "ruta no relativa"
    partes = ruta.replace("\\", "/").split("/")
    if ".." in partes or "" in partes: return "ruta con .. o vacia"
    if PROHIBIDAS.search(ruta.replace("\\", "/")): return "ruta sensible (workflows, credenciales, pagos, configuracion o laboratorio)"
    return None


def es_ruta_test(ruta):
    return isinstance(ruta, str) and ruta.startswith(lim("dir_tests", "tests/mejoras-web/")) and Path(ruta).suffix in EXT_TESTS and ruta_segura(ruta) is None


def validar_parche(parche, leer):
    """-> (ok, problemas, normalizado). `leer(ruta)` devuelve el texto actual del fichero o None. No escribe nada.
    parche = {"ficheros":[{"ruta","reemplazos":[{"buscar","por"}]}], "ficheros_nuevos":[{"ruta","contenido"}]}"""
    problemas, norm = [], {"ficheros": [], "ficheros_nuevos": []}
    if not isinstance(parche, dict): return False, ["parche no es un objeto"], None
    fich, nuevos = parche.get("ficheros") or [], parche.get("ficheros_nuevos") or []
    if not isinstance(fich, list) or not isinstance(nuevos, list) or not (fich or nuevos): return False, ["parche sin ficheros"], None
    if len(fich) > lim("max_ficheros", 6) or len(nuevos) > lim("max_ficheros_nuevos", 4): return False, ["demasiados ficheros"], None
    vistos = set()
    for f in fich:
        ruta = f.get("ruta") if isinstance(f, dict) else None
        if (m := ruta_segura(ruta)): problemas.append(f"{ruta}: {m}"); continue
        if ruta in vistos: problemas.append(f"{ruta}: repetido"); continue
        vistos.add(ruta)
        texto = leer(ruta)
        if texto is None: problemas.append(f"{ruta}: no existe en la rama base"); continue
        reps = f.get("reemplazos")
        if not isinstance(reps, list) or not reps or len(reps) > lim("max_reemplazos", 8): problemas.append(f"{ruta}: reemplazos invalidos"); continue
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
    for f in nuevos:
        ruta = f.get("ruta") if isinstance(f, dict) else None
        cont = f.get("contenido") if isinstance(f, dict) else None
        if (m := ruta_segura(ruta)): problemas.append(f"{ruta}: {m}"); continue
        if ruta in vistos: problemas.append(f"{ruta}: repetido"); continue
        vistos.add(ruta)
        if es_ruta_test(ruta): problemas.append(f"{ruta}: los tests van en el campo `pruebas`, no en ficheros_nuevos"); continue
        if Path(ruta).suffix not in EXT_NUEVOS: problemas.append(f"{ruta}: extension no admitida para un fichero nuevo"); continue
        if leer(ruta) is not None: problemas.append(f"{ruta}: ya existe (usa reemplazos)"); continue
        if not isinstance(cont, str) or not cont.strip(): problemas.append(f"{ruta}: contenido vacio"); continue
        if len(cont.encode("utf-8")) > lim("max_bytes_nuevo", 60000): problemas.append(f"{ruta}: supera {lim('max_bytes_nuevo', 60000)} bytes"); continue
        if SECRETO.search(cont): problemas.append(f"{ruta}: parece contener un secreto"); continue
        norm["ficheros_nuevos"].append({"ruta": ruta, "contenido": cont})
    return (not problemas), problemas, (norm if not problemas else None)


def validar_pruebas(pruebas):
    """Tests de aceptacion NUEVOS bajo tests/mejoras-web/. -> (ok, problemas, normalizado[{ruta, contenido, exe}])."""
    if not isinstance(pruebas, list) or not pruebas: return False, ["la mejora necesita al menos un test de aceptacion"], None
    if len(pruebas) > lim("max_tests", 3): return False, [f"mas de {lim('max_tests', 3)} tests"], None
    problemas, out, vistos = [], [], set()
    for t in pruebas:
        ruta = t.get("ruta") if isinstance(t, dict) else None
        cont = t.get("contenido") if isinstance(t, dict) else None
        if not es_ruta_test(ruta): problemas.append(f"{ruta}: el test debe ser .py/.mjs/.js bajo {lim('dir_tests', 'tests/mejoras-web/')}"); continue
        if ruta in vistos: problemas.append(f"{ruta}: repetido"); continue
        vistos.add(ruta)
        if not isinstance(cont, str) or len(cont.strip()) < 40: problemas.append(f"{ruta}: test vacio o trivial"); continue
        if len(cont.encode("utf-8")) > lim("max_bytes_nuevo", 60000): problemas.append(f"{ruta}: test demasiado grande"); continue
        if SECRETO.search(cont): problemas.append(f"{ruta}: parece contener un secreto"); continue
        if not re.search(r"assert|expect|throw new Error|sys\.exit\(1\)|raise\s+AssertionError|process\.exit\(1\)", cont): problemas.append(f"{ruta}: el test no comprueba nada (sin aserciones)"); continue
        if ruta.endswith(".py"):
            try: compile(cont, ruta, "exec")
            except SyntaxError as e: problemas.append(f"{ruta}: SyntaxError {e.msg} (linea {e.lineno})"); continue
        out.append({"ruta": ruta, "contenido": cont, "exe": EXT_TESTS[Path(ruta).suffix]})
    return (not problemas), problemas, (out if not problemas else None)


def validar_propuesta(data, leer):
    """Respuesta de desarrollo de GPT -> (ok, problemas, propuesta normalizada). No escribe nada."""
    ok1, pr1, norm = validar_parche(data.get("parche"), leer)
    ok2, pr2, tests = validar_pruebas(data.get("pruebas"))
    problemas = pr1 + pr2
    if not ok1 or not ok2: return False, problemas, None
    tocados = [f["ruta"] for f in norm["ficheros"]] + [f["ruta"] for f in norm["ficheros_nuevos"]]
    return True, [], {"parche": norm, "pruebas": tests, "tocados": tocados, "codigo_externo": data.get("codigo_externo") or [],
                      "resumen": str(data.get("explicacion") or "")[:600], "confianza": data.get("confianza")}


def verificar_procedencia(externo, textos_nuevos, fetch=None):
    """Cada `codigo_externo` exige: url del repo, commit_upstream (40 hex), ruta_upstream, fuente_sha (blob, 40 hex), codigo_original literal,
    licencia SPDX. verificar_upstream lo comprueba contra GitHub REST (contenido en ese commit y licencia real). Ademas el literal debe aparecer en
    el parche (o declararse `adaptado` con descripcion). -> (ok, problemas, registros). `fetch` inyectable (pruebas)."""
    problemas, registros = [], []
    for i, e in enumerate(externo or []):
        if not isinstance(e, dict): problemas.append(f"codigo_externo[{i}] no es un objeto"); continue
        inv = {"fuente_sha": e.get("fuente_sha", ""), "codigo_original": e.get("codigo_original", ""), "licencia": e.get("licencia", ""),
               "commit_upstream": e.get("commit_upstream", ""), "ruta_upstream": e.get("ruta_upstream", "")}
        try: reg = verificar_upstream.verificar(inv, {"url": e.get("url", "")}, fetch)
        except verificar_upstream.FuenteNoVerificada as exc: problemas.append(f"codigo_externo[{i}] {e.get('url', '?')}: {exc}"); continue
        if not reg.get("upstream_verificado"): problemas.append(f"codigo_externo[{i}]: la fuente no es un repositorio verificable"); continue
        literal = e["codigo_original"].strip()
        if not any(literal in t for t in textos_nuevos) and not (e.get("adaptado") and len(str(e.get("adaptacion", ""))) >= 20):
            problemas.append(f"codigo_externo[{i}]: el codigo literal no aparece en el parche y no se declara `adaptado` con `adaptacion`")
            continue
        registros.append({**reg, "adaptado": bool(e.get("adaptado")), "adaptacion": str(e.get("adaptacion", ""))[:300]})
    return (not problemas), problemas, registros


def textos_del_parche(prop):
    return [r["por"] for f in prop["parche"]["ficheros"] for r in f["reemplazos"]] + [f["contenido"] for f in prop["parche"]["ficheros_nuevos"]] + [t["contenido"] for t in prop["pruebas"]]


def aplicar(root, prop):
    """Escribe parche + tests en `root` (worktree). Vuelve a validar contra el disco; ValueError si no encaja. -> rutas tocadas."""
    root = Path(root)
    ok, problemas, norm = validar_parche(prop["parche"], lambda r: (root / r).read_text(encoding="utf-8") if (root / r).is_file() else None)
    if not ok: raise ValueError("; ".join(problemas))
    tocados = []
    for f in norm["ficheros"]:
        p = root / f["ruta"]; t = p.read_text(encoding="utf-8")
        for r in f["reemplazos"]: t = t.replace(r["buscar"], r["por"], 1)
        p.write_text(t, encoding="utf-8", newline=""); tocados.append(f["ruta"])
    for f in norm["ficheros_nuevos"] + prop["pruebas"]:
        if (root / f["ruta"]).exists(): raise ValueError(f"{f['ruta']}: ya existe")
        p = root / f["ruta"]; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["contenido"], encoding="utf-8", newline=""); tocados.append(f["ruta"])
    return tocados


# ---------- worktree candidato ----------
def wt_path(exp_id):
    return mw.STATE / "wt" / exp_id


def limpiar_wt(wt):
    wt = Path(wt)
    if wt.exists():
        j = wt / "node_modules"
        if j.exists() or j.is_symlink():
            try: os.rmdir(j)  # quita solo el junction/enlace, nunca el contenido de node_modules
            except OSError:
                try: j.unlink()
                except OSError: pass
        mw.git("worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(wt, ignore_errors=True)
    mw.git("worktree", "prune", check=False)


def construir_candidata(exp):
    """Worktree `mejoras-web/<id>` desde origin/<rama_base> + parche + tests, un commit LOCAL (no se publica). -> (wt, sha, base_sha, tocados).
    Falla con ValueError si el parche no encaja o el commit toca algo que no estaba declarado."""
    prop = json.loads(exp["parche"])
    rama = exp["rama"] or mw.CFG["prefijo_rama"] + exp["id"].lower()
    if not mw.rama_permitida(rama): raise ValueError(f"rama no permitida: {rama}")
    base = mw.git("rev-parse", mw.fuente_ref())
    wt = wt_path(exp["id"]); limpiar_wt(wt)
    wt.parent.mkdir(parents=True, exist_ok=True)
    mw.git("worktree", "add", "-B", rama, str(wt), base)
    try:
        tocados = aplicar(wt, prop)
        mw.git("add", "-A", "--", *tocados, cwd=wt)
        mw.git("-c", "user.name=mejoras-web", "-c", "user.email=mejoras-web@users.noreply.github.com", "commit", "-q", "-m",
               f"mejoras-web {exp['id']}: {exp['titulo'][:90]}\n\nExpediente {exp['id']} ({exp['area']}). Candidata validada en local; sin publicar.", cwd=wt)
        sha = mw.git("rev-parse", "HEAD", cwd=wt)
        reales = set(mw.git("diff", "--name-only", f"{base}..{sha}", cwd=wt).split())
        if reales != set(tocados): raise ValueError(f"el commit toca ficheros no declarados: {sorted(reales ^ set(tocados))[:4]}")
        return wt, sha, base, tocados
    except Exception:
        limpiar_wt(wt)
        mw.git("branch", "-D", rama, check=False)
        raise
