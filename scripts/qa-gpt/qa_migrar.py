"""qa_migrar: migracion controlada de `estado.db` (normalizar `como_ejecutar` de propuestas historicas a `pasos` validados).

Garantias: copia previa (sqlite backup API), validacion de esquema, una sola transaccion con rollback ante cualquier fallo,
idempotente (lo ya normalizado se omite), no toca propuestas ya ejecutadas/publicadas ni con lote asociado, no borra nada
(deja `como_ejecutar_original` y un evento por propuesta) y comprueba al final que los contadores no cambiaron.
"""
import hashlib, json, sqlite3
from pathlib import Path
import qa_cobertura as cob

INTOCABLES = ("ejecutada", "publicada")
ESQUEMA = {"propuestas": {"id", "datos", "estado", "huella_conductual"}, "eventos": {"fecha", "entidad", "ident", "estado", "nota"}}


def _esquema_ok(c):
    falta = []
    for t, cols in ESQUEMA.items():
        have = {r[1] for r in c.execute(f"PRAGMA table_info({t})")}
        if not cols <= have: falta.append(f"{t}: faltan {sorted(cols - have)}")
    return falta


def _contadores(c):
    por_estado = {r[0]: r[1] for r in c.execute("SELECT estado,COUNT(*) FROM propuestas GROUP BY estado")}
    quitar = ("pasos", "como_ejecutar", "como_ejecutar_original")
    resto = [(r[0], hashlib.sha1(json.dumps({k: v for k, v in json.loads(r[1] or "{}").items() if k not in quitar}, sort_keys=True).encode()).hexdigest())
             for r in c.execute("SELECT id,datos FROM propuestas ORDER BY id")]
    return {"total": sum(por_estado.values()), "por_estado": por_estado, "resto_datos": resto,
            "otras_columnas": [tuple(r) for r in c.execute("SELECT id,huella,area,titulo,estado,veredicto,rama,huella_conductual,fuente_sha FROM propuestas ORDER BY id")],
            "eventos": c.execute("SELECT COUNT(*) FROM eventos").fetchone()[0]}


def candidatas(c):
    out = []
    for r in c.execute("SELECT id,estado,datos FROM propuestas ORDER BY id"):
        if r["estado"] in INTOCABLES: continue
        try: d = json.loads(r["datos"])
        except (TypeError, ValueError): continue
        if not isinstance(d, dict) or "pasos" in d or not isinstance(d.get("ficheros_nuevos"), list): continue
        if not any(isinstance(f, dict) and Path(f.get("ruta", "")).suffix in cob._TEST_EXT for f in d["ficheros_nuevos"]): continue
        if c.execute("SELECT 1 FROM sqlite_master WHERE name='lote_items'").fetchone() and any(
                str(r["id"]) in json.loads(i[0]) for i in c.execute("SELECT propuestas FROM lote_items")): continue  # ya capturada por un lote
        out.append((r["id"], d))
    return out


def migrar(db_path, backup_dir, ahora, aplicar=True):
    """-> dict con resultado. `aplicar=False` es un ensayo (no escribe nada, ni siquiera copia)."""
    src = sqlite3.connect(db_path, timeout=60); src.row_factory = sqlite3.Row
    res = {"backup": None, "migradas": [], "omitidas": 0, "ok": False, "error": None}
    try:
        if (f := _esquema_ok(src)): res["error"] = "esquema incompatible: " + "; ".join(f); return res
        cands = candidatas(src); res["omitidas"] = src.execute("SELECT COUNT(*) FROM propuestas").fetchone()[0] - len(cands)
        if not aplicar or not cands: res["migradas"] = [i for i, _ in cands]; res["ok"] = True; return res
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        dest = Path(backup_dir) / f"estado-pre-migracion-{ahora.replace(':', '').replace('-', '')}.db"
        b = sqlite3.connect(dest); src.backup(b); b.close(); res["backup"] = str(dest)
        antes = _contadores(src)
        src.isolation_level = None; src.execute("BEGIN IMMEDIATE")
        try:
            for pid, d in cands:
                cob.normalizar_comandos(d)
                src.execute("UPDATE propuestas SET datos=? WHERE id=?", (json.dumps(d, ensure_ascii=False), pid))
                src.execute("INSERT INTO eventos VALUES(?,?,?,?,?)", (ahora, "propuesta", pid, "migrada_pasos", "como_ejecutar normalizado a pasos argv (original conservado)"))
            despues = _contadores(src)
            malo = [k for k in ("total", "por_estado", "resto_datos", "otras_columnas") if antes[k] != despues[k]]
            if malo or despues["eventos"] != antes["eventos"] + len(cands): raise RuntimeError(f"los contadores cambiaron ({malo or 'eventos'}): se revierte")
            src.execute("COMMIT")
        except BaseException:
            src.execute("ROLLBACK"); raise
        res["migradas"] = [i for i, _ in cands]; res["ok"] = True
    except Exception as e: res["error"] = str(e)[:300]
    finally: src.close()
    return res
