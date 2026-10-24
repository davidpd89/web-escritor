"""Cliente de decision estructurada con Claude Code CLI headless (`claude -p`). Claude DECIDE, no desarrolla.

Por que CLI y no claude.ai/code: el CLI devuelve JSON validado por esquema, coste/tokens/duracion por llamada, no depende de selectores del DOM ni de
sesiones en la nube que se acumulan, y se lanza bajo demanda (cero procesos residentes). Una llamada sin herramientas con sistema minimo cuesta ~0,01 USD;
con la configuracion por defecto (CLAUDE.md, skills, MCP, herramientas) la misma llamada cuesta ~0,40 USD, por eso se desactivan.

Garantias: sin herramientas de escritura (solo --tools vacio o Read/Grep/Glob), un solo proceso claude a la vez (lock), timeout, cache por hash de la
entrada (misma evidencia = mismo veredicto, sin nueva consulta), cada llamada queda en `claude_llamadas` con coste, tokens y duracion.
Una respuesta que no cumple el esquema NUNCA se convierte en decision: lanza ClaudeError.
"""
import hashlib, json, os, subprocess, threading, time
from pathlib import Path

DEFECTOS = {"modelo": "claude-sonnet-5-5", "esfuerzo": "low", "max_turnos": 2, "timeout_s": 240, "max_usd_llamada": 0.5}
_LOCK = threading.Lock()   # un Claude CLI a la vez dentro del proceso
_CLAUDE_EXE = None


class ClaudeError(RuntimeError): pass


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
    cand = [os.environ.get("QA_CLAUDE_EXE", "")]
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
        for i, x in enumerate(dato[:50]):
            if "items" in esquema: p += validar(x, esquema["items"], f"{ruta}[{i}]")
    return p


def huella(*partes):
    return hashlib.sha1("\x1f".join(partes).encode("utf-8")).hexdigest()[:16]


def llamar(q, c, clave, tipo, sistema, entrada, esquema, herramientas="", cwd=None, max_turnos=None, esfuerzo=None, usar_cache=True):
    """-> (dict validado, meta). Cache por (clave, hash(sistema+entrada+esquema+modelo+esfuerzo)). Lanza ClaudeError si falla o no valida."""
    cfg = config(q); esf = esfuerzo or cfg["esfuerzo"]
    h = huella(sistema, entrada, json.dumps(esquema, sort_keys=True), cfg["modelo"], esf, herramientas)
    if usar_cache:
        r = c.execute("SELECT respuesta FROM claude_veredictos WHERE clave=? AND hash=?", (clave, h)).fetchone()
        if r: return json.loads(r[0]), {"cache": True, "hash": h}
    args = [exe(), "-p", "--model", cfg["modelo"], "--effort", esf, "--output-format", "json",
            "--max-turns", str(max_turnos or cfg["max_turnos"]), "--tools", herramientas, "--system-prompt", sistema, "--setting-sources", "",
            "--disable-slash-commands", "--strict-mcp-config", "--no-session-persistence", "--json-schema", json.dumps(esquema, ensure_ascii=False),
            "--max-budget-usd", str(cfg["max_usd_llamada"])]
    if herramientas: args += ["--allowedTools", herramientas]
    t0 = time.time(); err = None; meta = {"hash": h}; salida = None
    with _LOCK:
        try:
            r = subprocess.run(args, input=entrada, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=cfg["timeout_s"],
                               cwd=str(cwd or q.STATE / "claude"), creationflags=0x08000000 if os.name == "nt" else 0)
            if r.returncode: err = f"claude exit {r.returncode}: {(r.stderr or r.stdout)[-300:]}"
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
    if salida is not None and not err:
        probl = validar(salida, esquema)
        if probl: err = "esquema no cumplido: " + "; ".join(probl[:4])
    seg = round(time.time() - t0, 1)
    c.execute("INSERT INTO claude_llamadas(fecha,clave,tipo,modelo,esfuerzo,turnos,coste_usd,tok_in,tok_out,tok_cache_lee,tok_cache_crea,segundos,ok,error,hash) "
              "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (q.now(), clave, tipo, cfg["modelo"], esf, meta.get("turnos"), meta.get("coste"), meta.get("tok_in"), meta.get("tok_out"), meta.get("cache_lee"),
               meta.get("cache_crea"), seg, 0 if err else 1, err, h))
    if err: c.commit(); raise ClaudeError(err)
    c.execute("INSERT OR REPLACE INTO claude_veredictos(clave,hash,respuesta,fecha) VALUES(?,?,?,?)", (clave, h, json.dumps(salida, ensure_ascii=False), q.now())); c.commit()
    meta["segundos"] = seg
    return salida, meta


def resumen_consumo(c):
    """Para ESTADO: llamadas, coste y tokens medidos."""
    r = c.execute("SELECT COUNT(*),COALESCE(SUM(ok),0),COALESCE(SUM(coste_usd),0),COALESCE(SUM(tok_in+tok_cache_crea+tok_cache_lee),0),COALESCE(SUM(tok_out),0),"
                  "COALESCE(AVG(segundos),0) FROM claude_llamadas").fetchone()
    return {"llamadas": r[0], "ok": r[1], "usd": round(r[2], 3), "tok_entrada": r[3], "tok_salida": r[4], "seg_medio": round(r[5], 1)}
