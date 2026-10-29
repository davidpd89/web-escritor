"""MW-0087: el catálogo de libros recomendados declara su BreadcrumbList (Inicio > Libros recomendados), como ya hacen sus páginas hijas."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
html = (ROOT / "recomendaciones/index.html").read_text(encoding="utf-8")
nodos = []
for bloque in re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
    dato = json.loads(bloque)
    nodos += dato.get("@graph", [dato]) if isinstance(dato, dict) else dato
migas = [n for n in nodos if n.get("@type") == "BreadcrumbList"]
assert len(migas) == 1, f"se esperaba una BreadcrumbList en recomendaciones/index.html, hay {len(migas)}"
items = migas[0]["itemListElement"]
assert [(i["position"], i["name"], i["item"]) for i in items] == [
    (1, "Inicio", "https://davidportodiaz.com/"),
    (2, "Libros recomendados", "https://davidportodiaz.com/recomendaciones/"),
], f"migas incorrectas: {items}"
print("PASS MW-0087: BreadcrumbList Inicio > Libros recomendados en el catálogo")
