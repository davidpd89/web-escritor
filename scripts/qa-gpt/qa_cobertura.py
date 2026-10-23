"""Modelo de cobertura dinamico de qa-gpt: familias de rutas <-> tests <-> tecnicas, tecnicas descubribles y dedup conductual.

Todo se recalcula desde el repo (git ls-files) y se persiste en SQLite; nada esta fijado a una lista cerrada:
las tecnicas semilla viven en config.json y GPT puede anadir nuevas (tabla `tecnicas`, origen 'descubierta').
"""
import hashlib, json, re, subprocess, unicodedata
from pathlib import Path

NO_FAMILIA = {"tests", "qa", ".github", "node_modules", "pagefind", "docs", "migrations", "video-ios-test", "artifacts", "_reddit", "_tools", "WEB DAVID PORTO nuevas ideas"}
TRAZAS = {  # rasgo de una familia -> extensiones
    "html": {".html"}, "js": {".js", ".mjs"}, "css": {".css"}, "datos": {".json", ".ics", ".xml", ".csv", ".txt"},
    "generador": {".py"}, "media": {".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg", ".mp4", ".pdf"},
}
GLOBAL_RE = re.compile(r"(rglob|glob\(|os\.walk|readdirSync|walk\(|\*\.html|\*\*/\*)")
STOP = set("para como este esta esos esas desde entre sobre cuando donde debe deben tiene tienen pero solo mismo todos todas test tests prueba".split())


def _git(root, *a):
    r = subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout.strip()


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9_]{4,}", norm(s)) if w not in STOP}


def migrar(c):
    """Esquema ampliado (idempotente). `c` ya tiene las tablas base."""
    def cols(t): return {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
    def add(t, col, ddl):
        if col not in cols(t): c.execute(f"ALTER TABLE {t} ADD COLUMN {col} {ddl}")
    for col, ddl in (("chat_id", "TEXT"), ("fase", "TEXT"), ("respuesta", "TEXT"), ("modo", "TEXT")): add("jobs", col, ddl)
    for col, ddl in (("tecnica", "TEXT"), ("funcionalidad", "TEXT"), ("huella_conductual", "TEXT"), ("fuente_sha", "TEXT"), ("familias", "TEXT"), ("duplica", "INTEGER"), ("siguiente", "TEXT"), ("base_sha", "TEXT"), ("version_test", "TEXT")): add("propuestas", col, ddl)
    for col, ddl in (("base_sha", "TEXT"), ("comandos", "TEXT")): add("ramas", col, ddl)
    for col, ddl in (("chat_id", "TEXT"), ("herramientas", "INTEGER"), ("estado", "TEXT"), ("segundos", "INTEGER")): add("peticiones", col, ddl)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS tecnicas(id TEXT PRIMARY KEY, nombre TEXT, kw TEXT, aplica TEXT, origen TEXT, creada TEXT, nota TEXT);
    CREATE TABLE IF NOT EXISTS cobertura(familia TEXT PRIMARY KEY, datos TEXT, head TEXT, actualizado TEXT);
    CREATE TABLE IF NOT EXISTS eventos(fecha TEXT, entidad TEXT, ident INTEGER, estado TEXT, nota TEXT);
    CREATE TABLE IF NOT EXISTS cruces(propuesta INTEGER, familia TEXT, tecnica TEXT, estado TEXT DEFAULT 'pendiente', UNIQUE(propuesta, familia));
    """)
    c.commit()


def sembrar_tecnicas(c, cfg, now):
    """Semilla = tipos + tecnicas_semilla de config; nunca borra las descubiertas."""
    for t in cfg["tipos"]:
        c.execute("INSERT OR IGNORE INTO tecnicas VALUES(?,?,?,?,?,?,?)", (t["id"], t["nombre"], json.dumps(t["kw"]), json.dumps(t.get("aplica", ["html", "js", "datos", "generador"])), "semilla", now, ""))
    for t in cfg.get("tecnicas_semilla", []):
        c.execute("INSERT OR IGNORE INTO tecnicas VALUES(?,?,?,?,?,?,?)", (t["id"], t["nombre"], json.dumps(t["kw"]), json.dumps(t.get("aplica", ["*"])), "semilla", now, ""))
    c.commit()


def registrar_tecnica(c, t, now, propuesta=None):
    """Registra una tecnica descubierta por GPT (id kebab-case). Devuelve True si es nueva."""
    tid = re.sub(r"[^a-z0-9]+", "-", norm(t.get("id") or t.get("nombre") or "")).strip("-")[:48]
    if not tid or c.execute("SELECT 1 FROM tecnicas WHERE id=?", (tid,)).fetchone(): return False
    kw = t.get("palabras_clave") or sorted(tokens(t.get("nombre", "")))[:5]
    c.execute("INSERT INTO tecnicas VALUES(?,?,?,?,?,?,?)", (tid, (t.get("nombre") or tid)[:160], json.dumps(kw), json.dumps(t.get("aplica") or ["*"]), "descubierta", now, f"propuesta {propuesta}" if propuesta else ""))
    c.commit(); return True


def tecnicas(c):
    return [dict(id=r["id"], nombre=r["nombre"], kw=[k.lower() for k in json.loads(r["kw"])], aplica=json.loads(r["aplica"]), origen=r["origen"]) for r in c.execute("SELECT * FROM tecnicas")]


def evento(c, entidad, ident, estado, nota, now):
    c.execute("INSERT INTO eventos VALUES(?,?,?,?,?)", (now, entidad, ident, estado, (nota or "")[:300]))


# ---------- inventario ----------
def familias_de(root):
    out = {}
    for p in _git(root, "ls-files").splitlines():
        p = p.strip('"')
        top = p.split("/")[0] if "/" in p else "(raiz)"
        if top in NO_FAMILIA or top.startswith("."): continue
        out.setdefault(top, []).append(p)
    return out


def rasgos(files):
    exts = {Path(f).suffix.lower() for f in files}
    return sorted(r for r, e in TRAZAS.items() if exts & e)


def aplica(t, rs):
    return "*" in t["aplica"] or bool(set(t["aplica"]) & set(rs))


def construir(c, root, cfg, now, forzar=False):
    """Recalcula la matriz si cambio HEAD (o forzar). Devuelve {familia: datos}."""
    head = _git(root, "rev-parse", "--short", "HEAD")
    if not forzar and c.execute("SELECT COUNT(*) FROM cobertura WHERE head=?", (head,)).fetchone()[0]:
        return {r["familia"]: json.loads(r["datos"]) for r in c.execute("SELECT * FROM cobertura")}
    fams, tecs = familias_de(root), tecnicas(c)
    pool = [p for p in _git(root, "ls-files", "tests", "qa", ".github/workflows").splitlines() if not p.endswith((".png", ".jpg", ".json.snap"))]
    info = {}
    for p in pool:
        try: txt = (root / p).read_text(encoding="utf-8", errors="replace")[:60000]
        except OSError: continue
        base = norm(Path(p).name + " " + txt[:20000])
        info[p] = (txt, {t["id"] for t in tecs if any(k in base for k in t["kw"])}, bool(GLOBAL_RE.search(txt)))
    areas = {a["id"]: a for a in cfg["areas"]}
    out = {}
    for fam, files in fams.items():
        rs = rasgos(files); pref = fam + "/"
        refs = [p for p, (txt, _, g) in info.items() if (pref in txt) or (fam == "(raiz)" and "index.html" in txt)]
        glob_t = [p for p, (_, _, g) in info.items() if g and p not in refs]
        cubiertas = {tid for p in refs for tid in info[p][1]}
        cub_glob = {tid for p in glob_t for tid in info[p][1]}
        apl = [t["id"] for t in tecs if aplica(t, rs)]
        huecos = [tid for tid in apl if tid not in cubiertas and tid not in cub_glob]
        parcial = [tid for tid in apl if tid not in cubiertas and tid in cub_glob]
        sha = _git(root, "log", "-1", "--format=%h", "--", fam if fam != "(raiz)" else ":(top,glob)*.html") or ""
        com = _git(root, "rev-list", "--count", "--since=14 days ago", "HEAD", "--", fam if fam != "(raiz)" else ":(top,glob)*.html") or "0"
        riesgo = max((a["riesgo"] for a in areas.values() if any(fam in f.split("/")[0] or f.startswith(fam) for f in a["fuentes"])), default=2)
        out[fam] = dict(familia=fam, ficheros=len(files), rasgos=rs, tests_propios=len(refs), tests_globales=len(glob_t), tecnicas_cubiertas=sorted(cubiertas),
                        tecnicas_parcial=parcial, tecnicas_aplicables=apl, huecos=huecos, sha=sha, commits14d=int(com or 0), riesgo=riesgo, ejemplos_tests=refs[:6])
    c.execute("DELETE FROM cobertura")
    for fam, d in out.items(): c.execute("INSERT INTO cobertura VALUES(?,?,?,?)", (fam, json.dumps(d, ensure_ascii=False), head, now))
    c.commit(); return out


# ---------- deduplicacion conductual ----------
def sha_fuentes(root, rutas):
    ex = [r for r in rutas if r and (root / r).exists()]
    return _git(root, "log", "-1", "--format=%h", "--", *ex) if ex else ""


def datos_prop(pr):
    fuentes = sorted({f.get("ruta", "") for f in pr.get("ficheros_fuente", []) if isinstance(f, dict) and f.get("ruta")})
    tec = (pr.get("tecnica") or {}); tec = tec.get("id") if isinstance(tec, dict) else str(tec or "")
    tec = re.sub(r"[^a-z0-9]+", "-", norm(tec)).strip("-") or "sin-tecnica"
    func = pr.get("funcionalidad") or pr.get("comportamiento") or pr.get("titulo", "")
    inv = pr.get("invariante") or pr.get("resultado_esperado") or ""
    toks = tokens(func + " " + inv)
    huella = hashlib.sha1(("|".join(sorted(toks)[:40]) + "#" + tec + "#" + ",".join(fuentes)).encode()).hexdigest()[:16]
    return dict(fuentes=fuentes, tecnica=tec, funcionalidad=func[:300], toks=toks, huella=huella)


def buscar_duplicado(c, root, pr):
    """-> (fila_previa, motivo) o (None, None). Rechazadas/invalidas se reabren SOLO si las fuentes cambiaron desde entonces."""
    d = datos_prop(pr)
    for r in c.execute("SELECT * FROM propuestas WHERE huella_conductual IS NOT NULL ORDER BY id"):
        prev = json.loads(r["datos"]); pd = datos_prop(prev)
        exacta = r["huella_conductual"] == d["huella"]
        sol = set(pd["fuentes"]) & set(d["fuentes"])
        jac = len(pd["toks"] & d["toks"]) / max(1, len(pd["toks"] | d["toks"]))
        if not (exacta or (pd["tecnica"] == d["tecnica"] and (sol or not d["fuentes"]) and jac >= 0.55)): continue
        if r["estado"] in ("rechazada", "invalida") and r["fuente_sha"] and sha_fuentes(root, pd["fuentes"]) != r["fuente_sha"]:
            continue  # el codigo cambio: se puede volver a mirar
        return r, f"{'huella igual' if exacta else f'similitud {jac:.2f}'} con #{r['id']} [{r['estado']}]"
    return None, None
