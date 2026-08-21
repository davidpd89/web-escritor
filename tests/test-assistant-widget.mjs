import assert from "node:assert/strict";
import {
  ASSISTANT_WIDGET_AUTO_KEY,
  normalizeWidgetPath,
  shouldMountAssistantWidget,
  assistantContextStarters,
  isTrustedWidgetMessage,
} from "../assets/assistant-widget-core.mjs";

assert.equal(ASSISTANT_WIDGET_AUTO_KEY, "davidporto-assistant-widget-auto-v1");
assert.equal(normalizeWidgetPath("//libros///samuel-entre-mundos/?x=1"), "/libros/samuel-entre-mundos/");
assert.equal(shouldMountAssistantWidget("/"), true);
assert.equal(shouldMountAssistantWidget("/autor.html"), true);
assert.equal(shouldMountAssistantWidget("/asistente/"), false);
assert.equal(shouldMountAssistantWidget("/asistente/embed.html"), false);
assert.match(assistantContextStarters("/las-manecillas-del-recuerdo/")[0], /manecillas/i);
assert.match(assistantContextStarters("/universo/noveris/")[1], /Noveris/i);
assert.match(assistantContextStarters("/herramientas/")[0], /herramientas/i);
const source = {};
assert.equal(isTrustedWidgetMessage("https://davidportodiaz.com", "https://davidportodiaz.com", source, source), true);
assert.equal(isTrustedWidgetMessage("https://evil.example", "https://davidportodiaz.com", source, source), false);
assert.equal(isTrustedWidgetMessage("https://davidportodiaz.com", "https://davidportodiaz.com", {}, source), false);
console.log("assistant-widget: OK");
