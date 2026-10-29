"""MW-0104: las colecciones temáticas del Cuaderno declaran el RSS del Cuaderno para el descubrimiento automático."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FEED = "https://davidportodiaz.com/cuaderno/feed.xml"
paginas = sorted((ROOT / "cuaderno" / "temas").glob("**/index.html"))
assert len(paginas) >= 2, "se esperaban el índice de temas y al menos una colección"
for pagina in paginas:
    head = re.search(r"<head>[\s\S]*?</head>", pagina.read_text(encoding="utf-8"), re.I).group(0)
    rss = re.findall(r'<link\b[^>]*type="application/rss\+xml"[^>]*>', head)
    assert len(rss) == 1, f"{pagina.relative_to(ROOT)}: se esperaba un único RSS alternate, hay {len(rss)}"
    assert f'href="{FEED}"' in rss[0] and 'rel="alternate"' in rss[0], f"{pagina.relative_to(ROOT)}: RSS alternate incorrecto: {rss[0]}"
print(f"PASS MW-0104: {len(paginas)} páginas de temas anuncian el RSS del Cuaderno")
