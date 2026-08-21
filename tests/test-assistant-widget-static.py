#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

def need(condition, message):
    if not condition:
        errors.append(message)

widget = (ROOT / "assets/assistant-widget.js").read_text(encoding="utf-8")
widget_core = (ROOT / "assets/assistant-widget-core.mjs").read_text(encoding="utf-8")
widget_css = (ROOT / "assets/assistant-widget.css").read_text(encoding="utf-8")
embed = (ROOT / "asistente/embed.html").read_text(encoding="utf-8")
embed_client = (ROOT / "assets/assistant-embed.js").read_text(encoding="utf-8")
shell = (ROOT / "assets/v1-shell.js").read_text(encoding="utf-8")

need("import('/assets/assistant-widget.js')" in shell, "V1 shell must lazy-load the assistant widget")
need('/assets/assistant-widget.css' in shell, "V1 shell must load widget styles")
need('data-assistant-menu-link' in shell and "href = '/asistente/'" in shell, "Explore must expose the assistant as a real fallback link")
need("asistente: ['Asistente'" in shell, "Explore preview copy for assistant missing")
need("requestIdleCallback" in shell, "widget must be loaded off the critical render path")
need('/^\\/asistente(?:\\/|$)/' in shell, "full assistant/embed routes must not recursively mount widget")

need('aria-controls' in widget and 'aria-expanded' in widget, "launcher disclosure semantics missing")
need('role", "dialog"' in widget and 'aria-modal", "false"' in widget, "widget must be a non-modal dialog")
need('frame.src = `/asistente/embed.html?from=' in widget, "widget iframe must be same-origin assistant embed")
need('event.origin !== EXPECTED_ORIGIN' in widget and 'event.source !== frame.contentWindow' in widget, "postMessage must validate both origin and source window")
need('ASSISTANT_WIDGET_AUTO_KEY' in widget and 'AUTO_OPEN_DELAY_MS' in widget, "auto-open-once session contract missing")
need('focus: false, auto: true' in widget, "automatic opening must not steal focus")
need('data-assistant-menu-link' in widget and 'event.preventDefault()' in widget, "menu entry must open the widget progressively")
need('innerHTML' not in widget, "widget must construct DOM without innerHTML")
need('location.pathname' in widget and 'location.search' not in widget, "widget context must use pathname only and drop query-string tracking data")

need('ASSISTANT_WIDGET_AUTO_KEY' in widget_core, "widget session key missing")
need('shouldMountAssistantWidget' in widget_core, "widget mount guard missing")
need('assistantContextStarters' in widget_core, "contextual starter helper missing")
need('/asistente' in widget_core, "assistant routes must be excluded by core helper")

need('content="noindex,nofollow"' in embed, "embed document must never be indexed")
need('data-assistant-turnstile' in embed, "embed must keep the anti-abuse control")
need('/assets/assistant.js' in embed and '/assets/assistant-embed.js' in embed, "embed must reuse the hardened assistant client")
need(embed.count('data-assistant-example=') == 3, "embed must expose exactly three starter questions")
need('target="_top"' in embed and 'href="/asistente/"' in embed, "embed must offer a full-page escape hatch")
need('event.origin !== location.origin' in embed_client and 'event.source !== parent' in embed_client, "embed message listener must verify its parent")
need('assistant:close' in embed_client and 'assistant:ready' in embed_client and 'assistant:focus' in embed_client, "embed/widget message protocol incomplete")

need('position:fixed' in widget_css and 'right:max(' in widget_css and 'bottom:max(' in widget_css, "launcher must be fixed bottom-right with safe-area support")
need('@media(max-width:640px)' in widget_css and '76dvh' in widget_css, "mobile bottom-sheet sizing missing")
need('@media(prefers-reduced-motion:reduce)' in widget_css, "reduced-motion fallback missing")
need('@media print' in widget_css and 'display:none!important' in widget_css, "widget must be hidden when printing")
need('focus-visible' in widget_css, "keyboard focus styling missing")

coverage = [
    "index.html",
    "autor.html",
    "prensa.html",
    "eventos.html",
    "libros/index.html",
    "cuaderno/index.html",
    "herramientas/index.html",
    "las-manecillas-del-recuerdo/index.html",
]
for relative in coverage:
    path = ROOT / relative
    if path.exists():
        text = path.read_text(encoding="utf-8")
        need("v1-shell.js" in text, f"{relative}: representative public page does not load V1 shell, so global assistant would be missing")

if errors:
    print("Assistant widget static contract FAILED:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)
print("Assistant widget static contract: OK")
