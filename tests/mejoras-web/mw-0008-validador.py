from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
script = (ROOT / "scripts/check-navigation-coverage.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/content-index-check.yml").read_text(encoding="utf-8")

assert (
    'HTML_SITEMAP_PATH = ROOT / "mapa-del-sitio" / "index.html"'
) in script, "MW-0008: el validador no declara el mapa HTML"

start_marker = "    # El mapa HTML no debe promocionar artículos excluidos de ambos índices."
end_marker = "    # Relationships must resolve to canonical IDs."
assert start_marker in script, "MW-0008: falta la protección del mapa HTML"
assert end_marker in script, "MW-0008: falta el marcador de continuidad del validador"
start = script.index(start_marker)
end = script.index(end_marker, start)
guard = script[start:end]

required = [
    'HTML_SITEMAP_PATH.read_text(encoding="utf-8")',
    're.search(r"<main\\b[\\s\\S]*?</main>", sitemap_html, re.I)',
    'if not main_match:',
    'for href in hrefs_in(main_match.group(0)):',
    'by_url.get(normalize_public_url(href))',
    'item.get("type") == "article"',
    'item.get("sitemap") is False',
    'item.get("searchIndex") is False',
    'errors.append(',
    'excluded article linked:',
    'sitemap=false, searchIndex=false',
]
for fragment in required:
    assert fragment in guard, (
        "MW-0008: falta una condición o diagnóstico del control de exclusión: "
        + fragment
    )

assert 'if errors:' in script and 'return 1' in script, (
    "MW-0008: las infracciones deben provocar un código de salida distinto de cero"
)
assert 'run: python scripts/check-navigation-coverage.py' in workflow, (
    "MW-0008: el workflow de índices debe ejecutar el validador ampliado"
)

print("PASS MW-0008: protección general en el validador y reutilización del workflow existente")
