"""El orden de fichas hermanas (pie Anterior/Siguiente): contenido coherente y al día."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("page_order", ROOT / "scripts/build-page-order.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

text = m.OUTPUT.read_text(encoding="utf-8")
assert text == m.render(m.build()), "assets/page-order.generated.js no está al día"
data = json.loads(text[len(m.PREFIX):-len(m.SUFFIX)])
prefixes = [f["prefix"] for f in data["families"]]
assert len(prefixes) == len(set(prefixes)) and "/editoriales/" in prefixes and "/atlas-literario/" in prefixes
for family in data["families"]:
    hrefs = [href for href, _ in family["items"]]
    assert len(hrefs) == len(set(hrefs)) >= 2, family["prefix"]
    for href, title in family["items"]:
        assert href.startswith(family["prefix"]) and href.endswith("/"), href
        assert title and len(title) < 200, href
        assert (ROOT / href.strip("/") / "index.html").is_file(), href
    assert family["hub"]["href"].startswith("/") and family["hub"]["label"]
# Orden alfabético estable y sin acentos en editoriales
titles = [t for _, t in next(f for f in data["families"] if f["prefix"] == "/editoriales/")["items"]]
assert [m.sort_key(t) for t in titles] == sorted(m.sort_key(t) for t in titles)
# El script de la página debe permitir el CSP de las fichas: scripts propios, sin fetch
assert not re.search(r"fetch\(['\"]/assets/page-order", (ROOT / "assets/v1-editorial-interior-v4.js").read_text(encoding="utf-8"))
print("PASS: page order")
