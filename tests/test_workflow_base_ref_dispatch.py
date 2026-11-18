"""18/11: un valor que solo existe en `pull_request` (github.base_ref, pull_request.base.*) llega VACÍO cuando el
workflow se lanza con `workflow_dispatch`, que es como el publicador de la carga nocturna completa los checks de su
rama. broken-links perdía así la regla de #1430 (host externo caído y ya presente en main = aviso) y tumbó el lote 2.

Regla por forma: en todo workflow con `workflow_dispatch`, cada uso de esos valores lleva una alternativa `||` en la
misma expresión, o el workflow figura en TRATA_VACIO con el motivo de por qué el vacío está controlado.
"""
from pathlib import Path
import re
import unittest

RAIZ = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.y*ml"))
EXPR = re.compile(r"\$\{\{([^}]*)\}\}")
SOLO_PR = re.compile(r"\bgithub\.base_ref\b|\bgithub\.event\.pull_request\.base\.")
# Workflows que usan el valor sin `||` porque tratan el vacío explícitamente. Sin entradas muertas.
TRATA_VACIO = {
    "content-parity-manecillas.yml": "qa/manecillas-fragments-nav.mjs aborta si falta la base (fallo ruidoso)",
    "manecillas-fragments-nav-qa.yml": "qa/manecillas-fragments-nav.mjs aborta si falta la base (fallo ruidoso)",
    "findability-browser-qa.yml": "si PR_BASE_SHA está vacío usa origin/implementacion-web-2026",
    "higiene-repo.yml": "fuera de pull_request usa --since=35.days",
    "lighthouse-ci.yml": "${BASE_SHA:-origin/main} y rama explícita por event_name",
    "pa11y-baseline.yml": "${BASE_SHA:-origin/main} y rama explícita por event_name",
    "sitewide-reflow-qa.yml": "${BASE_SHA:-origin/main} y rama explícita por event_name",
    "visual-regression-qa.yml": "el diff solo corre tras comprobar event_name == pull_request",
    "required-merge-gate.yml": "check-no-skip-ci-markers.py solo mira la PR; en dispatch no hay commits de PR",
    "samuel-ecosystem-browser-qa.yml": "sin base omite la comparación literal (solo en PR con fragmento/)",
}


def es_dispatch(texto):
    return re.search(r"^\s*workflow_dispatch\s*:", texto, re.M) is not None


def usos_sin_alternativa(texto):
    return [e.strip() for e in EXPR.findall(texto) if SOLO_PR.search(e) and "||" not in e]


class BaseRefEnDispatch(unittest.TestCase):
    def test_valores_de_pr_tienen_alternativa_en_dispatch(self):
        malos = {}
        for wf in WORKFLOWS:
            texto = wf.read_text(encoding="utf-8")
            if not es_dispatch(texto) or wf.name in TRATA_VACIO:
                continue
            usos = usos_sin_alternativa(texto)
            if usos:
                malos[wf.name] = usos
        self.assertEqual(malos, {}, "valor de pull_request sin alternativa en un workflow despachable; añade `||` o "
                         "documenta en TRATA_VACIO cómo se controla el vacío")

    def test_sin_entradas_muertas(self):
        vivos = {wf.name for wf in WORKFLOWS
                 if es_dispatch(t := wf.read_text(encoding="utf-8")) and usos_sin_alternativa(t)}
        self.assertEqual(set(TRATA_VACIO) - vivos, set())

    def test_broken_links_compara_con_main_en_dispatch(self):
        texto = (RAIZ / ".github/workflows/broken-links.yml").read_text(encoding="utf-8")
        self.assertIn("github.base_ref || (github.ref_name != 'main' && 'main' || '')", texto)


if __name__ == "__main__":
    unittest.main()
