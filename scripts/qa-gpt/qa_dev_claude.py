"""Desarrollador Claude: para correcciones aprobadas cuyo parche GPT fallo, Claude edita un worktree desde origin/main y el diff se
convierte al formato de parche buscar/por (literal unico) que ya valida `Pr.preparar` (fail-to-pass, verificadores, alcance).
Nada de lo que escribe Claude llega a main sin pasar por esa validacion, la CI y la revision de lote."""
import difflib
import json
import re
import shutil
from pathlib import Path

import qa_claude
import qa_pr

ESTADOS = ("validacion_fallida", "parche_no_encaja", "descartada")
SISTEMA = ("Eres un desarrollador que corrige un defecto en un sitio web estatico. Trabajas en un checkout de la rama main. Edita SOLO los ficheros "
           "necesarios con la herramienta Edit (cambio minimo, sin refactors, sin tocar tests, workflows, package.json ni scripts/qa-gpt). "
           "El test que reproduce el defecto ya esta en el repo: leelo para saber que debe cumplirse. No ejecutes nada. Cuando termines responde con el JSON del esquema.")
ESQUEMA = {"type": "object", "properties": {"resultado": {"type": "string", "enum": ["corregido", "no_se_puede"]}, "resumen": {"type": "string"}},
           "required": ["resultado", "resumen"], "additionalProperties": False}


def diff_a_parche(antes, despues):
    """{ruta: (texto_antes, texto_despues)} -> parche buscar/por; cada hunk se amplia con lineas de contexto hasta que 'buscar' es unico. None si no se puede."""
    ficheros = []
    for ruta, (a, b) in antes.items():
        la, lb = a.split("\n"), despues[ruta].split("\n")
        reps = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, la, lb, autojunk=False).get_opcodes():
            if tag == "equal": continue
            lo, hi = i1, i2
            while True:
                buscar = "\n".join(la[lo:hi])
                if buscar.strip() and a.count(buscar) == 1: break
                if lo == 0 and hi == len(la): return None
                if lo > 0: lo -= 1
                if hi < len(la): hi += 1
            # el contexto de arriba/abajo que se anyade se repite igual en 'por'
            por = "\n".join(la[lo:i1] + lb[j1:j2] + la[i2:hi])
            reps.append({"buscar": buscar, "por": por})
        if reps: ficheros.append({"ruta": ruta, "reemplazos": reps})
    return {"ficheros": ficheros} if ficheros else None


def elegible(c, maxi=1):
    return c.execute(f"""SELECT * FROM triaje WHERE decision='corregir' AND clase IN ('defecto_web','test_roto') AND COALESCE(pr_estado,'') IN ({','.join('?' * len(ESTADOS))})
        AND NOT EXISTS (SELECT 1 FROM claude_llamadas WHERE clave='dev_claude:'||triaje.id) ORDER BY COALESCE(prioridad,'3'), id LIMIT ?""", (*ESTADOS, maxi)).fetchall()


def desarrollar(q, c, pr, row):
    """-> estado. Reencola la fila a validacion con el parche de Claude, o la deja descartada."""
    clave = f"dev_claude:{row['id']}"
    rama = f"qa-dev/{row['id']}"
    wt = Path(q.STATE) / "pr" / f"qa-dev_{row['id']}"
    try:
        rc, o = pr.git("fetch", "origin", "main", timeout=180)
        if rc: return "fetch_fallo"
        if wt.exists(): pr.limpiar(wt, rama)
        wt.parent.mkdir(parents=True, exist_ok=True)
        if pr.git("worktree", "add", "-B", rama, str(wt), "origin/main")[0]: return "worktree_fallo"
        tests = pr._rutas_tests(c, json.loads(row["propuestas"] or "[]"))
        pr._traer_tests(c, row, wt, tests)
        d = json.loads(row["decision_json"] or "{}") or {}
        entrada = (f"CAUSA RAIZ: {row['causa_raiz']}\nCRITERIO DE ACEPTACION: {d.get('criterio_aceptacion', '')}\nTEST QUE REPRODUCE EL DEFECTO: {', '.join(tests)}\n"
                   f"ARCHIVOS PROBABLES: {', '.join(d.get('archivos') or [])}\nFALLO DEL INTENTO ANTERIOR: {(row['pr_detalle'] or '')[:500]}")
        try: res, _ = qa_claude.llamar(q, c, clave, "desarrollo", SISTEMA, entrada, ESQUEMA, herramientas="Read,Edit,Grep,Glob", cwd=wt, max_turnos=16, esfuerzo="medium", usar_cache=False)
        except qa_claude.ClaudeError as e:
            c.execute("UPDATE triaje SET dev_estado='claude_fallo',pr_detalle=?,actualizado=? WHERE id=?", (str(e)[:300], q.now(), row["id"])); c.commit(); return "claude_fallo"
        if res["resultado"] != "corregido":
            c.execute("UPDATE triaje SET dev_estado='claude_no_puede',pr_detalle=?,actualizado=? WHERE id=?", (res["resumen"][:300], q.now(), row["id"])); c.commit(); return "no_se_puede"
        tocados = [x for x in pr.git("diff", "--name-only", cwd=wt)[1].split() if x not in set(tests)]
        antes, despues = {}, {}
        for r in tocados:
            if qa_pr.ruta_segura(r): return _fallo(q, c, row, f"Claude toco una ruta no permitida: {r}")
            rc, a = pr.git("show", f"origin/main:{r}", cwd=wt)
            if rc: return _fallo(q, c, row, f"fichero nuevo no soportado: {r}")
            antes[r] = a.replace("\r\n", "\n"); despues[r] = (wt / r).read_text(encoding="utf-8").replace("\r\n", "\n")
        parche = diff_a_parche(antes, despues) if antes else None
        if not parche: return _fallo(q, c, row, "el cambio de Claude no se pudo convertir a parche")
        ok, probl, norm = qa_pr.validar_parche(parche, lambda r: antes.get(r))
        if not ok: return _fallo(q, c, row, "parche de Claude invalido: " + "; ".join(probl)[:200])
        c.execute("UPDATE triaje SET parche=?,pr_estado=NULL,pr_detalle=?,dev_estado='claude',actualizado=? WHERE id=?",
                  (json.dumps(norm, ensure_ascii=False), "parche de Claude: " + res["resumen"][:300], q.now(), row["id"])); c.commit()
        return "reencolada"
    finally:
        try: pr.limpiar(wt, rama)
        except qa_pr.Interrumpido: shutil.rmtree(wt, ignore_errors=True)


def _fallo(q, c, row, msg):
    c.execute("UPDATE triaje SET dev_estado='claude_invalido',pr_detalle=?,actualizado=? WHERE id=?", (msg[:300], q.now(), row["id"])); c.commit()
    return "invalido"
