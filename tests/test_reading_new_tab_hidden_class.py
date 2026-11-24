"""The «(otra pestaña)» hint must use a class the catalogue CSS actually hides.

It used `visually-hidden`, defined only in the Atlas stylesheet, so on 949 catalogue pages the hint was shown
and long source links overflowed at 320 px with 200 % text (F.2 text resilience, 24/11/2026).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_new_tab_hint_class_is_hidden_by_loaded_css():
    builder = (ROOT / "scripts" / "build-reading-catalogue.py").read_text(encoding="utf-8")
    cls = re.search(r"NEW_TAB='<span class=\"([^\"]+)\">", builder).group(1)
    page = (ROOT / "recomendaciones" / "index.html").read_text(encoding="utf-8")
    sheets = re.findall(r'<link rel="stylesheet" href="/(assets/[^"?]+)', page)
    css = "".join((ROOT / s).read_text(encoding="utf-8") for s in sheets)
    rule = re.search(r"\." + re.escape(cls) + r"\{([^}]*)\}", css)
    assert rule, f".{cls} is not defined in the stylesheets catalogue pages load: {sheets}"
    assert "position:absolute" in rule.group(1) and "clip" in rule.group(1)
