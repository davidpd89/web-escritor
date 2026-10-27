"""pr_hija: prepara la PR hija EN BORRADOR hacia lab/mejoras-web-20261024 mediante una accion explicita (`mw.py pr ID --confirmar`).

Nunca fusiona, nunca activa auto-merge, nunca apunta a main, nunca cierra ni borra ramas, nunca relanza workflows. Solo `gh pr create --draft` y
`gh pr list` (para no duplicar). Sin --confirmar solo muestra lo que haria.

PROCEDENCIA: el cuerpo estructurado de la PR sigue `qa_pr.cuerpo_pr` y la comprobacion de PR existente `qa_lote.Gh.pr_de_rama`
(scripts/qa-gpt @ fe131c8ce6a663b54ab067ea5bc123318ececbb0); `Gh.pr_crear` del QA apuntaba a main y aqui se limita a la rama base del laboratorio.
"""
import json, re

import mw


class PrError(RuntimeError):
    pass


class GhPr:
    """Fachada minima de `gh pr`; `ejecutar` es inyectable en pruebas."""
    def __init__(self, q, ejecutar=None):
        self.q, self.repo = q, q.CFG["repo"]
        self.ejecutar = ejecutar or self._real

    def _real(self, args):
        r = self.q.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode: raise PrError((r.stderr or r.stdout).strip()[:300])
        return r.stdout

    def de_rama(self, rama):
        """PRs (cualquier estado) cuya cabeza es `rama`: evita duplicar."""
        return json.loads(self.ejecutar(["pr", "list", "-R", self.repo, "--state", "all", "--head", rama, "--json", "number,url,state,baseRefName,isDraft"]) or "[]")

    def abiertas_laboratorio(self):
        rs = json.loads(self.ejecutar(["pr", "list", "-R", self.repo, "--state", "open", "--base", self.q.CFG["rama_base"], "--limit", "100", "--json", "number,headRefName,url"]) or "[]")
        return [r for r in rs if r["headRefName"].startswith(self.q.CFG["prefijo_rama"])]

    def crear_borrador(self, rama, titulo, cuerpo):
        base = self.q.CFG["rama_base"]
        if base in ("main", "master") or not self.q.rama_permitida(rama): raise PrError(f"PR bloqueada: base {base!r} / cabeza {rama!r} no permitidas")
        out = self.ejecutar(["pr", "create", "-R", self.repo, "--base", base, "--head", rama, "--title", titulo, "--body", cuerpo, "--draft"])
        return out.strip().splitlines()[-1]


def cuerpo(q, e, it, cola_tests):
    d = json.loads(e["datos"] or "{}"); cont = json.loads(e["contraste"] or "{}"); rev = json.loads(e["revision"] or "{}"); prop = json.loads(e["parche"] or "{}")
    runs = json.loads(it["runs"] or "{}") if it else {}
    ultimo = runs[max(runs, key=int)] if runs else None
    fuentes = "\n".join(f"- [{f.get('titulo', f['url'])}]({f['url']}) ({f.get('fecha', 's/f')}): {f.get('afirma', '')[:200]}" for f in d.get("fuentes", [])) or "- (sin fuentes)"
    proc = "\n".join(f"- {p['repositorio']} `{p['ruta']}` @ {p['commit'][:12]} (blob {p['blob_sha'][:12]}), licencia {p['licencia']}" + (f"; adaptado: {p['adaptacion']}" if p.get("adaptado") else "") for p in rev.get("procedencia", [])) or "- Sin codigo externo."
    tests = "\n".join(f"- `{t['ruta']}`: local {next((x['clase'] for x in cola_tests if x['ruta'] == t['ruta'] and x['fuente'] == 'local'), '?')}, Actions {next((x['clase'] for x in cola_tests if x['ruta'] == t['ruta'] and x['fuente'] == 'actions'), 'no ejecutado')}" for t in prop.get("pruebas", []))
    return "\n".join([
        f"## Resumen\n{e['titulo']}  \nExpediente `{e['id']}` · area `{e['area']}` · rama base `{q.CFG['rama_base']}` @ `{(e['base_sha'] or '')[:12]}` · candidata `{(e['sha'] or '')[:12]}`",
        f"## Necesidad\n{e['necesidad']}", f"## Estado real del sitio\n{(d.get('estado_sitio') or {}).get('observacion', '')}",
        f"## Cambio\n{d.get('propuesta', '')}\n\nFicheros: " + ", ".join(f"`{x}`" for x in prop.get("tocados", [])),
        f"## Criterio de aceptacion\n{cont.get('criterio_aceptacion') or d.get('criterio_aceptacion', '')}",
        f"## Pruebas\n{tests}", "## Validacion remota\n" + (f"Run: {ultimo['url']} ({ultimo.get('conclusion') or ultimo.get('status')})" if ultimo else "No se ejecuto en Actions (PR preparada con `--solo-local`)."),
        f"## Fuentes\n{fuentes}", f"## Procedencia del codigo externo\n{proc}",
        f"## Revision de Claude\nDecision: {rev.get('decision', '?')} · riesgo {rev.get('riesgo', '?')}\n{rev.get('motivo', '')}\nCoherencia editorial: {rev.get('coherencia_editorial', '-')}",
        f"## Riesgos\n{d.get('riesgos', '')}",
        "## Vista previa\nLocal: `python motor/mw.py vista-previa " + e["id"] + "` (127.0.0.1:8766). Enlace publico de la rama de laboratorio: workflow manual `mejoras-web-preview.yml` (no se activa solo).",
        "> PR en BORRADOR hacia la rama de laboratorio. No se fusiona automaticamente; pasar a main solo cuando David lo ordene."])


def main(q, a, gh=None):
    c = q.db(); e = c.execute("SELECT * FROM expedientes WHERE id=?", (a.id,)).fetchone()
    if not e: print("expediente inexistente"); return 2
    permitidos = ("remoto_ok",) + (("validado",) if a.solo_local else ())
    if e["estado"] not in permitidos:
        print(f"{a.id} esta en '{e['estado']}': solo se prepara PR desde {permitidos}. (--solo-local permite 'validado' sin Actions.)"); return 2
    rama = e["rama"]
    if not q.rama_permitida(rama): print(f"rama {rama!r} no permitida"); return 2
    it = c.execute("SELECT * FROM cola WHERE exp=? AND sha=? ORDER BY rowid DESC LIMIT 1", (a.id, e["sha"])).fetchone()
    if not it: print("la cola no contiene el SHA actual de este expediente: valida primero"); return 2
    if a.solo_local and e["estado"] == "validado" and not a.confirmar: pass
    gh = gh or GhPr(q)
    try:
        previas = [p for p in gh.de_rama(rama) if p["state"] == "OPEN"]
        if previas:
            c.execute("UPDATE expedientes SET pr_url=?, estado='pr_borrador' WHERE id=?", (previas[0]["url"], a.id)); c.commit()
            print(f"Ya existe una PR abierta para {rama}: {previas[0]['url']} (no se crea otra)"); return 0
        tope = q.CFG.get("pr", {}).get("max_abiertas", 2)
        abiertas = gh.abiertas_laboratorio()
        if len(abiertas) >= tope: print(f"Ya hay {len(abiertas)} PR hijas abiertas hacia {q.CFG['rama_base']} (tope {tope}). Revisa/cierra alguna antes."); return 2
        titulo = f"mejoras-web {e['id']}: {e['titulo']}"[:120]
        texto = cuerpo(q, e, it, [dict(r) for r in c.execute("SELECT * FROM cola_tests WHERE clave=?", (it["clave"],))])
        if not a.confirmar:
            print(f"[SIMULACION] Se crearia PR en BORRADOR: {rama} -> {q.CFG['rama_base']}\nTitulo: {titulo}\n\n{texto}\n\nRepite con --confirmar para crearla."); return 0
        if e["estado"] == "validado":  # --solo-local: la rama aun no esta en el remoto
            import actions
            actions.AUTORIZADO = True
            try: g = actions.Gh(q); g.push(e["sha"], rama)
            finally: actions.AUTORIZADO = False
        url = gh.crear_borrador(rama, titulo, texto)
    except PrError as err:
        print(f"ERROR de GitHub: {err}"); return 1
    c.execute("UPDATE expedientes SET pr_url=?, estado='pr_borrador', actualizado=? WHERE id=?", (url, q.now(), a.id))
    c.execute("INSERT INTO historial VALUES(?,?,?,?)", (a.id, q.now(), "pr_borrador", url)); c.commit()
    print(f"PR en borrador creada: {url}\nNo se fusiona sola. Revisa la vista previa antes de integrarla en {q.CFG['rama_base']}."); return 0
