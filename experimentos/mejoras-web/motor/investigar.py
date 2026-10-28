"""investigar: el circuito de INVESTIGACION y DESARROLLO del laboratorio (lo ejecuta el servicio de INICIAR; no envia Actions ni abre PR).

  1) GPT investiga (job I): oportunidad concreta + estado real del sitio + fuentes; puede descartar sin codigo.
  2) Claude contrasta: ¿existe la necesidad?, ¿ya esta implementada?, ¿merece desarrollarse?
  3) GPT desarrolla (job D): cambio minimo + tests de aceptacion + (si reutiliza codigo ajeno) ruta, commit, literal y licencia.
  4) Claude revisa el parche: codigo, duplicidades, regresiones, coherencia editorial.
  El expediente termina en `preparado` (cola de EJECUTAR) o en un estado final con su motivo. La validacion local, Actions y la PR viven en
  actions.py / pr_hija.py y solo las activa una accion explicita.

PROCEDENCIA: la gestion de jobs GPT (reanudar por chat_id sin reenviar, respuesta guardada antes de ingerir, limite de uso, login, backoff, reintentos
acotados) es `process`/`fallo`/`ingest_answer` de scripts/qa-gpt/qa_gpt.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, simplificada: sin la escalada
automatica a Claude de jobs agotados (un job agotado queda visible en ESTADO) y sin los modos zona/familia/tipo/cambio del QA, sustituidos por la
rotacion area x lente (infinita por epocas). La rotacion con memoria de uso sigue la idea de `priority`/`cooldown` del QA.
"""
import datetime as dt, json, random, re, time
from pathlib import Path

import claude_cli, dedupe, mw, parches

ASK = None          # pruebas: sustituye a gpt_browser.ask
CLAUDE_HOOK = None  # pruebas: callable(clave, tipo, sistema, entrada, esquema) -> dict
PISTAS = None       # pruebas: callable(area, epoca) -> lista de pistas; None = descubrimiento real

ACTIVOS = ("investigado", "aprobado", "desarrollando", "parche_listo", "preparado")
FINALES_NO_DUPLICAR = ("duplicado", "descartado_manual")  # estados que no se usan como referencia de duplicado
# `evidencia_insuficiente` y `fallo_desarrollo` no bloquean volver a proponer algo parecido; el resto de descartes SI (no repetir lo rechazado)

ESQUEMA_CONTRASTE = {"type": "object", "required": ["decision", "motivo", "riesgo"],
                     "properties": {"decision": {"type": "string", "enum": ["aprobar", "rechazar", "ya_implementada", "investigar_mas"]},
                                    "motivo": {"type": "string", "minLength": 30},
                                    "criterio_aceptacion": {"type": "string"},
                                    "riesgo": {"type": "string", "enum": ["bajo", "medio", "alto"]},
                                    "archivos": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
                                    "observaciones": {"type": "string"}}}
ESQUEMA_REVISION = {"type": "object", "required": ["decision", "motivo", "riesgo"],
                    "properties": {"decision": {"type": "string", "enum": ["aprobar", "corregir", "rechazar"]},
                                   "motivo": {"type": "string", "minLength": 30},
                                   "problemas": {"type": "array", "items": {"type": "string"}, "maxItems": 10},
                                   "duplicidades": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                   "regresiones": {"type": "array", "items": {"type": "string"}, "maxItems": 6},
                                   "coherencia_editorial": {"type": "string"},
                                   "riesgo": {"type": "string", "enum": ["bajo", "medio", "alto"]}}}


class RespuestaInvalida(ValueError):
    pass


def leer_prompt(nombre):
    return (mw.LAB / "prompts" / nombre).read_text(encoding="utf-8")


def fill(tpl, **kv):
    for k, v in kv.items(): tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


# ---------- rotacion infinita: area x lente por epocas ----------
def lista_pares():
    return [f"{a['id']}|{i}" for a in mw.CFG["areas"] for i in range(len(mw.CFG["lentes"]))]


def elegir_par(c):
    """Par (area, lente) menos usado; epoca = veces del menos usado. Cada vuelta completa reordena los pares con otra semilla: no se agota nunca.
    Respeta un enfriamiento por par y devuelve (area_id, lente_idx, epoca)."""
    todos = lista_pares()
    veces = {r["par"]: r["veces"] for r in c.execute("SELECT par, veces FROM pares")}
    ult = {r["par"]: r["ultima"] for r in c.execute("SELECT par, ultima FROM pares")}
    epoca = min(veces.get(p, 0) for p in todos)
    cand = [p for p in todos if veces.get(p, 0) == epoca]
    random.Random(20261027 + epoca).shuffle(cand)
    frio = (mw._ahora() - dt.timedelta(days=mw.CFG.get("cooldown_par_dias", 2))).isoformat(timespec="seconds")
    par = next((p for p in cand if not ult.get(p) or ult[p] < frio), cand[0])
    area, lente = par.split("|")
    return area, int(lente), epoca


def marcar_par(c, area, lente, util=False):
    par = f"{area}|{lente}"
    c.execute("INSERT INTO pares(par, ultima, veces, utiles) VALUES(?,?,1,?) ON CONFLICT(par) DO UPDATE SET veces=veces+1, ultima=excluded.ultima, utiles=utiles+excluded.utiles",
              (par, mw.now(), 1 if util else 0))
    c.commit()


def area_de(area_id):
    return next(a for a in mw.CFG["areas"] if a["id"] == area_id)


def capacidad(c):
    """¿Se puede abrir otra investigacion? Tope de expedientes en curso + tope horario de consultas a ChatGPT."""
    n = c.execute(f"SELECT COUNT(*) FROM expedientes WHERE estado IN ({','.join('?' * len(ACTIVOS))})", ACTIVOS).fetchone()[0]
    return n < mw.CFG.get("max_pendientes", 6)


def consultas_ultima_hora(c):
    desde = (mw._ahora() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    return c.execute("SELECT COUNT(*) FROM peticiones WHERE hora>=?", (desde,)).fetchone()[0]


def encolar_investigacion(c):
    area, lente, epoca = elegir_par(c)
    clave = f"I:{area}:{lente}:{epoca}"
    payload = {"area": area, "lente": lente, "epoca": epoca}
    cur = c.execute("INSERT OR IGNORE INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES(?,?,?,?,?,?,?)",
                    (clave, "I", f"{area}|{lente}", "pendiente", json.dumps(payload), mw.now(), mw.now()))
    if cur.rowcount == 0:  # misma clave ya en ERROR (el par no se marca hasta que acaba bien): se reintenta en vez de quedar atascado para siempre
        cur = c.execute("UPDATE jobs SET estado='pendiente', intentos=0, no_antes=NULL, actualizado=? WHERE clave=? AND estado='error'", (mw.now(), clave))
    c.commit()
    return cur.rowcount > 0


def encolar_desarrollo(c, exp_id, problemas=(), observaciones=""):
    n = c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='D' AND payload LIKE ?", (f'%"{exp_id}"%',)).fetchone()[0] + 1
    clave = f"D:{exp_id}:{n}"
    c.execute("INSERT OR IGNORE INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES(?,?,?,?,?,?,?)",
              (clave, "D", exp_id, "pendiente", json.dumps({"exp": exp_id, "problemas": list(problemas), "observaciones": observaciones}), mw.now(), mw.now()))
    c.execute("UPDATE expedientes SET estado='desarrollando', intentos_parche=?, actualizado=? WHERE id=?", (n, mw.now(), exp_id))
    c.commit()


def next_job(c):
    ahora = mw.now()
    return c.execute("SELECT * FROM jobs WHERE estado='pendiente' AND (no_antes IS NULL OR no_antes<=?) ORDER BY (tipo='D') DESC, id LIMIT 1", (ahora,)).fetchone()


def nuevo_id(c):
    m = c.execute("SELECT MAX(CAST(substr(id,4) AS INTEGER)) FROM expedientes").fetchone()[0] or 0
    return f"MW-{m + 1:04d}"


# ---------- prompts ----------
def previos(c, n=25):
    filas = c.execute("SELECT id, titulo, estado, motivo FROM expedientes WHERE estado NOT IN ('invalido') ORDER BY rowid DESC LIMIT ?", (n,)).fetchall()
    return "\n".join(f"- [{r['estado']}] {r['titulo'][:90]}" + (f" ({(r['motivo'] or '')[:60]})" if r["estado"].startswith(("descartado", "duplicado")) else "") for r in filas) or "(ninguno todavia)"


def pistas_texto(area, epoca):
    if not mw.CFG.get("pistas", True): return "(desactivadas)"
    try:
        if PISTAS is not None: lista = PISTAS(area, epoca)
        else:
            import descubrimiento
            canal = {"apis": "api", "fuentes-datos": "api", "crecimiento": "sector", "funciones-editoriales": "sector", "automatizacion": "github"}.get(area, "web")
            lista = descubrimiento.nuevas(descubrimiento.descubrir(canal, area, epoca))[:5]
        return "\n".join(f"- {p.get('titulo', '')[:100]} ({p.get('publicado', '')}) {p.get('url', '')}" for p in lista) or "(sin pistas nuevas)"
    except Exception as e:  # red caida o API limitada: las pistas son opcionales, nunca bloquean
        return f"(pistas no disponibles: {type(e).__name__})"


def prompt_investigar(job, c):
    p = json.loads(job["payload"]); a = area_de(p["area"])
    sup = a["superficies"][p["epoca"] % len(a["superficies"])]
    return fill(leer_prompt("investigar.txt"), RAMA_BASE=mw.CFG["rama_base"], HEAD_SHA=mw.head_base()[:12], SITIO=mw.CFG["sitio"], AREA=a["nombre"],
                LENTE=mw.CFG["lentes"][p["lente"]], SUPERFICIE=sup, EPOCA=p["epoca"], PREVIOS=previos(c), PISTAS=pistas_texto(p["area"], p["epoca"]))


def leer_base(ruta):
    """Texto de un fichero en la rama base del laboratorio (sin checkout): None si no existe."""
    try: return mw.git("show", f"{mw.fuente_ref()}:{ruta}", check=True)
    except RuntimeError: return None


def existe_en_base(ruta):
    return mw.run(["git", "cat-file", "-e", f"{mw.fuente_ref()}:{ruta}"], cwd=mw.REPO, capture_output=True).returncode == 0


def prompt_desarrollar(job, c):
    p = json.loads(job["payload"]); e = c.execute("SELECT * FROM expedientes WHERE id=?", (p["exp"],)).fetchone()
    d = json.loads(e["datos"]); cont = json.loads(e["contraste"] or "{}")
    archivos = (cont.get("archivos") or d.get("archivos_objetivo") or [])[:6]
    partes, total = [], 0
    for r in archivos:
        if parches.ruta_segura(r): continue
        t = leer_base(r)
        if t is None: partes.append(f"=== {r} (NO EXISTE: si lo necesitas, crealo en ficheros_nuevos) ==="); continue
        t = t[:max(4000, 60000 // max(1, len(archivos)))]; total += len(t)
        partes.append(f"=== {r} ===\n{t}")
    pl = parches.lim
    return fill(leer_prompt("desarrollar.txt"), RAMA_BASE=mw.CFG["rama_base"], HEAD_SHA=mw.head_base()[:12], INTENTO=e["intentos_parche"] or 1, ID=e["id"], ID_MIN=e["id"].lower(),
                TITULO=e["titulo"], NECESIDAD=e["necesidad"], PROPUESTA=d.get("propuesta", ""), CRITERIO=cont.get("criterio_aceptacion") or d.get("criterio_aceptacion", ""),
                ARCHIVOS=", ".join(archivos) or "(los decide el desarrollador)", OBSERVACIONES=cont.get("observaciones") or p.get("observaciones") or "(ninguna)",
                PROBLEMAS="; ".join(p.get("problemas") or []) or "(primer intento)", CODIGO="\n\n".join(partes) or "(sin ficheros previos)",
                MAX_FICHEROS=pl("max_ficheros", 6), MAX_NUEVOS=pl("max_ficheros_nuevos", 4), MAX_TESTS=pl("max_tests", 3), DIR_TESTS=pl("dir_tests", "tests/mejoras-web/"))


def prompt_de(job, c):
    if job["tipo"] == "I": return prompt_investigar(job, c)
    texto = prompt_desarrollar(job, c)
    err = (job["error"] if "error" in job.keys() else None) or ""
    if err.startswith(("respuesta invalida", "parche invalido")) and "(primer intento)" in texto:
        # el rechazo del validador viaja al reintento: antes GPT repetia el mismo fallo 3 veces (MW-0008, 27/10)
        texto = texto.replace("(primer intento)", err[:500], 1)
    return texto


# ---------- ingesta ----------
def _url_ok(u):
    return isinstance(u, str) and re.fullmatch(r"https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/\S*)?", u) is not None


def validar_investigacion(d):
    """-> lista de problemas de forma (vacia = valida). No juzga si la idea es buena."""
    if d.get("descartar") is True:
        return [] if isinstance(d.get("motivo_descarte"), str) and len(d["motivo_descarte"].strip()) >= 15 else ["descartar sin motivo_descarte"]
    p = []
    for k, minimo in (("titulo", 8), ("necesidad", 40), ("propuesta", 30), ("criterio_aceptacion", 20), ("riesgos", 5)):
        if not isinstance(d.get(k), str) or len(d[k].strip()) < minimo: p.append(f"{k} ausente o demasiado corto")
    es = d.get("estado_sitio")
    if not isinstance(es, dict) or not isinstance(es.get("archivos_leidos"), list) or not es["archivos_leidos"] or not isinstance(es.get("observacion"), str) or len(es["observacion"]) < 20:
        p.append("estado_sitio sin archivos_leidos/observacion")
    fu = d.get("fuentes")
    if not isinstance(fu, list) or not fu or not all(isinstance(f, dict) and _url_ok(f.get("url")) and f.get("titulo") for f in fu): p.append("fuentes: se exige al menos una con url https y titulo")
    if not isinstance(d.get("archivos_objetivo"), list) or not d["archivos_objetivo"]: p.append("archivos_objetivo vacio")
    if not isinstance(d.get("pruebas_aceptacion"), list) or not d["pruebas_aceptacion"]: p.append("pruebas_aceptacion vacio")
    return p


def pool_duplicados(c):
    """Expedientes contra los que se compara: todo menos los marcados duplicado/invalido/manual y los de evidencia insuficiente."""
    out = []
    for r in c.execute("SELECT id, titulo, necesidad, h_necesidad, h_comportamiento, datos, contraste, estado FROM expedientes WHERE estado NOT IN ('duplicado','invalido','evidencia_insuficiente','fallo_desarrollo')"):
        d = json.loads(r["datos"] or "{}"); cont = json.loads(r["contraste"] or "{}")
        out.append({"id": r["id"], "titulo": r["titulo"], "necesidad": r["necesidad"], "h_necesidad": r["h_necesidad"], "h_comportamiento": r["h_comportamiento"],
                    "criterio": cont.get("criterio_aceptacion") or d.get("criterio_aceptacion", ""), "archivos": d.get("archivos_objetivo") or [], "estado": r["estado"]})
    return out


def ingest_investigacion(c, job, d):
    """Crea el expediente de una respuesta de investigacion. -> id. Lanza RespuestaInvalida si la forma no vale (el job se reintenta en chat nuevo)."""
    p = json.loads(job["payload"])
    problemas = validar_investigacion(d)
    if problemas: raise RespuestaInvalida("; ".join(problemas))
    eid = nuevo_id(c)
    if d.get("descartar") is True:
        c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,estado,datos,motivo,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (eid, p["area"], str(p["lente"]), (d.get("titulo") or "(descartada sin codigo)")[:100], d["motivo_descarte"][:400], "descartado_gpt", json.dumps(d, ensure_ascii=False),
                   d["motivo_descarte"][:400], mw.now(), mw.now()))
        c.execute("INSERT INTO historial VALUES(?,?,?,?)", (eid, mw.now(), "descartado_gpt", d["motivo_descarte"][:300])); c.commit()
        marcar_par(c, p["area"], p["lente"], util=False); return eid
    # el estado real del sitio debe ser real: las rutas que GPT dice haber leido existen en la rama base
    leidas = [r for r in d["estado_sitio"]["archivos_leidos"] if isinstance(r, str)]
    faltan = [r for r in leidas if not existe_en_base(r)]
    if not leidas or len(faltan) * 2 > len(leidas):
        raise RespuestaInvalida(f"GPT cita archivos que no existen en {mw.CFG['rama_base']}: {faltan[:4]} (no leyo el repo)")
    cand = {"id": eid, "titulo": d["titulo"], "necesidad": d["necesidad"], "criterio": d["criterio_aceptacion"], "archivos": d["archivos_objetivo"]}
    dup = dedupe.buscar_duplicado(cand, pool_duplicados(c))
    hn, hc = dedupe.huella_necesidad(d["necesidad"]), dedupe.huella_comportamiento(d["archivos_objetivo"], d["criterio_aceptacion"])
    estado = "duplicado" if dup else "investigado"
    c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,h_necesidad,h_comportamiento,estado,datos,duplicado_de,motivo,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (eid, p["area"], str(p["lente"]), d["titulo"][:100], d["necesidad"], hn, hc, estado, json.dumps(d, ensure_ascii=False), dup[0] if dup else None,
               f"{dup[1]} con {dup[0]} ({dup[2]})" if dup else None, mw.now(), mw.now()))
    c.execute("INSERT INTO historial VALUES(?,?,?,?)", (eid, mw.now(), estado, f"duplicado de {dup[0]}: {dup[1]}" if dup else "investigado por GPT")); c.commit()
    marcar_par(c, p["area"], p["lente"], util=not dup)
    return eid


def ingest_desarrollo(c, job, d):
    """Valida la propuesta de parche de GPT contra la rama base. Valida -> `parche_listo`; ya resuelta -> descartado_gpt; invalida -> RespuestaInvalida."""
    p = json.loads(job["payload"]); eid = p["exp"]
    if d.get("resuelto_en_base") is True and not d.get("parche"):
        mw.set_estado(c, eid, "descartado_gpt", "GPT indica que la mejora ya existe en la rama base: " + str(d.get("explicacion", ""))[:300]); return eid
    ok, problemas, prop = parches.validar_propuesta(d, leer_base)
    if not ok: raise RespuestaInvalida("parche invalido: " + "; ".join(problemas)[:600])
    c.execute("UPDATE expedientes SET parche=?, rama=?, actualizado=? WHERE id=?", (json.dumps(prop, ensure_ascii=False), mw.CFG["prefijo_rama"] + eid.lower(), mw.now(), eid))
    mw.set_estado(c, eid, "parche_listo", f"parche de GPT valido: {len(prop['tocados'])} ficheros, {len(prop['pruebas'])} tests")
    return eid


# ---------- Claude ----------
def claude(c, clave, tipo, sistema, entrada, esquema, **kw):
    if CLAUDE_HOOK is not None:
        salida = CLAUDE_HOOK(clave, tipo, sistema, entrada, esquema)
        probl = claude_cli.validar(salida, esquema)
        if probl: raise claude_cli.ClaudeError("esquema no cumplido: " + "; ".join(probl[:4]))
        return salida
    src = mw.preparar_src(); cfg = mw.CFG["claude"]; turnos = cfg.get("max_turnos", 10)
    try:
        return claude_cli.llamar(mw, c, clave, tipo, sistema, entrada, esquema, herramientas="Read,Grep,Glob", cwd=src, max_turnos=turnos, **kw)[0]
    except claude_cli.ClaudeLimiteLlamada:  # agoto turnos/presupuesto leyendo el repo: UNA repeticion con mas margen (tope por llamada x2.5)
        return claude_cli.llamar(mw, c, clave, tipo, sistema, entrada, esquema, herramientas="Read,Grep,Glob", cwd=src, max_turnos=int(turnos * 2.5),
                                 max_usd=min(2.5, cfg.get("max_usd_llamada", 1.0) * 2.5), usar_cache=False, **kw)[0]


def _fallo_claude(c, e, err):
    """Un fallo de Claude no pierde el expediente: reintento con espera; al tercero queda `claude_fallo` visible en ESTADO. El tope diario pausa el servicio."""
    if "tope diario" in str(err):
        (mw.STATE / "limite").write_text(mw.now()); raise SystemExit(str(err))
    d = json.loads(e["datos"] or "{}"); n = d.get("claude_fallos", 0) + 1
    d["claude_fallos"] = n; d["claude_no_antes"] = (mw._ahora() + dt.timedelta(minutes=5 * n)).isoformat(timespec="seconds")
    c.execute("UPDATE expedientes SET datos=?, motivo=?, actualizado=? WHERE id=?", (json.dumps(d, ensure_ascii=False), f"Claude: {str(err)[:200]}", mw.now(), e["id"])); c.commit()
    if n >= 3: mw.set_estado(c, e["id"], "claude_fallo", f"Claude fallo {n} veces: {str(err)[:200]}")
    print(f"  Claude no respondio ({str(err)[:120]}); reintento en {5 * n} min")


def resumen_expediente(e):
    d = json.loads(e["datos"] or "{}")
    return {k: d.get(k) for k in ("titulo", "necesidad", "estado_sitio", "fuentes", "propuesta", "archivos_objetivo", "criterio_aceptacion", "pruebas_aceptacion", "riesgos", "alternativas", "tamano")}


def similares(c, e, n=3):
    cand = {"id": e["id"], "titulo": e["titulo"], "necesidad": e["necesidad"]}
    d = json.loads(e["datos"] or "{}"); cand.update(criterio=d.get("criterio_aceptacion", ""), archivos=d.get("archivos_objetivo") or [])
    pts = sorted(((dedupe.similitud(cand, x)[0], x) for x in pool_duplicados(c) if x["id"] != e["id"]), key=lambda t: -t[0])[:n]
    return [{"id": x["id"], "titulo": x["titulo"], "estado": x["estado"], "similitud": round(p, 2)} for p, x in pts if p > 0.15]


def contrastar(c, e):
    entrada = json.dumps({"expediente": resumen_expediente(e), "ramas": {"base": mw.CFG["rama_base"]}, "expedientes_parecidos": similares(c, e)}, ensure_ascii=False)
    try: r = claude(c, f"contraste:{e['id']}", "contraste", leer_prompt("contrastar.txt"), entrada, ESQUEMA_CONTRASTE)
    except claude_cli.ClaudeError as err: return _fallo_claude(c, e, err)
    c.execute("UPDATE expedientes SET contraste=? WHERE id=?", (json.dumps(r, ensure_ascii=False), e["id"])); c.commit()
    dec = r["decision"]
    if dec == "aprobar":
        mw.set_estado(c, e["id"], "aprobado", "Claude: " + r["motivo"][:300]); encolar_desarrollo(c, e["id"], observaciones=r.get("observaciones", ""))
    elif dec == "ya_implementada": mw.set_estado(c, e["id"], "descartado_claude", "ya implementada: " + r["motivo"][:300])
    elif dec == "investigar_mas": mw.set_estado(c, e["id"], "evidencia_insuficiente", r["motivo"][:300])
    else: mw.set_estado(c, e["id"], "descartado_claude", r["motivo"][:300])
    return dec


def revisar(c, e, fetch=None):
    """Revision del parche: primero la procedencia del codigo externo contra GitHub (hechos), despues Claude (juicio)."""
    prop = json.loads(e["parche"]); intento = e["intentos_parche"] or 1
    ok, probl_proc, regs = parches.verificar_procedencia(prop["codigo_externo"], parches.textos_del_parche(prop), fetch)
    maxi = mw.CFG["flujo"].get("max_intentos_parche", 2)
    if not ok:
        return _tras_revision(c, e, "corregir", probl_proc, intento, maxi, "procedencia del codigo externo no verificada")
    entrada = json.dumps({"expediente": resumen_expediente(e), "criterio_aceptacion": (json.loads(e["contraste"] or "{}")).get("criterio_aceptacion"),
                          "parche": prop["parche"], "pruebas": [{"ruta": t["ruta"], "contenido": t["contenido"]} for t in prop["pruebas"]],  # COMPLETOS: recortarlos hacia que Claude rechazara tests "truncados" que no lo estaban (MW-0005/12/20/28/29)
                          "procedencia_verificada": regs, "expedientes_parecidos": similares(c, e)}, ensure_ascii=False)
    try: r = claude(c, f"revision:{e['id']}:{intento}", "revision", leer_prompt("revisar.txt"), entrada, ESQUEMA_REVISION)
    except claude_cli.ClaudeError as err: return _fallo_claude(c, e, err)
    c.execute("UPDATE expedientes SET revision=? WHERE id=?", (json.dumps({**r, "procedencia": regs}, ensure_ascii=False), e["id"])); c.commit()
    return _tras_revision(c, e, r["decision"], (r.get("problemas") or []) + (r.get("duplicidades") or []) + (r.get("regresiones") or []), intento, maxi, r["motivo"])


def _tras_revision(c, e, decision, problemas, intento, maxi, motivo):
    if decision == "aprobar": mw.set_estado(c, e["id"], "preparado", "Claude aprueba el parche: " + motivo[:260]); return "preparado"
    if decision == "corregir" and intento < maxi:
        mw.set_estado(c, e["id"], "desarrollando", f"Claude pide correcciones (intento {intento}/{maxi}): {motivo[:200]}")
        encolar_desarrollo(c, e["id"], problemas=problemas or [motivo]); return "corregir"
    mw.set_estado(c, e["id"], "parche_rechazado", f"{'sin intentos de correccion' if decision == 'corregir' else 'Claude rechaza'}: {motivo[:260]}"); return "rechazado"


# ---------- jobs GPT (reanudables) ----------
def guardar_respuesta(job, cid, texto):
    d = mw.STATE / "respuestas"; d.mkdir(parents=True, exist_ok=True)
    f = d / f"job{job['id']}_{cid[:8]}.txt"; f.write_text(texto, encoding="utf-8"); return f


def ingest_answer(c, job, texto):
    data = mw.load_json_block(texto)
    if not isinstance(data, dict): raise RespuestaInvalida("la respuesta no es un objeto JSON")
    if job["tipo"] == "I": ingest_investigacion(c, job, data)
    else: ingest_desarrollo(c, job, data)
    c.execute("UPDATE jobs SET estado='hecho', error=NULL, actualizado=? WHERE id=?", (mw.now(), job["id"])); c.commit()


def fallo(c, job, err, nuevo_chat=True):
    cfg = mw.CFG
    n = c.execute("SELECT intentos FROM jobs WHERE id=?", (job["id"],)).fetchone()[0]
    reset = ",chat_id=NULL,fase=NULL,respuesta=NULL" if nuevo_chat else ""
    previo = c.execute("SELECT error FROM jobs WHERE id=?", (job["id"],)).fetchone()[0] or ""
    if "[reencolado]" in previo and "[reencolado]" not in err: err = "[reencolado] " + err  # la marca sobrevive: el reencolado lento ocurre una sola vez
    if n > cfg["reintentos"] and "inaccesible" in err and "[reencolado]" not in previo:
        # Un chat que no abre es un problema de ChatGPT/navegador, no del trabajo: segunda oportunidad con chat NUEVO tras una espera (como el QA: reencolar_inaccesible_h)
        nb = (mw._ahora() + dt.timedelta(hours=cfg.get("reencolar_inaccesible_h", 1))).isoformat(timespec="seconds")
        c.execute(f"UPDATE jobs SET estado='pendiente',intentos=0,error=?,no_antes=?,actualizado=?{reset} WHERE id=?", (("[reencolado] " + err)[:300], nb, mw.now(), job["id"]))
    elif n > cfg["reintentos"]:
        c.execute(f"UPDATE jobs SET estado='error',error=?,actualizado=?{reset} WHERE id=?", (err[:300], mw.now(), job["id"]))
        if job["tipo"] == "D":
            c.commit(); mw.set_estado(c, job["area"], "fallo_desarrollo", f"GPT no produjo un parche valido tras {n} intentos: {err[:200]}")
    else:
        nb = (mw._ahora() + dt.timedelta(minutes=cfg["backoff_min"][min(n - 1, len(cfg["backoff_min"]) - 1)])).isoformat(timespec="seconds")
        c.execute(f"UPDATE jobs SET estado='pendiente',error=?,no_antes=?,actualizado=?{reset} WHERE id=?", (err[:300], nb, mw.now(), job["id"]))
    c.commit(); print(f"  fallo (intento {n}/{cfg['reintentos'] + 1}): {err[:160]}")


def procesar_job(c, job):
    import gpt_browser as g
    ask = ASK or g.ask
    cfg, jid = mw.CFG, job["id"]
    # 1) respuesta ya capturada y guardada pero sin ingerir (caida entre captura e ingesta): no se vuelve a preguntar
    if job["respuesta"] and Path(job["respuesta"]).exists():
        print(f"  reingesta desde {job['respuesta']}")
        try: return ingest_answer(c, job, Path(job["respuesta"]).read_text(encoding="utf-8"))
        except Exception as e: return fallo(c, job, f"reingesta: {e}", nuevo_chat=True)
    texto = prompt_de(job, c)
    reanudar = job["chat_id"] if job["fase"] == "generando" else None
    if not reanudar: c.execute("UPDATE jobs SET intentos=intentos+1 WHERE id=?", (jid,))
    c.execute("UPDATE jobs SET estado='en_curso',actualizado=? WHERE id=?", (mw.now(), jid)); c.commit()
    t0 = time.monotonic(); est = {"cid": reanudar}

    def on_chat(cid):  # chat creado: persistir YA (permite reanudar si todo se cae)
        est["cid"] = cid
        c.execute("UPDATE jobs SET chat_id=?,fase='generando',actualizado=? WHERE id=?", (cid, mw.now(), jid))
        c.execute("INSERT INTO peticiones(fecha,hora,tipo,area,chars_in,chars_out,ok,chat_id,estado) VALUES(?,?,?,?,?,?,?,?,?)",
                  (mw.today(), mw.now(), job["tipo"], job["area"], len(texto), 0, 0, cid, "enviada")); c.commit()

    def on_result(res):  # respuesta COMPLETA: validar y guardar antes de que se cierre la pestana
        if not res.texto.strip(): raise RespuestaInvalida("respuesta vacia")
        f = guardar_respuesta(job, res.cid, res.texto)
        c.execute("UPDATE jobs SET respuesta=?,fase='capturada',actualizado=? WHERE id=?", (str(f), mw.now(), jid))
        c.execute("UPDATE peticiones SET chars_out=?,ok=1,estado='terminada',herramientas=?,segundos=? WHERE chat_id=?", (len(res.texto), res.herramientas, int(time.monotonic() - t0), res.cid)); c.commit()
        est["res"] = res
        mw.load_json_block(res.texto)  # nada se da por bueno si no es JSON

    try:
        res = ask(texto, cfg["espera_respuesta_min"], cfg["stall_min"], on_chat, on_result, resume_cid=reanudar, registro=lambda m: print("  " + m))
    except g.LoginRequired:
        c.execute("UPDATE jobs SET estado='pendiente',error='login',actualizado=? WHERE id=?", (mw.now(), jid)); c.commit()
        raise SystemExit("ChatGPT sin sesion en el Edge del laboratorio: inicia sesion y relanza (la cola se conserva).")
    except g.RateLimited as e:
        (mw.STATE / "limite").write_text(mw.now())
        c.execute("UPDATE jobs SET estado='pendiente',error=?,no_antes=?,actualizado=? WHERE id=?", (str(e), (mw._ahora() + dt.timedelta(minutes=5)).isoformat(timespec="seconds"), mw.now(), jid)); c.commit()  # (el mismo defecto de 3 valores para 4 marcadores estaba en qa_gpt.py:537; corregido tambien alli en a3a7cd89)
        raise SystemExit("Limite de uso de ChatGPT: pausa con espera (no se reintenta en bucle).")
    except g.Incompleta as e:
        cid = e.cid or est.get("cid")
        if cid: c.execute("UPDATE peticiones SET estado=? WHERE chat_id=?", (e.estado, cid)); c.commit()
        if e.estado == "backend" and cid:  # chat inaccesible/incierto: reintentos acotados; agotados, se abandona ese chat (el prompt se regenera)
            c.execute("UPDATE jobs SET intentos=intentos+1 WHERE id=?", (jid,)); c.commit()
            if c.execute("SELECT intentos FROM jobs WHERE id=?", (jid,)).fetchone()[0] > cfg["reintentos"]:
                return fallo(c, job, f"chat inaccesible: {e}", nuevo_chat=True)
        if e.estado in ("generando", "estancada", "backend") and cid:  # recuperable: se conserva el chat, se reanuda sin reenviar
            edad = (mw._ahora() - dt.datetime.fromisoformat(job["creado"])).total_seconds() / 3600
            if edad > cfg["reanudar_max_horas"]:
                c.execute("UPDATE jobs SET estado='error',error=?,actualizado=? WHERE id=?", (f"{e} (>{cfg['reanudar_max_horas']} h)", mw.now(), jid))
            else:
                nb = (mw._ahora() + dt.timedelta(minutes=cfg["backoff_min"][0])).isoformat(timespec="seconds")
                c.execute("UPDATE jobs SET estado='pendiente',chat_id=?,fase='generando',error=?,no_antes=?,actualizado=? WHERE id=?", (cid, str(e)[:300], nb, mw.now(), jid))
            c.commit(); print(f"  INCOMPLETA ({e.estado}), chat conservado para reanudar: {e}"); return
        return fallo(c, job, f"{e}", nuevo_chat=True)
    except RespuestaInvalida as e:
        return fallo(c, job, f"respuesta invalida: {e}", nuevo_chat=True)
    except Exception as e:
        cid = est.get("cid")
        if cid and "res" not in est:  # fallo tecnico con chat creado: reanudable
            c.execute("UPDATE jobs SET estado='pendiente',chat_id=?,fase='generando',error=?,no_antes=?,actualizado=? WHERE id=?",
                      (cid, str(e)[:300], (mw._ahora() + dt.timedelta(minutes=cfg["backoff_min"][0])).isoformat(timespec="seconds"), mw.now(), jid)); c.commit()
            print(f"  fallo tecnico, chat conservado: {str(e)[:160]}"); return
        return fallo(c, job, str(e), nuevo_chat=True)
    try: ingest_answer(c, job, res.texto)
    except RespuestaInvalida as e: fallo(c, job, f"respuesta invalida: {e}", nuevo_chat=True)
    except Exception as e: fallo(c, job, f"ingesta: {e}", nuevo_chat=False)  # la respuesta esta en disco: se reingiere sin volver a preguntar


# ---------- bucle ----------
def siguiente_exp(c, estado):
    ahora = mw.now()
    for e in c.execute("SELECT * FROM expedientes WHERE estado=? ORDER BY rowid", (estado,)):
        no_antes = (json.loads(e["datos"] or "{}")).get("claude_no_antes")
        if not no_antes or no_antes <= ahora: return e
    return None


def reconciliar(c):
    """Al arrancar/reanudar: cada expediente aprobado/desarrollando tiene su job D; los jobs fallidos no dejan expedientes colgados."""
    n = 0
    for e in c.execute("SELECT id, estado FROM expedientes WHERE estado IN ('aprobado','desarrollando')").fetchall():
        vivo = c.execute("SELECT 1 FROM jobs WHERE tipo='D' AND area=? AND estado IN ('pendiente','en_curso')", (e["id"],)).fetchone()
        if vivo: continue
        ultimo = c.execute("SELECT estado FROM jobs WHERE tipo='D' AND area=? ORDER BY id DESC LIMIT 1", (e["id"],)).fetchone()
        if ultimo and ultimo["estado"] == "error": mw.set_estado(c, e["id"], "fallo_desarrollo", "job de desarrollo agotado")
        elif ultimo and ultimo["estado"] == "hecho" and e["estado"] == "desarrollando": continue  # ya hay parche_listo/descarte: lo avanzara su estado
        else: encolar_desarrollo(c, e["id"]); n += 1
    return n


def motivo_espera(c):
    """Por que el investigador no hace nada ahora (para el log y ESTADO)."""
    por = dict(c.execute("SELECT estado, COUNT(*) FROM expedientes GROUP BY estado").fetchall())
    en_curso = sum(por.get(e, 0) for e in ACTIVOS)
    if en_curso >= mw.CFG.get("max_pendientes", 6):
        return (f"{en_curso} expedientes en curso (tope {mw.CFG.get('max_pendientes', 6)}): {por.get('preparado', 0)} preparado(s) esperan EJECUTAR; "
                "no se abren investigaciones nuevas hasta que se ejecuten (ESTADO lo muestra)")
    if consultas_ultima_hora(c) >= mw.CFG["flujo"].get("consultas_gpt_por_hora", 8): return "tope horario de consultas a ChatGPT; se reanuda en la hora siguiente"
    prox = c.execute("SELECT MIN(no_antes) FROM jobs WHERE estado='pendiente' AND no_antes IS NOT NULL").fetchone()[0]
    return f"trabajos en espera de reintento hasta {prox}" if prox else "sin trabajo pendiente"


def paso(c):
    """Un paso del servicio. True = hizo trabajo; False = nada ejecutable ahora; SystemExit = limite/login (lo gestiona el bucle)."""
    e = siguiente_exp(c, "investigado")
    if e: mw.marcar(estado="ejecutando", tarea="Claude contrasta " + e["id"]); print(f"{mw.now()} -> contraste {e['id']}: {e['titulo'][:60]}"); contrastar(c, e); return True
    e = siguiente_exp(c, "parche_listo")
    if e: mw.marcar(estado="ejecutando", tarea="Claude revisa " + e["id"]); print(f"{mw.now()} -> revision {e['id']}"); revisar(c, e); return True
    job = next_job(c)
    if job is None and capacidad(c) and consultas_ultima_hora(c) < mw.CFG["flujo"].get("consultas_gpt_por_hora", 8):
        encolar_investigacion(c); job = next_job(c)
    if job is None: return False
    if consultas_ultima_hora(c) >= mw.CFG["flujo"].get("consultas_gpt_por_hora", 8) and not job["chat_id"]: return False  # control de uso de ChatGPT
    mw.marcar(estado="ejecutando", tarea=f"GPT {'investiga' if job['tipo'] == 'I' else 'desarrolla'} {job['area']}")
    print(f"{mw.now()} -> {job['tipo']} {job['area']}" + (f" (reanudando chat {job['chat_id'][:8]})" if job["fase"] == "generando" and job["chat_id"] else ""))
    procesar_job(c, job)
    return True
