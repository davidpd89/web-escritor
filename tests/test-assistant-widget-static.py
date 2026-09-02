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
client = (ROOT / "assets/assistant.js").read_text(encoding="utf-8")
knowledge = (ROOT / "assets/assistant-local-knowledge.mjs").read_text(encoding="utf-8")
shell = (ROOT / "assets/v1-shell.js").read_text(encoding="utf-8")

need("import('/assets/assistant-widget.js')" in shell, "V1 shell must lazy-load the assistant widget")
need('/assets/assistant-widget.css' in shell, "V1 shell must load widget styles")
need('data-assistant-menu-link' in shell and "href = '/asistente/'" in shell, "Explore must expose the assistant as a real fallback link")
need("asistente: ['Asistente'" in shell, "Explore preview copy for assistant missing")
need("requestIdleCallback" in shell, "widget must be loaded off the critical render path")
need('/^\\/asistente(?:\\/|$)/' in shell, "full assistant/embed routes must not recursively mount widget")
need("frame-src\\s+'none'" in shell, "widget must not mount on pages whose CSP forbids framing")

need('aria-controls' in widget and 'aria-expanded' in widget, "launcher disclosure semantics missing")
need('role", "dialog"' in widget and 'aria-modal", "false"' in widget, "widget must remain a non-modal dialog")
need('frame.src = `/asistente/embed.html?from=' in widget, "widget iframe must stay same-origin")
need('event.origin !== EXPECTED_ORIGIN' in widget and 'event.source !== frame.contentWindow' in widget, "postMessage must validate both origin and source window")
need('AUTO_OPEN_DELAY_MS' not in widget and 'tryAutoOpen' not in widget and 'openWidget({ focus: false' not in widget, "widget must never auto-open")
need('ASSISTANT_WIDGET_HINT_KEY' in widget and 'HINT_DELAY_MS' in widget and 'HINT_VISIBLE_MS' in widget, "one-session non-modal hint contract missing")
need('¿Buscas algo? Pregúntame' in widget, "subtle assistant hint copy missing")
need('sessionStorageUsable' in widget and 'if (!sessionStorageUsable' in widget, "blocked sessionStorage must suppress hint rather than repeat it")
need('ensureFrame();' in widget and 'function openWidget' in widget, "assistant iframe must be instantiated only after explicit opening")
need('data-assistant-menu-link' in widget and 'event.preventDefault()' in widget, "menu entry must open the widget progressively")
need('innerHTML' not in widget, "widget must construct DOM without innerHTML")
need('location.pathname' in widget and 'location.search' not in widget, "widget context must use pathname only and drop tracking query strings")

need('ASSISTANT_WIDGET_HINT_KEY' in widget_core, "widget session hint key missing")
need('ASSISTANT_WIDGET_AUTO_KEY' not in widget_core, "obsolete auto-open session contract must be removed")
need('shouldMountAssistantWidget' in widget_core, "widget mount guard missing")
need('assistantContextStarters' in widget_core, "contextual starter helper missing")
need('/asistente' in widget_core, "assistant routes must be excluded by core helper")

need('content="noindex,nofollow"' in embed, "embed document must never be indexed")
need('data-assistant-log' in embed and 'role="log"' in embed, "embed must expose an actual chat transcript")
need('assistant-composer' in embed and 'data-assistant-query' in embed and 'data-assistant-submit' in embed, "compact chat composer missing")
need('data-assistant-turnstile' in embed, "embed must keep the anti-abuse control mount point")
need('/assets/assistant.js?v=1' in embed and '/assets/assistant-embed.js?v=1' in embed, "embed must reuse the hardened assistant client")
need(embed.count('data-assistant-example=') == 3, "embed must expose exactly three contextual starter questions")
for forbidden in ('asistente remoto', 'respuesta con IA', 'Cloudflare Turnstile', 'repositorio', 'no se guarda una conversación', 'endpoint del propio sitio'):
    need(forbidden.lower() not in embed.lower(), f"embed must not expose internal implementation copy: {forbidden}")
need('event.origin !== location.origin' in embed_client and 'event.source !== parent' in embed_client, "embed message listener must verify its parent")
need('assistant:close' in embed_client and 'assistant:ready' in embed_client and 'assistant:focus' in embed_client, "embed/widget message protocol incomplete")

need('position:fixed' in widget_css and 'right:max(' in widget_css and 'bottom:max(' in widget_css, "launcher must stay fixed bottom-right with safe-area support")
need('width:min(378px' in widget_css and 'height:min(520px' in widget_css, "desktop assistant panel must remain compact")
need('@media(max-width:640px)' in widget_css and '58dvh' in widget_css and '76dvh' not in widget_css, "mobile assistant must be materially smaller than the old 76dvh sheet")
need('width:48px' in widget_css, "mobile launcher should be compact")
need('@media(prefers-reduced-motion:reduce)' in widget_css, "reduced-motion fallback missing")
need('@media print' in widget_css and 'display:none!important' in widget_css, "widget must be hidden when printing")
need('focus-visible' in widget_css, "keyboard focus styling missing")

need('resolveLocalAnswer' in client, "assistant must answer common intents locally before depending on remote AI")
need('appendMessage("user"' in client and 'appendMessage("assistant"' in client, "assistant client must render actual conversation turns")
need('data-assistant-log' in client and 'upgradeStandaloneMarkup' in client, "standalone assistant must be upgraded to the same conversational UI")
need('remote está desactivado' not in client and 'respuesta remota no pasó' not in client and 'verificación antiabuso' not in client, "client must not expose infrastructure/failure jargon to visitors")
need('innerHTML' not in client, "assistant client must build response DOM without innerHTML")
need('fragment-choice' in knowledge and 'mando un manuscrito' in knowledge, "local knowledge must cover ambiguity and core writer flows")

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
    print("Assistant widget/UX static contract FAILED:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)
print("Assistant widget/UX static contract: OK")
