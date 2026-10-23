"""Triaje de fallos (job tipo T): agrupa por causa raiz, clasifica y persiste en la tabla `triaje`.

Clases: defecto_web | test_roto | flaky | infraestructura | sin_clasificar.
Nunca modifica el sitio: el arreglo propuesto queda como texto para revisar en rama/PR aparte.
"""
import json, re
from pathlib import Path

CLASES = ("defecto_web", "test_roto", "flaky", "infraestructura")
MAX_LOG = 3500


def migrar(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS triaje(id INTEGER PRIMARY KEY, grupo TEXT UNIQUE, causa_raiz TEXT, clase TEXT, propuestas TEXT,
      items TEXT, evidencia TEXT, reproduccion TEXT, arreglo TEXT, estado TEXT, fuente TEXT, creado TEXT, actualizado TEXT);
    """)


def guardar(c, ahora, grupo, causa, clase, propuestas, items, evidencia, reproduccion, arreglo, fuente, estado="triado"):
    if clase not in CLASES: clase = "sin_clasificar"
    c.execute("""INSERT INTO triaje(grupo,causa_raiz,clase,propuestas,items,evidencia,reproduccion,arreglo,estado,fuente,creado,actualizado)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(grupo) DO UPDATE SET causa_raiz=excluded.causa_raiz,clase=excluded.clase,propuestas=excluded.propuestas,
      items=excluded.items,evidencia=excluded.evidencia,reproduccion=excluded.reproduccion,arreglo=excluded.arreglo,estado=excluded.estado,
      fuente=excluded.fuente,actualizado=excluded.actualizado""",
              (grupo, causa, clase, json.dumps(propuestas), json.dumps(items), evidencia, reproduccion, arreglo, estado, fuente, ahora, ahora))
    c.commit()


def trozo_log(log, pid):
    """Extrae del log del lote la seccion de la propuesta (salida + primeras lineas de error)."""
    if not log or not Path(log).exists(): return ""
    t = Path(log).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"### propuesta #%s .*?(?=\n### propuesta #|\Z)" % pid, t, re.S)
    return (m.group(0) if m else "")[:MAX_LOG]


def pendientes(c):
    """Items de lote a triar + hallazgos de Via A sin triar, con evidencia."""
    out = []
    for it in c.execute("SELECT clave, propuestas, local_log, detalle FROM lote_items WHERE estado IN ('a_triar','test_roto','defecto_demostrado','revision_humana')"):
        if c.execute("SELECT 1 FROM triaje WHERE items LIKE ?", (f'%{it["clave"]}%',)).fetchone(): continue
        ids = json.loads(it["propuestas"] or "[]") if (it["propuestas"] or "").startswith("[") else []
        fallos = []
        for pid in ids:
            t = trozo_log(it["local_log"], pid)
            if re.search(r"-> exit [1-9]", t): fallos.append({"propuesta": pid, "log": t})
        if fallos: out.append({"item": it["clave"], "detalle": it["detalle"], "fallos": fallos})
    return out


def cmd_triaje(q, a):
    """Encola un job T por cada tanda de fallos sin triar (el servicio lo ejecuta con GPT)."""
    c = q.db(); n = 0
    for it in pendientes(c):
        clave = "T:" + it["item"]
        if q.enqueue(c, "T", "triaje:" + it["item"].split("@")[0].split("/")[-1], it, clave):
            n += 1; print(f"  encolado triaje {clave} ({len(it['fallos'])} fallos)")
    print(f"Triaje: {n} jobs T encolados; en tabla: {c.execute('SELECT COUNT(*) FROM triaje').fetchone()[0]} grupos")


def prompt(q, job, c):
    p = json.loads(job["payload"])
    return q.fill((q.HERE / "prompts" / "pass_triaje_v1.txt").read_text(encoding="utf-8"),
                  HEAD_SHA=q.git("rev-parse", "--short", "origin/main"), FALLOS=json.dumps(p["fallos"], ensure_ascii=False)[:24000], ITEM=p["item"])


def ingest(q, c, job, data):
    p = json.loads(job["payload"]); n = 0
    for g in data.get("grupos", []):
        ids = [int(x) for x in g.get("propuestas", []) if str(x).isdigit()]
        grupo = f"{p['item']}#{g.get('causa_raiz', '')[:60]}"
        guardar(c, q.now(), grupo, g.get("causa_raiz", "?"), g.get("clase", ""), ids, [p["item"]], g.get("evidencia", ""),
                g.get("reproduccion", ""), g.get("arreglo_propuesto", ""), "gpt")
        for pid in ids:
            if g.get("clase") == "test_roto":
                q.estado_prop(c, pid, "invalida", "triaje GPT: test roto, a reparar y reencolar")
        n += 1
    print(f"  TRIAJE {job['area']}: {n} grupos persistidos")
    return n
