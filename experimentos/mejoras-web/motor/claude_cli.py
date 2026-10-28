"""PROCEDENCIA: scripts/qa-gpt/qa_claude.py @ fe131c8ce6a663b54ab067ea5bc123318ececbb0, blob 56189d8f2c8aa4fa7071b7143f5e90f4f13c9a6e.
CAMBIOS: `exe()` resuelve tambien el ejecutable nativo (~/.local/bin/claude[.exe]) y MEJORAS_WEB_CLAUDE_EXE (no QA_CLAUDE_EXE); tope diario de gasto
(`max_usd_dia`, ClaudeError ANTES de gastar); la config de cuentas extra NO se hereda del QA (cuentas_extra vacio por defecto: no se tocan sesiones ajenas).
Todo lo demas (esquema, cache, lock, rotacion de cuentas por limite, registro de coste) es literal. `q` es el modulo mw (CFG, STATE, now).

Cliente de decision estructurada con Claude Code CLI headless (`claude -p`). Claude DECIDE, no desarrolla.

Por que CLI y no claude.ai/code: el CLI devuelve JSON validado por esquema, coste/tokens/duracion por llamada, no depende de selectores del DOM ni de
sesiones en la nube que se acumulan, y se lanza bajo demanda (cero procesos residentes). Una llamada sin herramientas con sistema minimo cuesta ~0,01 USD;
con la configuracion por defecto (CLAUDE.md, skills, MCP, herramientas) la misma llamada cuesta ~0,40 USD, por eso se desactivan.

Garantias: sin herramientas de escritura (solo --tools vacio o Read/Grep/Glob), un solo proceso claude a la vez (lock), timeout, cache por hash de la
entrada (misma evidencia = mismo veredicto, sin nueva consulta), cada llamada queda en `claude_llamadas` con coste, tokens y duracion.
Una respuesta que no cumple el esquema NUNCA se convierte en decision: lanza ClaudeError.
"""
import hashlib, json, os, re, subprocess, threading, time
from pathlib import Path

DEFECTOS = {"modelo": "claude-sonnet-5-5", "esfuerzo": "low", "max_turnos": 2, "timeout_s": 240, "max_usd_llamada": 0.5,
            "cuentas_extra": [], "extra_primero": False, "pausa_limite_s": 3600}
# limite de uso de la suscripcion (no el --max-budget-usd de una llamada): se salta a la siguiente cuenta
LIMITE = re.compile(r"usage limit|hit your limit|limit reached|rate.?limit|out of (extra )?usage|credit balance|\b429\b", re.I)
_AGOTADA = {}  # dir de cuenta ("" = la del sistema) -> time.time() hasta el que no se usa
_LOCK = threading.Lock()   # un Claude CLI de decision/revision a la vez dentro del proceso
_LOCK_DEV = threading.Lock()  # el desarrollo (minutos, ejecuta tests) va aparte: no retiene revisiones ni decisiones
_CLAUDE_EXE = None


class ClaudeError(RuntimeError): pass
class ClaudeLimiteLlamada(ClaudeError):
    """La llamada agoto sus turnos o su presupuesto (error_max_turns / error_max_budget_usd): no es un fallo de Claude, se puede repetir con mas margen."""


def migrar(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS claude_llamadas(id INTEGER PRIMARY KEY, fecha TEXT, clave TEXT, tipo TEXT, modelo TEXT, esfuerzo TEXT, turnos INTEGER,
      coste_usd REAL, tok_in INTEGER, tok_out INTEGER, tok_cache_lee INTEGER, tok_cache_crea INTEGER, segundos REAL, ok INTEGER, error TEXT, hash TEXT);
    CREATE TABLE IF NOT EXISTS claude_veredictos(clave TEXT, hash TEXT, respuesta TEXT, fecha TEXT, PRIMARY KEY(clave, hash));
    """)
    c.commit()


def config(q):
    return {**DEFECTOS, **(q.CFG.get("claude") or {})}


def exe():
    """Ejecutable real de claude (no el .cmd de npm: evita el re-entrecomillado de cmd.exe con el esquema JSON)."""
    global _CLAUDE_EXE
    if _CLAUDE_EXE: return _CLAUDE_EXE
    import shutil
    cand = [os.environ.get("MEJORAS_WEB_CLAUDE_EXE", ""), str(Path.home() / ".local" / "bin" / ("claude.exe" if os.name == "nt" else "claude"))]
    w = shutil.which("claude")
    if w: cand.append(str(Path(w).with_name("node_modules") / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe")); cand.append(w)
    for x in cand:
        if x and Path(x).exists(): _CLAUDE_EXE = x; return x
    raise ClaudeError("claude CLI no encontrado (npm i -g @anthropic-ai/claude-code)")


def validar(dato, esquema, ruta="$"):
    """Validador minimo de JSON Schema (type, properties, required, enum, items, minLength, maxItems). Devuelve lista de problemas."""
    t = esquema.get("type"); p = []
    tipos = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}
    if t and not (isinstance(dato, tipos[t]) and not (t in ("integer", "number") and isinstance(dato, bool))): return [f"{ruta}: se esperaba {t}"]
    if "enum" in esquema and dato not in esquema["enum"]: p.append(f"{ruta}: valor fuera de {esquema['enum']}")
    if t == "string" and len(dato) < esquema.get("minLength", 0): p.append(f"{ruta}: vacio")
    if t == "object":
        for k in esquema.get("required", []):
            if k not in dato: p.append(f"{ruta}.{k}: falta")
        for k, sub in esquema.get("properties", {}).items():
            if k in dato: p += validar(dato[k], sub, f"{ruta}.{k}")
    if t == "array":
        if len(dato) > esquema.get("maxItems", 10**6): p.append(f"{ruta}: demasiados elementos")
        if "items" in esquema:
            for i, x in enumerate(dato):
                p += validar(x, esquema["items"], f"{ruta}[{i}]")
    return p


def cuentas(cfg):
    """Cuentas por orden de preferencia: la del sistema y despues cada CLAUDE_CONFIG_DIR de cuentas_extra que exista (login hecho);
    con extra_primero, las extra antes (reservar la cuota de la del sistema). Las que dieron limite hace menos de pausa_limite_s van al final."""
    extra = [str(x) for x in cfg.get("cuentas_extra") or [] if x and Path(x).is_dir()]
    todas = extra + [""] if cfg.get("extra_primero") else [""] + extra
    ahora = time.time()
    return [x for x in todas if _AGOTADA.get(x, 0) <= ahora] + sorted((x for x in todas if _AGOTADA.get(x, 0) > ahora), key=lambda x: _AGOTADA[x])


def gasto_hoy(c, hoy):
    """USD gastados hoy segun claude_llamadas (fecha ISO local)."""
    return c.execute("SELECT COALESCE(SUM(coste_usd),0) FROM claude_llamadas WHERE substr(fecha,1,10)=?", (hoy,)).fetchone()[0] or 0.0


def huella(*partes):
    return hashlib.sha1("\x1f".join(partes).encode("utf-8")).hexdigest()[:16]


def llamar(q, c, clave, tipo, sistema, entrada, esquema, herramientas="", cwd=None, max_turnos=None, esfuerzo=None, usar_cache=True, timeout_s=None, max_usd=None):
    """-> (dict validado, meta). Cache por (clave, hash(sistema+entrada+esquema+modelo+esfuerzo)). Lanza ClaudeError si falla o no valida.
    `herramientas` admite patrones de permiso (`Bash(cmd:*)`): --tools recibe solo el nombre y --allowedTools el patron."""
    cfg = config(q); esf = esfuerzo or cfg["esfuerzo"]
    cfg = {**cfg, "timeout_s": timeout_s or cfg["timeout_s"], "max_usd_llamada": max_usd or cfg["max_usd_llamada"]}
    nombres = ",".join(dict.fromkeys(h.split("(")[0].strip() for h in herramientas.split(",") if h.strip())) if herramientas else ""
    h = huella(sistema, entrada, json.dumps(esquema, sort_keys=True), cfg["modelo"], esf, herramientas)

    if usar_cache:
        r = c.execute("SELECT respuesta FROM claude_veredictos WHERE clave=? AND hash=?", (clave, h)).fetchone()
        if r:
            try:
                dato_cache = json.loads(r[0])
                if not validar(dato_cache, esquema):
                    return dato_cache, {"cache": True, "hash": h}
            except (ValueError, TypeError, KeyError):
                pass
            # Una fila corrupta o incompatible no puede convertirse en decision.
            # Se invalida y se vuelve a consultar Claude.
            c.execute("DELETE FROM claude_veredictos WHERE clave=? AND hash=?", (clave, h))
            c.commit()

    tope = cfg.get("max_usd_dia")
    if tope and gasto_hoy(c, q.today()) >= tope:
        raise ClaudeError(f"tope diario de gasto Claude alcanzado ({tope} USD): sin consultas hasta manana")
    args = [exe(), "-p", "--model", cfg["modelo"], "--effort", esf, "--output-format", "json",
            "--max-turns", str(max_turnos or cfg["max_turnos"]), "--tools", nombres, "--system-prompt", sistema, "--setting-sources", "",
            "--disable-slash-commands", "--strict-mcp-config", "--no-session-persistence", "--json-schema", json.dumps(esquema, ensure_ascii=False),
            "--max-budget-usd", str(cfg["max_usd_llamada"])]
    if herramientas: args += ["--allowedTools", herramientas]
    t0 = time.time(); err = None; meta = {"hash": h}; salida = None
    with (_LOCK_DEV if tipo == "desarrollo" else _LOCK):
        for cuenta in cuentas(cfg):
            err = None
            env = {**os.environ, "CLAUDE_CONFIG_DIR": cuenta} if cuenta else None
            Path(cwd or q.STATE / "claude").mkdir(parents=True, exist_ok=True)  # un cwd inexistente se confundia con "claude no ejecutable"
            try:
                r = subprocess.run(args, input=entrada, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=cfg["timeout_s"],
                                   cwd=str(cwd or q.STATE / "claude"), env=env, creationflags=0x08000000 if os.name == "nt" else 0)
                if r.returncode:
                    err = f"claude exit {r.returncode}: {(r.stderr or r.stdout)[-300:]}"
                    try:  # claude -p devuelve su JSON de resultado tambien con exit 1: el subtipo dice la causa real (antes solo se veia la cola del JSON)
                        dj = json.loads(r.stdout); sub = str(dj.get("subtype") or "")
                        err = f"claude exit {r.returncode}: {sub or 'error'}: {str(dj.get('result') or dj.get('errors') or '')[:200]}"
                        if sub in ("error_max_turns", "error_max_budget_usd"): err = "LIMITE_LLAMADA " + err
                    except (ValueError, TypeError, AttributeError): pass
                else:
                    d = json.loads(r.stdout)
                    u = d.get("usage") or {}
                    meta.update(coste=d.get("total_cost_usd"), turnos=d.get("num_turns"), tok_in=u.get("input_tokens"), tok_out=u.get("output_tokens"),
                                cache_lee=u.get("cache_read_input_tokens"), cache_crea=u.get("cache_creation_input_tokens"))
                    if d.get("is_error"): err = f"claude error: {str(d.get('result'))[:300]}"
                    else:
                        salida = d.get("structured_output")
                        if salida is None:
                            try: salida = json.loads(d.get("result") or "")
                            except ValueError: err = "sin salida estructurada"
            except subprocess.TimeoutExpired: err = f"claude timeout {cfg['timeout_s']}s"
            except (OSError, ValueError) as e: err = f"claude no ejecutable: {str(e)[:200]}"
            if not (err and LIMITE.search(err) and "budget" not in err.lower()): break
            _AGOTADA[cuenta] = time.time() + cfg["pausa_limite_s"]
            err = f"[cuenta {cuenta or 'sistema'} en limite] {err}"
    if salida is not None and not err:
        probl = validar(salida, esquema)
        if probl: err = "esquema no cumplido: " + "; ".join(probl[:4])
    seg = round(time.time() - t0, 1)
    c.execute("INSERT INTO claude_llamadas(fecha,clave,tipo,modelo,esfuerzo,turnos,coste_usd,tok_in,tok_out,tok_cache_lee,tok_cache_crea,segundos,ok,error,hash) "
              "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (q.now(), clave, tipo, cfg["modelo"], esf, meta.get("turnos"), meta.get("coste"), meta.get("tok_in"), meta.get("tok_out"), meta.get("cache_lee"),
               meta.get("cache_crea"), seg, 0 if err else 1, err, h))
    if err: c.commit(); raise (ClaudeLimiteLlamada if err.startswith("LIMITE_LLAMADA") else ClaudeError)(err)
    c.execute("INSERT OR REPLACE INTO claude_veredictos(clave,hash,respuesta,fecha) VALUES(?,?,?,?)", (clave, h, json.dumps(salida, ensure_ascii=False), q.now())); c.commit()
    meta["segundos"] = seg
    return salida, meta


def resumen_consumo(c):
    """Para ESTADO: llamadas, coste y tokens medidos."""
    r = c.execute("SELECT COUNT(*),COALESCE(SUM(ok),0),COALESCE(SUM(coste_usd),0),"
                  "COALESCE(SUM(COALESCE(tok_in,0)+COALESCE(tok_cache_crea,0)+COALESCE(tok_cache_lee,0)),0),"
                  "COALESCE(SUM(tok_out),0),COALESCE(AVG(segundos),0) FROM claude_llamadas").fetchone()
    return {"llamadas": r[0], "ok": r[1], "usd": round(r[2], 3), "tok_entrada": r[3], "tok_salida": r[4], "seg_medio": round(r[5], 1)}
