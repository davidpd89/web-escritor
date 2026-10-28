"""informe: ESTADO-MEJORAS-WEB.bat. Solo lectura de la base del laboratorio: expedientes por fase, cola, SHA y URL de runs, gasto Claude, errores.
Equivalente de qa_gpt.cmd_status + qa_lote.bloque_estado (scripts/qa-gpt @ fe131c8c) sobre el esquema propio; no abre ni escribe nada del QA original."""
import datetime as dt, json

import claude_cli

GRUPOS = [("Investigados (esperan a Claude)", ("investigado",)),
          ("Descartados por GPT (sin codigo)", ("descartado_gpt",)),
          ("Descartados por Claude / duplicados / manual", ("descartado_claude", "duplicado", "descartado_manual", "evidencia_insuficiente")),
          ("En desarrollo (GPT)", ("aprobado", "desarrollando")),
          ("Parche listo (esperan revision de Claude)", ("parche_listo",)),
          ("Preparados (esperan EJECUTAR)", ("preparado",)),
          ("Validando en local", ("validando",)),
          ("Validados en local (en cola para Actions)", ("validado",)),
          ("En ejecucion en Actions", ("en_actions",)),
          ("Finalizados OK en Actions", ("remoto_ok",)),
          ("Finalizados con fallo (parche/test)", ("remoto_fallo", "fallo_local", "parche_rechazado", "fallo_desarrollo")),
          ("Infraestructura / revision humana / Claude caido", ("remoto_infra", "revision_humana", "claude_fallo")),
          ("PR hija en borrador", ("pr_borrador",)),
          ("INTEGRADAS en la rama de laboratorio (visibles en la vista previa)", ("integrado",))]


def texto(q, completo=False):
    c = q.db()
    try: return _texto(q, c, completo)
    finally: c.close()  # en Windows una conexion abierta impide borrar/mover la carpeta de estado


def _texto(q, c, completo):
    L = []
    n = lambda sql, *a: c.execute(sql, a).fetchone()[0]
    svc = q.leer_servicio()
    w, ac, sup = q.Lock("worker").dueno(), q.Lock("actions").dueno(), q.Lock("supervisor").dueno()
    L += [f"LABORATORIO DE MEJORAS WEB  ({q.now()})",
          f"Investigador: {'EN MARCHA pid ' + str(w) if w else 'parado'}"
          + (f" | estado {svc.get('estado')} | tarea {svc.get('tarea')}" if w else f" | ultimo estado {svc.get('estado', '-')}")
          + (f" | hasta {svc['hasta']}" if svc.get("hasta") else ""),
          f"Ejecutor de Actions: {'EN MARCHA pid ' + str(ac) if ac else 'parado'} | supervisor: {'pid ' + str(sup) if sup else 'no'}",
          f"Aislado del QA: CDP {q.CFG['gpt']['puerto_cdp']} | estado {q.STATE} | ramas {q.CFG['prefijo_rama']}* -> {q.CFG['rama_base']} | main intocable"]
    if svc.get("ultimo_error"): L.append(f"ULTIMO ERROR: {svc['ultimo_error'][:200]}")
    integ = q.CFG.get("integracion", {}); url = (q.CFG.get("preview") or {}).get("url")
    L.append(f"Integracion automatica en {q.CFG['rama_base']}: {integ.get('modo', 'manual')} ({'tras validar en Actions' if integ.get('exigir_actions', True) else 'tras validar en local'}) | vista previa: {url or 'sin configurar'}")
    L += ["", "Expedientes (fase actual, cada uno cuenta una vez):"]
    por = dict(c.execute("SELECT estado, COUNT(*) FROM expedientes GROUP BY estado").fetchall())
    cubiertos = set()
    for nombre, es in GRUPOS:
        k = sum(por.get(e, 0) for e in es); cubiertos.update(es)
        L.append(f"  - {nombre}: {k}")
    otros = {e: k for e, k in por.items() if e not in cubiertos}
    if otros: L.append("  - Otros: " + ", ".join(f"{e} {k}" for e, k in otros.items()))
    L.append(f"  Total expedientes: {sum(por.values())}")
    # actividad reciente: lo que ha ido pasando (para ver que el sistema trabaja)
    ev = c.execute("SELECT h.fecha, h.exp, h.estado, h.detalle, e.titulo FROM historial h LEFT JOIN expedientes e ON e.id=h.exp ORDER BY h.rowid DESC LIMIT ?", (30 if completo else 10,)).fetchall()
    L += ["", f"Actividad reciente (ultimos {len(ev)} movimientos):"]
    for r in ev: L.append(f"  {r['fecha'][5:16].replace('T', ' ')}  {r['exp']} -> {r['estado']}" + (f"  [{(r['titulo'] or '')[:50]}]" if r["titulo"] else ""))
    if not ev: L.append("  (ninguna todavia)")
    # rotacion
    pares = n("SELECT COUNT(*) FROM pares"); vueltas = c.execute("SELECT MIN(veces) FROM pares").fetchone()[0] if pares else 0
    L += ["", f"Descubrimiento: {n('SELECT COALESCE(SUM(veces),0) FROM pares')} rondas hechas | pares area x lente tocados {pares} | vuelta completa n.{(vueltas or 0) + 1} (no se agota: cada vuelta reordena)"]
    # jobs / GPT
    # errores VIVOS: de investigacion, o de desarrollo de un expediente que sigue en fallo_desarrollo (los de expedientes ya recuperados/resueltos son historial)
    vivos_err = "estado='error' AND (tipo='I' OR area IN (SELECT id FROM expedientes WHERE estado='fallo_desarrollo'))"
    jp = dict(c.execute("SELECT estado, COUNT(*) FROM jobs GROUP BY estado").fetchall()); jp["error"] = n(f"SELECT COUNT(*) FROM jobs WHERE {vivos_err}")
    L += [f"Cola GPT: pendientes {jp.get('pendiente', 0)} | en curso {jp.get('en_curso', 0)} | hechos {jp.get('hecho', 0)} | en ERROR {jp.get('error', 0)} | consultas hoy {n('SELECT COUNT(*) FROM peticiones WHERE fecha=?', q.today())}"]
    for r in c.execute(f"SELECT clave, error FROM jobs WHERE {vivos_err} ORDER BY id DESC LIMIT 5"): L.append(f"    ERROR job {r['clave']}: {(r['error'] or '')[:130]}")
    for r in c.execute("SELECT clave, chat_id, error FROM jobs WHERE estado='pendiente' AND chat_id IS NOT NULL AND fase='generando'"): L.append(f"    reanudable: {r['clave']} chat {r['chat_id'][:8]}")
    # Claude
    cl = claude_cli.resumen_consumo(c); hoy = claude_cli.gasto_hoy(c, q.today()); tope = q.CFG["claude"].get("max_usd_dia")
    L += [f"Claude: {cl['llamadas']} consultas ({cl['ok']} ok) | {cl['usd']} USD en total | hoy {round(hoy, 3)} USD" + (f" de {tope} USD" if tope else "") + f" | {cl['tok_entrada']} tok entrada / {cl['tok_salida']} salida | {q.CFG['claude']['modelo']}"]
    for r in c.execute("SELECT fecha, clave, error FROM claude_llamadas WHERE ok=0 ORDER BY id DESC LIMIT 3"): L.append(f"    error Claude {r['fecha']} {r['clave']}: {(r['error'] or '')[:110]}")
    # cola
    cola = c.execute("SELECT * FROM cola ORDER BY creado DESC").fetchall()
    L += ["", f"Cola de mejoras validadas ({len(cola)}):"]
    for it in cola[:(None if completo else 12)]:
        runs = json.loads(it["runs"] or "{}")
        ur = [f"#{k} run {v['id']} {v.get('conclusion') or v.get('status', '')} {v['url']}" for k, v in sorted(runs.items())]
        L.append(f"  - {it['rama']} @ {it['sha'][:12]} [{it['estado']}] {(it['detalle'] or '')[:100]}")
        tests = [f"{t['ruta'].split('/')[-1]}:{t['fuente']}={t['clase']}" for t in c.execute("SELECT * FROM cola_tests WHERE clave=?", (it["clave"],))]
        if tests: L.append("      tests: " + ", ".join(tests))
        for u in ur: L.append("      " + u)
    vivos = n("SELECT COUNT(*) FROM cola WHERE estado IN ('enviado','actions_pendiente','actions_ejecutando')")
    L.append(f"  Grupos en GitHub ahora: {vivos}/{q.CFG['actions']['concurrencia']} | envios hoy {n('SELECT COUNT(*) FROM envios WHERE fecha=?', q.today())}/{q.CFG['actions']['max_envios_dia']}")
    # atencion
    L += ["", "Requieren atencion:"]
    atencion = c.execute("SELECT id, estado, titulo, motivo, pr_url FROM expedientes WHERE estado IN ('remoto_infra','revision_humana','claude_fallo','fallo_desarrollo','remoto_fallo','fallo_local','parche_rechazado') ORDER BY rowid DESC LIMIT 8").fetchall()
    for r in atencion: L.append(f"  - {r['id']} [{r['estado']}] {r['titulo'][:60]}: {(r['motivo'] or '')[:110]}")
    if not atencion: L.append("  (nada)")
    ok = c.execute("SELECT id, titulo, rama, sha FROM expedientes WHERE estado='remoto_ok' ORDER BY rowid DESC LIMIT 5").fetchall()
    for r in ok: L.append(f"  LISTO PARA PR: {r['id']} {r['titulo'][:60]} -> python motor\\mw.py pr {r['id']} --confirmar")
    for r in c.execute("SELECT id, pr_url FROM expedientes WHERE pr_url IS NOT NULL ORDER BY rowid DESC LIMIT 5"): L.append(f"  PR: {r['id']} {r['pr_url']}")
    npre = por.get("preparado", 0); tope = q.CFG.get("max_pendientes", 6)
    if w and npre + sum(por.get(e, 0) for e in ("investigado", "aprobado", "desarrollando", "parche_listo")) >= tope:
        L.append(f"  El investigador NO abre investigaciones nuevas: hay {npre} preparado(s) esperando EJECUTAR (tope de expedientes en curso: {tope}).")
    prox = c.execute("SELECT id, titulo FROM expedientes WHERE estado='preparado' ORDER BY rowid LIMIT 1").fetchone()
    L.append(f"Proximo para EJECUTAR: {prox['id'] + ' ' + prox['titulo'][:60] if prox else '(ninguno preparado)'}")
    return "\n".join(L)
