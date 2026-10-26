"""qa_viaa: ejecutor persistente de la Via A (contratos masivos) dentro del mismo motor que los tests de la Via B.

- Estaticos: TODAS las paginas aplicables del sitemap (qa_contratos.ejecutar_sitio). Se reutiliza el resultado si no cambian ni el SHA del sitio ni los contratos.
- Navegador: muestra representativa por familia que ROTA en cada ejecucion hacia las paginas aun no comprobadas (la cobertura crece sin redisenar nada).
- Hallazgos: una fila por (tipo, contrato, causa, familia) con TODAS las paginas afectadas; estado a_triar hasta que alguien (o GPT sobre el grupo) lo clasifique.
"""
import hashlib, json, os, shutil, socket, subprocess, time
from pathlib import Path
from urllib.parse import urlparse

import qa_contratos
import qa_cobertura as cob

HERE = Path(__file__).parent
ESTADOS = ("a_triar", "defecto_demostrado", "falso_positivo", "duplicado", "infra", "resuelto")
NODE_MODULES = cob.NODE_MODULES


def migrar(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS viaa_runs(id INTEGER PRIMARY KEY, fecha TEXT, tipo TEXT, sha TEXT, version TEXT, paginas INTEGER, contratos INTEGER,
      aserciones INTEGER, brutos INTEGER, unicos INTEGER, segundos REAL, resultado TEXT);
    CREATE TABLE IF NOT EXISTS hallazgos(clave TEXT PRIMARY KEY, tipo TEXT, contrato TEXT, causa TEXT, familia TEXT, paginas INTEGER, urls TEXT, ejemplos TEXT,
      estado TEXT DEFAULT 'a_triar', nota TEXT, sha_primero TEXT, sha_ultimo TEXT, primera TEXT, ultima TEXT, comando TEXT, evidencia TEXT);
    CREATE TABLE IF NOT EXISTS viaa_cobertura(url TEXT PRIMARY KEY, familia TEXT, navegador TEXT, estatico TEXT);
    """)


def version_contratos():
    return hashlib.sha1((HERE / "qa_contratos.py").read_bytes() + (HERE / "contratos_browser.mjs").read_bytes()).hexdigest()[:10]


def registrar(c, q, tipo, res, hallazgos, sha, comando, commit=True):
    """Guarda la ejecucion y hace upsert de hallazgos. Los que dejan de reproducirse pasan a 'resuelto' salvo clasificacion humana."""
    ahora = q.now(); vistos = set()
    for h in hallazgos:
        clave = hashlib.sha1(f"{tipo}|{h['contrato']}|{h['causa']}|{h['familia']}".encode()).hexdigest()[:16]; vistos.add(clave)
        ev = f"{comando} | sha {sha[:8]} | {h['paginas']} paginas | ej: {h['ejemplos'][0] if h['ejemplos'] else ''}"
        ya = c.execute("SELECT estado FROM hallazgos WHERE clave=?", (clave,)).fetchone()
        if ya:
            est = "a_triar" if ya["estado"] == "resuelto" else ya["estado"]
            c.execute("UPDATE hallazgos SET paginas=?,urls=?,ejemplos=?,estado=?,sha_ultimo=?,ultima=?,evidencia=? WHERE clave=?",
                      (h["paginas"], json.dumps(h["urls"]), json.dumps(h["ejemplos"]), est, sha, ahora, ev, clave))
        else:
            c.execute("INSERT INTO hallazgos(clave,tipo,contrato,causa,familia,paginas,urls,ejemplos,estado,sha_primero,sha_ultimo,primera,ultima,comando,evidencia) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (clave, tipo, h["contrato"], h["causa"], h["familia"], h["paginas"], json.dumps(h["urls"]), json.dumps(h["ejemplos"]), "a_triar", sha, sha, ahora, ahora, comando, ev))
    if tipo == "estatico":  # solo el estatico recorre todo: lo que ya no falla queda resuelto (el de navegador es muestra rotatoria, no se cierra por ausencia)
        for r in c.execute("SELECT clave FROM hallazgos WHERE tipo=? AND estado='a_triar'", (tipo,)).fetchall():
            if r["clave"] not in vistos: c.execute("UPDATE hallazgos SET estado='resuelto',nota='ya no se reproduce' WHERE clave=?", (r["clave"],))
    c.execute("INSERT INTO viaa_runs(fecha,tipo,sha,version,paginas,contratos,aserciones,brutos,unicos,segundos,resultado) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
              (ahora, tipo, sha, version_contratos(), res["paginas"], res["contratos"], res["aserciones"], res["fallos_brutos"], res["fallos_unicos"], res["segundos"], json.dumps({"familias": res["familias"]})))
    if commit:
        c.commit()


def estatico(c, q, root, forzar=False, out=print):
    sha = q.git("rev-parse", "HEAD", cwd=root, check=False).strip() or "?"
    ult = c.execute("SELECT * FROM viaa_runs WHERE tipo='estatico' ORDER BY id DESC LIMIT 1").fetchone()
    if ult and not forzar and ult["sha"] == sha and ult["version"] == version_contratos():
        out(f"Via A estatica: resultado reutilizado (mismo SHA {sha[:8]} y contratos): {ult['paginas']} paginas, {ult['unicos']} hallazgos unicos"); return ult["unicos"]
    res = qa_contratos.ejecutar_sitio(root)
    try:
        registrar(c, q, "estatico", res, res["grupos"], sha, "qa_gpt.py contratos --completo", commit=False)
        for fam, rutas in qa_contratos.paginas_del_sitio(root).items():
            for r in rutas:
                c.execute("INSERT INTO viaa_cobertura(url,familia,estatico) VALUES(?,?,?) ON CONFLICT(url) DO UPDATE SET estatico=excluded.estatico",
                          (urlparse(qa_contratos.url_de(root, r)).path, fam, q.now()))
        c.commit()
    except Exception:
        c.rollback()
        raise
    out(f"Via A estatica: {res['contratos']} contratos x {res['paginas']} paginas = {res['aserciones']} aserciones en {res['segundos']} s -> {res['fallos_brutos']} fallos brutos -> {res['fallos_unicos']} hallazgos unicos"); return res["fallos_unicos"]


def _puerto():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def elegir_navegador(c, root, por_familia):
    """Por familia, primero las paginas que el navegador no ha visto nunca (la cobertura crece en cada clic)."""
    elegidas = []
    for fam, rutas in qa_contratos.paginas_del_sitio(root).items():
        urls = [urlparse(qa_contratos.url_de(root, r)).path for r in rutas]
        hechas = {r["url"]: r["navegador"] for r in c.execute("SELECT url,navegador FROM viaa_cobertura WHERE familia=?", (fam,)) if r["navegador"]}
        orden = sorted(urls, key=lambda u: (hechas.get(u) or "", u))  # nunca vistas primero, luego las mas antiguas
        elegidas += orden[: por_familia if fam != "generales" else por_familia * 3]
    return elegidas


def navegador(c, q, root, por_familia=8, out=print, timeout=900):
    node = shutil.which("node")
    if not node: out("Via A navegador: node no esta disponible"); return None
    lista = elegir_navegador(c, root, por_familia); sal = q.STATE / "auditoria"; sal.mkdir(parents=True, exist_ok=True)
    (sal / "urls-navegador.json").write_text(json.dumps(lista), encoding="utf-8")
    puerto = _puerto(); sha = q.git("rev-parse", "HEAD", cwd=root, check=False).strip() or "?"
    srv = cob.ServidorEstatico(root, puerto); srv.__enter__()  # hilo propio: no queda huerfano si EJECUTAR muere
    try:
        env = {**os.environ, "QA_NODE_MODULES": NODE_MODULES}; res_f = sal / "navegador-ultimo.json"; res_f.unlink(missing_ok=True)
        p = cob.run([node, str(HERE / "contratos_browser.mjs"), f"http://127.0.0.1:{puerto}", str(sal / "urls-navegador.json"), str(res_f)], env=env, capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0 or not res_f.exists(): out(f"Via A navegador: fallo de infraestructura: {(p.stderr or p.stdout)[-200:]}"); return None
    finally:
        srv.__exit__()

    try:
        d = json.loads(res_f.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            raise TypeError("resultado no es un objeto")
        if not isinstance(d["hallazgos"], list):
            raise TypeError("hallazgos no es una lista")
        if not isinstance(d["paginas"], int) or isinstance(d["paginas"], bool):
            raise TypeError("paginas no es un entero")
        if not isinstance(d["aserciones"], int) or isinstance(d["aserciones"], bool):
            raise TypeError("aserciones no es un entero")
        if not isinstance(d["segundos"], (int, float)) or isinstance(d["segundos"], bool):
            raise TypeError("segundos no es numerico")

        g = {}
        for h in d["hallazgos"]:
            if not isinstance(h, dict):
                raise TypeError("hallazgo no es un objeto")
            for campo in ("contrato", "causa", "url", "vista", "detalle"):
                if not isinstance(h[campo], str):
                    raise TypeError(f"{campo} no es texto")
            k = (h["contrato"], h["causa"], qa_contratos.familia_de("https://x" + h["url"]))
            e = g.setdefault(k, {"contrato": k[0], "causa": k[1], "familia": k[2], "urls": set(), "vistas": set(), "ejemplos": []})
            e["urls"].add(h["url"]); e["vistas"].add(h["vista"])
            if len(e["ejemplos"]) < 3: e["ejemplos"].append(f"{h['url']} [{h['vista']}] {h['detalle']}")
        grupos = [{**e, "urls": sorted(e["urls"]), "paginas": len(e["urls"]), "ejemplos": e["ejemplos"] + [f"vistas: {','.join(sorted(e['vistas']))}"]} for e in g.values()]
        for e in grupos: e.pop("vistas")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError, UnicodeError) as e:
        out(f"Via A navegador: fallo de infraestructura: resultado JSON invalido ({str(e)[:120]})")
        return None

    res = {"paginas": d["paginas"], "contratos": 11, "aserciones": d["aserciones"], "fallos_brutos": len(d["hallazgos"]), "fallos_unicos": len(grupos), "segundos": d["segundos"], "familias": {}}
    registrar(c, q, "navegador", res, grupos, sha, "node contratos_browser.mjs (3 vistas)")
    for u in lista: c.execute("INSERT INTO viaa_cobertura(url,familia,navegador) VALUES(?,?,?) ON CONFLICT(url) DO UPDATE SET navegador=excluded.navegador", (u, qa_contratos.familia_de("https://x" + u), q.now()))
    c.commit()
    out(f"Via A navegador: {d['paginas']} paginas x 3 vistas, {d['aserciones']} aserciones en {d['segundos']} s -> {len(d['hallazgos'])} fallos brutos -> {len(grupos)} hallazgos unicos"); return len(grupos)


def ejecutar(c, q, root, forzar=False, out=print, por_familia=8):
    migrar(c); r = {"estatico": estatico(c, q, root, forzar, out)}
    try: r["navegador"] = navegador(c, q, root, por_familia, out)
    except Exception as e: out(f"Via A navegador: fallo de infraestructura ({str(e)[:120]})"); r["navegador"] = None
    return r


def bloque_estado(q, c):
    try: c.execute("SELECT 1 FROM hallazgos LIMIT 1")
    except Exception: return ["", "Via A (contratos masivos): (aun sin ejecutar)"]
    n = lambda sql, *a: c.execute(sql, a).fetchone()[0]
    cov_e = n("SELECT COUNT(*) FROM viaa_cobertura WHERE estatico IS NOT NULL"); cov_b = n("SELECT COUNT(*) FROM viaa_cobertura WHERE navegador IS NOT NULL")
    L = ["", "Via A (contratos masivos; las aserciones NO son tests):",
         f"  - Paginas cubiertas: {cov_e} en estatico, {cov_b} en navegador | ejecuciones: {n('SELECT COUNT(*) FROM viaa_runs')}"]
    for t in ("estatico", "navegador"):
        u = c.execute("SELECT * FROM viaa_runs WHERE tipo=? ORDER BY id DESC LIMIT 1", (t,)).fetchone()
        if u: L.append(f"  - Ultimo {t}: {u['fecha']} | {u['contratos']} contratos x {u['paginas']} pag = {u['aserciones']} aserciones | {u['brutos']} brutos -> {u['unicos']} unicos | {u['segundos']} s")
    est = {r["estado"]: r["k"] for r in c.execute("SELECT estado, COUNT(*) k FROM hallazgos GROUP BY estado")}
    L.append(f"  - Hallazgos unicos: {est or '(ninguno)'}  (a triar = {est.get('a_triar', 0)}, defectos demostrados = {est.get('defecto_demostrado', 0)})")
    for r in c.execute("SELECT contrato,causa,familia,paginas,estado FROM hallazgos WHERE estado='a_triar' ORDER BY paginas DESC LIMIT 6"):
        L.append(f"      a_triar [{r['contrato']}] {r['causa']} | {r['familia']} | {r['paginas']} pag.")
    return L
