"""Utilidades de las pruebas: repo git temporal con la rama base del laboratorio y un `mw` aislado (estado, repo y config propios por prueba)."""
import copy, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

MOTOR = Path(__file__).resolve().parents[1] / "motor"
sys.path.insert(0, str(MOTOR))
os.environ.setdefault("MEJORAS_WEB_STATE", tempfile.mkdtemp(prefix="mw-state-"))
import mw  # noqa: E402

HTML = "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\"><title>Sitio</title></head><body><header><nav>menu</nav></header><main><h1>Hola</h1><p>texto uno</p></main></body></html>\n"
CSS = "body { margin: 0; }\n.hero { color: #111; }\n"


def git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], capture_output=True, text=True, check=True).stdout.strip()


def crear_repo(base):
    repo = Path(base) / "repo"; repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    (repo / "index.html").write_text(HTML, encoding="utf-8")
    (repo / "styles.css").write_text(CSS, encoding="utf-8")
    (repo / "tests").mkdir(); (repo / "tests" / "existente.py").write_text("print('ok')\n", encoding="utf-8")
    git(repo, "add", "-A"); git(repo, "commit", "-q", "-m", "base")
    git(repo, "update-ref", "refs/remotes/origin/lab/mejoras-web-20261024", "HEAD")  # la rama base del laboratorio, sin remoto real
    return repo


class Caso(unittest.TestCase):
    """Cada prueba: tmp con repo + STATE propio; mw apunta ahi; CFG restaurada al terminar."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.repo = crear_repo(self.tmp.name)
        self._o = (mw.REPO, mw.STATE, copy.deepcopy(mw.CFG))
        mw.REPO = self.repo; mw.STATE = Path(self.tmp.name) / "estado"
        mw.CFG["claude"]["max_usd_dia"] = 100
        for f in ("stop", "pause"): (mw.STATE / f).unlink(missing_ok=True)
        import investigar, actions
        self.inv, self.act = investigar, actions
        investigar.ASK = investigar.CLAUDE_HOOK = None; investigar.PISTAS = lambda a, e: []
        actions.AUTORIZADO = False
        self.addCleanup(self._restaurar)
        self.c = mw.db(); self.addCleanup(self.c.close)

    def _restaurar(self):
        mw.REPO, mw.STATE = self._o[0], self._o[1]
        mw.CFG.clear(); mw.CFG.update(self._o[2])
        self.inv.ASK = self.inv.CLAUDE_HOOK = self.inv.PISTAS = None; self.act.AUTORIZADO = False

    # ---- fabricas de datos ----
    def investigacion(self, **kw):
        d = {"descartar": False, "titulo": "Enlace para saltar al contenido principal",
             "necesidad": "Los lectores que navegan con teclado deben tabular por todo el menu antes de llegar al texto de cada pagina.",
             "estado_sitio": {"archivos_leidos": ["index.html"], "observacion": "La cabecera no tiene enlace de salto y el main no tiene id enfocable."},
             "fuentes": [{"url": "https://www.w3.org/WAI/WCAG22/Techniques/general/G1", "titulo": "WCAG G1: bypass blocks", "fecha": "2025-01-01", "afirma": "Un enlace al inicio permite saltar bloques repetidos."}],
             "propuesta": "Anadir un enlace skip-link como primer elemento del body que apunte a #contenido y dar id al main, con estilos visibles al enfocar.",
             "archivos_objetivo": ["index.html", "styles.css"], "criterio_aceptacion": "El primer elemento enfocable de index.html es un enlace a #contenido y existe un elemento con ese id.",
             "pruebas_aceptacion": ["index.html tiene skip-link"], "riesgos": "Ninguno relevante para el resto de paginas.", "alternativas": ["A", "B"], "tamano": "pequeno"}
        d.update(kw); return d

    def propuesta_gpt(self, **kw):
        test = ("import re, sys\nhtml = open('index.html', encoding='utf-8').read()\n"
                "assert re.search(r'<a[^>]+href=\"#contenido\"', html), 'falta skip-link'\nassert 'id=\"contenido\"' in html, 'falta id'\nprint('ok')\n")
        d = {"resuelto_en_base": False, "explicacion": "skip link", "confianza": "alta",
             "parche": {"ficheros": [{"ruta": "index.html", "reemplazos": [
                 {"buscar": "<body><header>", "por": "<body><a class=\"skip\" href=\"#contenido\">Saltar al contenido</a><header>"},
                 {"buscar": "<main>", "por": "<main id=\"contenido\">"}]}]},
             "pruebas": [{"ruta": "tests/mejoras-web/mw-0001-skip.py", "contenido": test}], "codigo_externo": []}
        d.update(kw); return d

    def job(self, tipo="I", payload=None, area="accesibilidad|1"):
        self.c.execute("INSERT INTO jobs(clave,tipo,area,estado,payload,creado,actualizado) VALUES(?,?,?,?,?,?,?)",
                       (f"{tipo}:{area}:{self.c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]}", tipo, area, "pendiente", json.dumps(payload or {"area": "accesibilidad", "lente": 1, "epoca": 0}), mw.now(), mw.now()))
        self.c.commit(); return self.c.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 1").fetchone()

    def exp_preparado(self, eid="MW-0001", estado="preparado", prop=None):
        """Expediente ya revisado por Claude con un parche valido guardado."""
        from parches import validar_propuesta
        ok, pr, norm = validar_propuesta(prop or self.propuesta_gpt(), self.inv.leer_base)
        assert ok, pr
        d = self.investigacion()
        self.c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,estado,datos,contraste,parche,revision,rama,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (eid, "accesibilidad", "1", d["titulo"], d["necesidad"], estado, json.dumps(d), json.dumps({"decision": "aprobar", "criterio_aceptacion": d["criterio_aceptacion"]}),
                        json.dumps(norm), json.dumps({"decision": "aprobar", "motivo": "ok", "riesgo": "bajo", "procedencia": []}), mw.CFG["prefijo_rama"] + eid.lower(), mw.now(), mw.now()))
        self.c.commit(); return eid
