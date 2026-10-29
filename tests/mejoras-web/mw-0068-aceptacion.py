"""MW-0068: la portada y las fichas de las novelas atribuyen el enlace al autor en Mastodon (fediverse:creator), como el resto de páginas del autor."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALOR = "@davidportodiaz@mastodon.social"
for ruta in ("index.html", "libros/samuel-entre-mundos/index.html", "las-manecillas-del-recuerdo/index.html", "libros/index.html"):
    html = (ROOT / ruta).read_text(encoding="utf-8")
    metas = re.findall(r'<meta name="fediverse:creator" content="([^"]+)"', html)
    assert metas == [VALOR], f"{ruta}: se esperaba un único fediverse:creator {VALOR}, hay {metas}"
print("PASS MW-0068: fediverse:creator en la portada y las fichas de las novelas")
