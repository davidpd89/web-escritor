"""MW-0036: todos los artículos del Cuaderno declaran Article.image, igual a su og:image."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paginas = sorted((ROOT / "cuaderno").glob("*/index.html"))
revisadas = 0
for pagina in paginas:
    html = pagina.read_text(encoding="utf-8")
    nodos = []
    for bloque in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
        dato = json.loads(bloque)
        nodos += dato.get("@graph", [dato]) if isinstance(dato, dict) else dato
    articulos = [n for n in nodos if n.get("@type") == "Article"]
    if not articulos:
        continue
    og = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    assert og, f"{pagina.relative_to(ROOT)}: sin og:image"
    for art in articulos:
        imagen = art.get("image")
        imagen = imagen if isinstance(imagen, str) else (imagen or [None])[0]
        imagen = imagen.get("url") if isinstance(imagen, dict) else imagen
        assert imagen, f"{pagina.relative_to(ROOT)}: Article sin image"
        assert imagen.rsplit(".", 1)[0] == og.group(1).rsplit(".", 1)[0], f"{pagina.relative_to(ROOT)}: image {imagen} no corresponde a og:image {og.group(1)}"
        revisadas += 1
assert revisadas >= 5, f"se esperaban al menos 5 artículos, hay {revisadas}"
print(f"PASS MW-0036: {revisadas} artículos del Cuaderno con Article.image coherente con og:image")
