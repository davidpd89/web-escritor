"""El orden de fichas hermanas (pie Anterior/Siguiente): contenido coherente y al día."""
import importlib.util
import json
import re
from pathlib import Path

from contrato_libros import incumplen

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("page_order", ROOT / "scripts/build-page-order.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

text = m.OUTPUT.read_text(encoding="utf-8")
assert text == m.render(m.build()), "assets/page-order.generated.js no está al día"
data = json.loads(text[len(m.PREFIX):-len(m.SUFFIX)])
prefixes = [f["prefix"] for f in data["families"]]
assert len(prefixes) == len(set(prefixes)) and "/editoriales/" in prefixes and "/atlas-literario/" in prefixes
malos = {}
for family in data["families"]:
    hrefs = [href for href, _ in family["items"]]
    assert len(hrefs) == len(set(hrefs)) >= 2, family["prefix"]
    for href, title in family["items"]:
        assert href.startswith(family["prefix"]) and href.endswith("/"), href
        if not (title and len(title) < 200 and (ROOT / href.strip("/") / "index.html").is_file()):
            malos[href] = f"título de {len(title or '')} caracteres o ficha inexistente"
    assert family["hub"]["href"].startswith("/") and family["hub"]["label"]
libros = {f"/recomendaciones/libros/{b['slug']}/": b["id"]
          for b in json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))["libros"]}
incumplen("ficha hermana con título y página", {libros[h]: m_ for h, m_ in malos.items() if h in libros})
assert not malos, malos
# Orden alfabético estable y sin acentos en editoriales
titles = [t for _, t in next(f for f in data["families"] if f["prefix"] == "/editoriales/")["items"]]
assert [m.sort_key(t) for t in titles] == sorted(m.sort_key(t) for t in titles)
# El script de la página debe permitir el CSP de las fichas: scripts propios, sin fetch
assert not re.search(r"fetch\(['\"]/assets/page-order", (ROOT / "assets/v1-editorial-interior-v4.js").read_text(encoding="utf-8"))
# Clase de fallo: un título largo (ficha académica de 200+ caracteres) se acota en el rótulo, nunca tumba el gate
largo = "Análisis de la percepción del profesorado sobre el uso de recursos digitales para la prevención de conductas disruptivas en un centro de educación especial en la etapa de educación básica obligatoria. " * 2
corto = m.shorten(largo)
assert len(corto) <= m.MAX_TITLE + 1 and corto.endswith("…") and " " + corto[-2] != "  ", corto
assert m.shorten("Título corto") == "Título corto"
print("PASS: page order")
