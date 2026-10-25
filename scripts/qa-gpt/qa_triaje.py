"""Analizador de fallos (job tipo T): agrupa por causa probable ENTRE lotes, consulta a GPT una vez por causa y persiste en `triaje`.

Clases: defecto_web | test_roto | flaky | infraestructura | sin_clasificar.
Nunca modifica el sitio ni ejecuta lo que devuelve GPT: la respuesta es una PROPUESTA. El parche se valida (rutas permitidas, texto
exacto presente) y solo lo aplica qa_pr en un worktree aislado, con el test que descubrio el fallo como prueba de regresion.
"""
import hashlib, json, re
from pathlib import Path

CLASES = ("defecto_web", "test_roto", "flaky", "infraestructura")
MAX_LOG = 3500
MAX_REPRESENTANTES = 6          # tests que se envian a GPT por causa (el resto solo se lista)
MAX_CODIGO = 3                  # ficheros de codigo relacionado por consulta
ESTADOS_FALLO = ("a_triar", "test_roto", "fallo_test", "defecto_demostrado", "actions_fallida", "revision_humana")
LINEA_ERROR = re.compile(r"AssertionError|ERR_ASSERTION|Error:|\bFAIL\b|expect\(|assert|Timeout|not ok", re.I)
RUTA_CODIGO = re.compile(r"(?<![\w/.-])((?:tests|qa|scripts|assets|data|[\w-]+)/[\w./-]+\.(?:py|mjs|js|html|css|json|xml))")


def migrar(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS triaje(id INTEGER PRIMARY KEY, grupo TEXT UNIQUE, causa_raiz TEXT, clase TEXT, propuestas TEXT,
      items TEXT, evidencia TEXT, reproduccion TEXT, arreglo TEXT, estado TEXT, fuente TEXT, creado TEXT, actualizado TEXT);
    """)
    cols = {r[1] for r in c.execute("PRAGMA table_info(triaje)")}
    for col in ("firma", "parche", "analisis", "validacion", "pr_estado", "pr_url", "pr_detalle",
                "decision", "decision_json", "decision_hash", "decision_fecha", "prioridad", "duplicado_de", "revision", "revision_hash", "integracion", "pr_head", "dev_estado"):
        if col not in cols: c.execute(f"ALTER TABLE triaje ADD COLUMN {col} TEXT")
    for col in ("intentos_dev", "pr_numero", "pr_nueva"):  # contadores/marcas: la PR es del flujo nuevo (Claude decide) si pr_nueva=1
        if col not in cols: c.execute(f"ALTER TABLE triaje ADD COLUMN {col} INTEGER DEFAULT 0")
    import qa_claude; qa_claude.migrar(c)
    c.commit()


def guardar(c, ahora, grupo, causa, clase, propuestas, items, evidencia, reproduccion, arreglo, fuente, estado="triado", **extra):
    if clase not in CLASES: clase = "sin_clasificar"
    c.execute("""INSERT INTO triaje(grupo,causa_raiz,clase,propuestas,items,evidencia,reproduccion,arreglo,estado,fuente,creado,actualizado)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(grupo) DO UPDATE SET causa_raiz=excluded.causa_raiz,clase=excluded.clase,propuestas=excluded.propuestas,
      items=excluded.items,evidencia=excluded.evidencia,reproduccion=excluded.reproduccion,arreglo=excluded.arreglo,estado=excluded.estado,
      fuente=excluded.fuente,actualizado=excluded.actualizado""",
              (grupo, causa, clase, json.dumps(propuestas), json.dumps(items), evidencia, reproduccion, arreglo, estado, fuente, ahora, ahora))
    if extra:
        c.execute(f"UPDATE triaje SET {','.join(k + '=?' for k in extra)} WHERE grupo=?", (*extra.values(), grupo))
    c.commit()


def trozo_log(log, pid):
    """Extrae del log del lote la seccion de la propuesta (salida + primeras lineas de error)."""
    if not log or not Path(log).exists(): return ""
    t = Path(log).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"### propuesta #%s .*?(?=\n### propuesta #|\Z)" % pid, t, re.S)
    return (m.group(0) if m else "")[:MAX_LOG]


def firma(log):
    """Huella estable de la causa probable: primera linea de error normalizada (sin rutas, numeros ni hashes). Mismo mensaje = misma causa."""
    lineas = [l.strip() for l in (log or "").splitlines() if l.strip() and not l.startswith("###")]
    linea = next((l for l in lineas if LINEA_ERROR.search(l)), None) or " | ".join(lineas[-2:]) or "sin salida"
    n = linea.lower()
    n = re.sub(r"[a-z]:[\\/][^\s'\"]+", "<ruta>", n)
    n = re.sub(r"(?<![\w])(?:[\w.-]+/)+[\w.-]+", lambda m: m.group(0).rsplit("/", 1)[-1], n)
    n = re.sub(r"\b[0-9a-f]{7,40}\b", "<hash>", n)
    n = re.sub(r"\d+", "#", n)
    n = re.sub(r"\s+", " ", n)[:140]
    return hashlib.sha1(n.encode("utf-8")).hexdigest()[:10], n


def _slug(clave): return re.sub(r"\W", "_", clave)


def fallos_de_item(c, it, dir_lote):
    """Fallos individuales (con identificador, rama, sha, test exacto, comando y salida) de un item de lote."""
    ids = json.loads(it["propuestas"] or "[]") if (it["propuestas"] or "").startswith("[") else []
    rama, _, sha = it["clave"].partition("@")
    base = {"item": it["clave"], "rama": rama, "sha_corto": sha}
    out = []
    for pid in ids:
        t = trozo_log(it["local_log"], pid)
        if not re.search(r"-> exit [1-9]", t): continue
        m = re.match(r"### propuesta #\d+ (.*?) -> exit (\d+)", t)
        cmd = m.group(1) if m else ""
        out.append({**base, "propuesta": pid, "origen": "local", "comando": cmd, "ruta": cmd.split()[-1] if cmd else "", "log": t, "firma": firma(t)[0]})
    if not out and it["estado"] == "actions_fallida":  # fallo remoto: un registro por item con la cola del log de Actions
        lp = Path(dir_lote) / f"{_slug(it['clave'])}.actions.log"
        t = lp.read_text(encoding="utf-8", errors="replace")[-MAX_LOG:] if lp.exists() else (it["detalle"] or "")
        rutas = [p for p in RUTA_CODIGO.findall(t) if p.startswith(("tests/", "qa/"))]
        out.append({**base, "propuesta": ids[0] if ids else None, "origen": "actions", "comando": "", "ruta": rutas[0] if rutas else "", "log": t, "firma": firma(t)[0]})
    return out


def fallos_pendientes(c, dir_lote):
    """Fallos de items finales que aun no se analizaron (item no incluido en ningun grupo triado)."""
    out = []
    marks = ",".join("?" * len(ESTADOS_FALLO))
    for it in c.execute(f"SELECT clave, propuestas, local_log, detalle, estado FROM lote_items WHERE estado IN ({marks})", ESTADOS_FALLO):
        if c.execute("SELECT 1 FROM triaje WHERE items LIKE ?", (f'%{it["clave"]}%',)).fetchone(): continue
        out += fallos_de_item(c, it, dir_lote)
    return out


def pendientes(c, dir_lote=None):
    """Compatibilidad: items con fallos sin triar (una entrada por item). El servicio agrupa por causa con `grupos_pendientes`."""
    dir_lote = dir_lote or Path(".")
    por_item = {}
    for f in fallos_pendientes(c, dir_lote): por_item.setdefault(f["item"], []).append({"propuesta": f["propuesta"], "log": f["log"]})
    return [{"item": k, "detalle": "", "fallos": v} for k, v in por_item.items()]


def grupos_pendientes(c, dir_lote):
    """Agrupa los fallos pendientes por causa probable (firma) ENTRE items. Una causa ya analizada no se vuelve a consultar: sus items se
    anaden al grupo existente. Devuelve (payloads para GPT, items ya cubiertos por analisis previos)."""
    por_firma = {}
    for f in fallos_pendientes(c, dir_lote): por_firma.setdefault(f["firma"], []).append(f)
    nuevos, cubiertos = [], []
    for fi, fs in sorted(por_firma.items()):
        previo = c.execute("SELECT id,items FROM triaje WHERE firma=? ORDER BY id LIMIT 1", (fi,)).fetchone()
        if previo:
            items = sorted(set(json.loads(previo["items"] or "[]")) | {f["item"] for f in fs})
            c.execute("UPDATE triaje SET items=? WHERE id=?", (json.dumps(items), previo["id"])); c.commit()
            cubiertos += [f["item"] for f in fs]; continue
        nuevos.append({"firma": fi, "n": len(fs), "afectados": [{"item": f["item"], "propuesta": f["propuesta"], "ruta": f["ruta"]} for f in fs],
                       "fallos": fs[:MAX_REPRESENTANTES]})
    return nuevos, cubiertos


def encolar(q, c):
    """Un job T por causa (no por test, no por item). Idempotente: la clave del job es la firma."""
    nuevos, cubiertos = grupos_pendientes(c, q.STATE / "lote")
    n = 0
    for g in nuevos:
        if q.enqueue(c, "T", "triaje:" + g["firma"], g, "T:" + g["firma"]): n += 1
    return n, len(cubiertos)


def cmd_triaje(q, a):
    c = q.db(); n, cub = encolar(q, c)
    print(f"Triaje: {n} jobs T encolados ({cub} fallos ya cubiertos por analisis previos); en tabla: {c.execute('SELECT COUNT(*) FROM triaje').fetchone()[0]} grupos")


def contexto_codigo(q, fallos):
    """Codigo real que GPT necesita ver: el test que falla (en su rama) y los ficheros que la salida menciona (en origin/main)."""
    partes, vistos = [], set()
    for f in fallos:
        if f["ruta"] and f["ruta"] not in vistos and f.get("sha_corto") is not None:
            vistos.add(f["ruta"])
            try: txt = q.git("show", f"{f['rama']}:{f['ruta']}", cwd=q.ROOT, check=False) or q.git("show", f"origin/main:{f['ruta']}", cwd=q.ROOT, check=False)
            except Exception: txt = ""
            if txt: partes.append(f"--- TEST {f['ruta']} ---\n{txt[:5000]}")
    for f in fallos:
        for r in RUTA_CODIGO.findall(f["log"]):
            if len(vistos) >= MAX_CODIGO + len(partes) or r in vistos or r.startswith(("tests/", "qa/")) or ".." in r: continue
            vistos.add(r)
            try: txt = q.git("show", f"origin/main:{r}", cwd=q.ROOT, check=False)
            except Exception: txt = ""
            if txt: partes.append(f"--- CODIGO {r} (origin/main) ---\n{txt[:5000]}")
    return "\n\n".join(partes)[:24000]


def prompt(q, job, c):
    p = json.loads(job["payload"])
    if "desarrollo" in p: return prompt_desarrollo(q, c, p["desarrollo"])
    if "firma" not in p:  # job antiguo (un item): formato v1
        return q.fill((q.HERE / "prompts" / "pass_triaje_v1.txt").read_text(encoding="utf-8"),
                      HEAD_SHA=q.git("rev-parse", "--short", "origin/main"), FALLOS=json.dumps(p["fallos"], ensure_ascii=False)[:24000], ITEM=p["item"])
    esperado = {}
    for f in p["fallos"]:
        r = c.execute("SELECT titulo,datos FROM propuestas WHERE id=?", (f["propuesta"],)).fetchone() if f.get("propuesta") else None
        if r:
            d = json.loads(r["datos"]); esperado[f["propuesta"]] = {"titulo": r["titulo"], "invariante": d.get("invariante"), "funcionalidad": d.get("funcionalidad"), "categoria": d.get("categoria")}
    visibles = [{k: f[k] for k in ("item", "propuesta", "ruta", "comando", "origen", "log")} for f in p["fallos"]]
    return q.fill((q.HERE / "prompts" / "pass_analisis_v2.txt").read_text(encoding="utf-8"),
                  HEAD_SHA=q.git("rev-parse", "--short", "origin/main"), N=p["n"], FIRMA=p["firma"],
                  AFECTADOS=json.dumps(p["afectados"], ensure_ascii=False)[:3000], ESPERADO=json.dumps(esperado, ensure_ascii=False)[:4000],
                  FALLOS=json.dumps(visibles, ensure_ascii=False)[:20000], CODIGO=contexto_codigo(q, p["fallos"]),
                  ENTORNO="Windows 10 local / ubuntu-latest en GitHub Actions; Python 3.11, Node 20, Playwright Chromium; sitio estatico servido con python http.server")


def ingest(q, c, job, data):
    p = json.loads(job["payload"]); n = 0
    if "desarrollo" in p: return ingest_desarrollo(q, c, p["desarrollo"], data)
    items = sorted({a["item"] for a in p.get("afectados", [])} | ({p["item"]} if "item" in p else set()))
    firma_ = p.get("firma")
    for g in data.get("grupos", []):
        ids = [int(x) for x in g.get("propuestas", []) if str(x).isdigit()] or [a["propuesta"] for a in p.get("afectados", []) if a.get("propuesta")]
        grupo = f"{firma_ or p.get('item')}#{g.get('causa_raiz', '')[:60]}"
        analisis = {k: g.get(k) for k in ("es_defecto_producto", "es_error_test", "es_infra", "intermitente", "hipotesis", "archivos_a_modificar",
                                          "pruebas_que_lo_demuestran", "componentes_afectados", "confianza", "comportamiento_esperado", "comportamiento_observado")}
        parche, validacion = None, {"ok": False, "problemas": ["sin parche"]}
        if isinstance(g.get("parche"), dict):
            import qa_pr
            ok, problemas, norm = qa_pr.validar_parche(g["parche"], lambda r: _leer_repo(q, r, items))
            parche = json.dumps(norm, ensure_ascii=False) if ok else None
            validacion = {"ok": ok, "problemas": problemas}
        guardar(c, q.now(), grupo, g.get("causa_raiz", "?"), g.get("clase", ""), ids, items, g.get("evidencia", ""),
                g.get("reproduccion", ""), g.get("arreglo_propuesto", ""), "gpt",
                firma=firma_, parche=parche, analisis=json.dumps(analisis, ensure_ascii=False), validacion=json.dumps(validacion, ensure_ascii=False))
        for pid in ids:
            if g.get("clase") == "test_roto":
                q.estado_prop(c, pid, "invalida", "triaje GPT: test roto, a reparar y reencolar")
        n += 1
    if n == 0 and firma_:  # GPT contesto sin grupos: queda registrado para no repetir la consulta
        guardar(c, q.now(), f"{firma_}#sin_grupos", "GPT no devolvio grupos", "sin_clasificar", [], items, "", "", "", "gpt", estado="a_triar", firma=firma_)
    print(f"  TRIAJE {job['area']}: {n} grupos persistidos")
    return n


def _leer_repo(q, ruta, items):
    """Contenido de `ruta` en origin/main o, si es un test nuevo, en la rama de algun item afectado."""
    t = q.git("show", f"origin/main:{ruta}", cwd=q.ROOT, check=False)
    if t: return t
    for it in items:
        t = q.git("show", f"{it.partition('@')[0]}:{ruta}", cwd=q.ROOT, check=False)
        if t: return t
    return None


# ---------- decision de Claude (filtro tecnico: sin 'corregir' no hay desarrollo ni PR) ----------
DECISIONES = ("corregir", "rechazar", "test_incorrecto", "infraestructura", "duplicado", "ya_resuelto", "opcional", "necesita_evidencia")
SISTEMA_DECISION = ("Eres el director tecnico de un sistema de QA de un sitio web estatico (HTML/JS/CSS + generadores Python). Recibes expedientes compactos de fallos "
                    "detectados por tests escritos por GPT. Decide por cada expediente si MERECE una correccion en el producto. Un test puede fallar porque (A) la web "
                    "tiene un defecto real, (B) el test esta mal planteado o inventa un requisito, (C) fallo el entorno. Una mejora defensiva u opcional NO es un defecto. "
                    "Usa 'corregir' solo con: comportamiento incorrecto o necesidad real, relacion clara con el codigo actual, reproduccion o contrato verificable, impacto "
                    "razonable y criterio de aceptacion claro. Si 'parche_encaja_en_main' es false, el codigo ya cambio: probablemente 'ya_resuelto'. Si hay duplicados_posibles "
                    "con la misma causa, 'duplicado' y su id en relacionados. Si falta evidencia, 'necesita_evidencia' e indica en 'pide' que ficheros o fragmentos necesitas. "
                    "Se breve y concreto. Responde SOLO con el JSON del esquema.")
ESQUEMA_DECISION = {"type": "object", "required": ["decisiones"], "properties": {"decisiones": {"type": "array", "maxItems": 8, "items": {
    "type": "object", "required": ["id", "decision", "prioridad", "causa_probable", "justificacion", "confianza"],
    "properties": {"id": {"type": "integer"}, "decision": {"type": "string", "enum": list(DECISIONES)}, "prioridad": {"type": "integer"},
                   "causa_probable": {"type": "string", "minLength": 1}, "justificacion": {"type": "string", "minLength": 1},
                   "evidencia_usada": {"type": "array", "items": {"type": "string"}}, "relacionados": {"type": "array", "items": {"type": "integer"}},
                   "archivos": {"type": "array", "items": {"type": "string"}}, "criterio_aceptacion": {"type": "string"},
                   "confianza": {"type": "string", "enum": ["alta", "media", "baja"]}, "pide": {"type": "array", "items": {"type": "string"}}}}}}}
LOTE_DECISION = 6          # expedientes por consulta (se agrupan decisiones independientes)
INTENTOS_DECISION = 2      # consultas maximas por expediente


def _j(x, d=None):
    try: return json.loads(x) if x else d
    except ValueError: return d


def archivos_de(row):
    a = _j(row["analisis"], {}) or {}
    p = _j(row["parche"], {}) or {}
    return sorted({*(a.get("archivos_a_modificar") or []), *(f["ruta"] for f in p.get("ficheros", []))})


def expediente(q, c, row, prs=()):
    """Expediente compacto (~2 KB) para Claude: nunca logs completos ni el repo."""
    a = _j(row["analisis"], {}) or {}; arch = archivos_de(row)
    par = _j(row["parche"], None)
    encaja, probl = None, []
    if par:
        try:
            import qa_pr
            encaja, probl, _ = qa_pr.validar_parche(par, lambda r: _leer_repo(q, r, _j(row["items"], [])))
        except Exception as e: probl = [str(e)[:100]]
    dup = []
    for o in c.execute("SELECT id,causa_raiz,analisis,parche,pr_url,decision FROM triaje WHERE id<>? AND COALESCE(decision,'') NOT IN ('rechazar','test_incorrecto','infraestructura') ORDER BY id", (row["id"],)):
        comunes = sorted(set(arch) & set(archivos_de(o)))
        if comunes: dup.append({"id": o["id"], "causa": (o["causa_raiz"] or "")[:100], "archivos_comunes": comunes[:4], "decision": o["decision"], "pr": o["pr_url"]})
    tests = []
    for pid in _j(row["propuestas"], [])[:5]:
        r = c.execute("SELECT titulo FROM propuestas WHERE id=?", (pid,)).fetchone()
        if r: tests.append(f"#{pid} {r[0][:90]}")
    rel = [{"pr": p["number"], "rama": p["headRefName"], "archivos_comunes": sorted(set(arch) & {f["path"] for f in p.get("files", [])})[:4]}
           for p in prs if set(arch) & {f["path"] for f in p.get("files", [])}][:6]
    return {"id": row["id"], "firma": row["firma"], "clase_gpt": row["clase"], "causa_raiz": (row["causa_raiz"] or "")[:300], "archivos": arch,
            "comportamiento_esperado": (a.get("comportamiento_esperado") or "")[:300], "comportamiento_observado": (a.get("comportamiento_observado") or "")[:300],
            "hipotesis": (a.get("hipotesis") or "")[:300], "evidencia": (row["evidencia"] or "")[:700], "reproduccion": (row["reproduccion"] or "")[:300],
            "tests_afectados": tests, "n_items_afectados": len(_j(row["items"], [])), "confianza_gpt": a.get("confianza"),
            "parche": {"ficheros": [f["ruta"] for f in par["ficheros"]], "ejemplo": (par["ficheros"][0]["reemplazos"][0]["por"] or "")[:300]} if par else None,
            "parche_encaja_en_main": encaja, "problemas_parche": probl[:3], "duplicados_posibles": dup[:5], "prs_abiertas_mismos_archivos": rel,
            "estado_actual": {"decision": row["decision"], "pr": row["pr_url"], "pr_estado": row["pr_estado"]}}


def decision_valida(d):
    """Reglas que el esquema no expresa. Una respuesta incoherente NUNCA aprueba: se degrada a necesita_evidencia."""
    if d["decision"] == "corregir":
        if not (d.get("criterio_aceptacion") or "").strip(): return "corregir sin criterio de aceptacion"
        if d["confianza"] == "baja": return "corregir con confianza baja"
        if not d.get("archivos"): return "corregir sin archivos implicados"
    if d["decision"] == "duplicado" and not d.get("relacionados"): return "duplicado sin id relacionado"
    return None


def reglas_previas(row):
    """Decisiones deterministas que no gastan Claude (clase ya concluida por el analisis GPT)."""
    if (row["grupo"] or "").endswith("#sin_grupos"): return "necesita_evidencia", "GPT no devolvio grupos para esta causa"
    if row["clase"] == "infraestructura": return "infraestructura", "clasificada como entorno por el analisis"
    if row["clase"] == "test_roto" and (_j(row["analisis"], {}) or {}).get("es_defecto_producto"): return None  # el test falla mal, pero ademas hay un defecto real: que decida Claude
    if row["clase"] == "test_roto": return "test_incorrecto", "el analisis concluye que el test esta mal planteado"
    if row["clase"] == "flaky": return "rechazar", "intermitente, sin defecto reproducible"
    return None


def aplicar_decision(q, c, row, d, huella):
    err = decision_valida(d)
    if err: d = {**d, "decision": "necesita_evidencia", "justificacion": f"[degradada: {err}] " + d["justificacion"]}
    dec = d["decision"]
    dup = d["relacionados"][0] if dec == "duplicado" and d.get("relacionados") else None
    c.execute("UPDATE triaje SET decision=?,decision_json=?,decision_hash=?,decision_fecha=?,prioridad=?,duplicado_de=?,actualizado=? WHERE id=?",
              (dec, json.dumps(d, ensure_ascii=False), huella, q.now(), str(max(1, min(5, d["prioridad"]))), dup, q.now(), row["id"]))
    c.execute("INSERT INTO eventos(fecha,entidad,ident,estado,nota) VALUES(?,?,?,?,?)", (q.now(), "triaje", row["id"], "decision_" + dec, d["justificacion"][:200])); c.commit()
    return dec


def decidir_pendientes(q, c, prs=(), maximo=LOTE_DECISION, out=print):
    """Decide hasta `maximo` expedientes sin decision vigente. Una decision 'necesita_evidencia' se reintenta como mucho INTENTOS_DECISION veces."""
    import qa_claude
    n = 0; cola = []
    for row in c.execute("SELECT * FROM triaje ORDER BY COALESCE(prioridad,'9'), id").fetchall():
        if row["decision"] and row["decision"] != "necesita_evidencia": continue
        r = reglas_previas(row)
        if r:
            c.execute("UPDATE triaje SET decision=?,decision_json=?,decision_fecha=?,prioridad=COALESCE(prioridad,'5') WHERE id=?",
                      (r[0], json.dumps({"id": row["id"], "decision": r[0], "justificacion": r[1], "origen": "regla"}), q.now(), row["id"])); c.commit(); n += 1; continue
        if row["decision"] and c.execute("SELECT COUNT(*) FROM claude_llamadas WHERE ok=1 AND clave LIKE ?", (f"%decision:%{row['id']}%",)).fetchone()[0] >= INTENTOS_DECISION: continue
        cola.append(row)
    cola = cola[:maximo]
    for i in range(0, len(cola), LOTE_DECISION):
        grupo = cola[i:i + LOTE_DECISION]
        exps = [expediente(q, c, r, prs) for r in grupo]
        huellas = {e["id"]: qa_claude.huella(json.dumps({k: v for k, v in e.items() if k != "estado_actual"}, sort_keys=True)) for e in exps}
        try: res, meta = qa_claude.llamar(q, c, "decision:" + ",".join(str(r["id"]) for r in grupo), "decision", SISTEMA_DECISION,
                                          json.dumps({"expedientes": exps}, ensure_ascii=False), ESQUEMA_DECISION)
        except qa_claude.ClaudeError as e: out(f"  Claude: {str(e)[:140]}"); break
        por_id = {d["id"]: d for d in res["decisiones"]}
        for r in grupo:
            d = por_id.get(r["id"])
            if not d: continue   # no contestado: sigue pendiente, nunca se aprueba por omision
            out(f"  Claude decide #{r['id']}: {aplicar_decision(q, c, r, d, huellas[r['id']])}"); n += 1
    return n


# ---------- desarrollo GPT de una causa APROBADA (solo se encola con decision='corregir') ----------
MAX_INTENTOS_DEV = 2


def encolar_desarrollo(q, c, row, problemas=""):
    """Un job T 'desarrollo' por (causa, intento): idempotente por clave. Solo causas aprobadas por Claude y bajo el limite de intentos."""
    if row["decision"] != "corregir": return False
    maxi = (q.CFG.get("flujo") or {}).get("max_intentos", MAX_INTENTOS_DEV)
    n = row["intentos_dev"] or 0
    if n >= maxi: return False
    d = _j(row["decision_json"], {})
    dev = {"id": row["id"], "firma": row["firma"], "intento": n + 1, "problemas": (problemas or "(primer intento)")[:600], "criterio": d.get("criterio_aceptacion", ""),
           "archivos": d.get("archivos") or archivos_de(row), "causa": (row["causa_raiz"] or "")[:300]}
    ok = q.enqueue(c, "T", f"desarrollo:{row['firma'] or row['id']}", {"desarrollo": dev}, f"D:{row['firma'] or row['id']}:{n + 1}")
    if ok: c.execute("UPDATE triaje SET intentos_dev=?,dev_estado='en_desarrollo',actualizado=? WHERE id=?", (n + 1, q.now(), row["id"])); c.commit()
    return ok


def prompt_desarrollo(q, c, dev):
    row = c.execute("SELECT * FROM triaje WHERE id=?", (dev["id"],)).fetchone()
    a = _j(row["analisis"], {}) or {}
    codigo, vistos = [], set()
    for r in dev["archivos"][:MAX_CODIGO + 2]:
        if r in vistos or ".." in r: continue
        vistos.add(r)
        t = q.git("show", f"origin/main:{r}", cwd=q.ROOT, check=False)
        if t: codigo.append(f"--- {r} ---\n{t[:6000]}")
    tests = [x for pid in _j(row["propuestas"], []) for x in [f"propuesta #{pid}"]]
    return q.fill((q.HERE / "prompts" / "pass_desarrollo_v1.txt").read_text(encoding="utf-8"), HEAD_SHA=q.git("rev-parse", "--short", "origin/main"),
                  FIRMA=dev["firma"], INTENTO=dev["intento"], CAUSA=dev["causa"], ESPERADO=(a.get("comportamiento_esperado") or "")[:400], CRITERIO=dev["criterio"],
                  ARCHIVOS=json.dumps(dev["archivos"]), TESTS=json.dumps(tests), PROBLEMAS=dev["problemas"], CODIGO="\n\n".join(codigo)[:20000])


def ingest_desarrollo(q, c, dev, data):
    """Parche nuevo para una causa aprobada. Se valida contra main; si no valida queda registrado y el ciclo decide si reintenta."""
    row = c.execute("SELECT * FROM triaje WHERE id=?", (dev["id"],)).fetchone()
    if not row: return 0
    if data.get("resuelto_en_main") or not isinstance(data.get("parche"), dict):
        c.execute("UPDATE triaje SET dev_estado=?,pr_detalle=?,actualizado=? WHERE id=?", ("sin_parche", (data.get("explicacion") or "GPT no propone parche")[:600], q.now(), row["id"]))
        c.commit(); return 1
    import qa_pr
    ok, problemas, norm = qa_pr.validar_parche(data["parche"], lambda r: _leer_repo(q, r, _j(row["items"], [])))
    c.execute("UPDATE triaje SET parche=?,validacion=?,pr_estado=NULL,dev_estado=?,actualizado=? WHERE id=?",
              (json.dumps(norm, ensure_ascii=False) if ok else row["parche"], json.dumps({"ok": ok, "problemas": problemas, "explicacion": (data.get("explicacion") or "")[:900], "confianza": data.get("confianza")}, ensure_ascii=False), "parche_listo" if ok else "parche_invalido", q.now(), row["id"]))
    c.commit(); print(f"  DESARROLLO #{row['id']}: {'parche validado' if ok else 'parche invalido: ' + '; '.join(problemas)[:120]}")
    return 1
