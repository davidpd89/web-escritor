"""Campana determinista (Via A): meta description entre 50 y 200 caracteres. Familia: autores."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGINAS = ["recomendaciones/autores/dk/index.html", "recomendaciones/autores/eva-blanch/index.html", "recomendaciones/autores/ruben-munoz/index.html"]
mal = []
for rel in PAGINAS:
    t = (ROOT / rel).read_text(encoding="utf-8")
    m = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]*content=[\"']([^\"']*)", t, re.I) or re.search(r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]*name=[\"']description", t, re.I)
    n = len(m.group(1).strip()) if m else 0
    if not 50 <= n <= 200: mal.append(f"{rel}: {n} caracteres")
if mal:
    print("FAIL meta description fuera de 50-200 caracteres:\n" + "\n".join(mal)); sys.exit(1)
print(f"PASS: {len(PAGINAS)} paginas con meta description valida")
