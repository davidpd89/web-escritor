"""MW-0080: los enlaces principales de la cabecera no anuncian un menú emergente; el botón que controla el submenú ya lo hace con aria-expanded/aria-controls."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for ruta in ("index.html", "assets/v1-editorial-interior-v4.js", "scripts/build-site-shell.py"):
    texto = (ROOT / ruta).read_text(encoding="utf-8")
    enlaces = re.findall(r"<a [^>]*data-territory=[^>]*>", texto)
    assert enlaces or ruta == "assets/v1-editorial-interior-v4.js" or ruta.endswith(".py"), f"{ruta}: no se encontraron enlaces de territorio"
    malos = [e for e in enlaces if "aria-haspopup" in e]
    assert not malos, f"{ruta}: enlaces con aria-haspopup (un enlace navega, no abre un menú): {malos[:2]}"

html = (ROOT / "index.html").read_text(encoding="utf-8")
botones = re.findall(r'<button[^>]*class="masthead-nav__submenu-trigger"[^>]*>', html)
assert botones and all('aria-expanded="false"' in b and "aria-controls=" in b for b in botones), "los botones de submenú conservan aria-expanded y aria-controls"
print(f"PASS MW-0080: {len(botones)} botones de submenú con estado propio y ningún enlace con aria-haspopup")
