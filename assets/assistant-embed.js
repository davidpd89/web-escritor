import { assistantContextStarters, normalizeWidgetPath } from "/assets/assistant-widget-core.mjs";

const params = new URLSearchParams(location.search);
const from = normalizeWidgetPath(params.get("from") || "/");
const starters = assistantContextStarters(from);
const buttons = [...document.querySelectorAll("[data-assistant-example]")];
const query = document.querySelector("[data-assistant-query]");

function compactLabel(value) {
  const text = String(value || "");
  if (/manecillas/i.test(text) && /de qué trata/i.test(text)) return "Sobre Las manecillas";
  if (/samuel/i.test(text) && /de qué trata/i.test(text)) return "Sobre Samuel";
  if (/noveris/i.test(text)) return "¿Qué es Noveris?";
  if (/fragmento|capítulo/i.test(text)) return /samuel/i.test(text) ? "Leer el capítulo 1" : "Leer un fragmento";
  if (/cuándo se publica/i.test(text)) return "Fecha de publicación";
  if (/herramientas/i.test(text)) return "Herramientas para escritores";
  if (/editoriales/i.test(text)) return "Buscar editoriales";
  if (/convocatorias/i.test(text)) return "Ver convocatorias";
  if (/kit de prensa/i.test(text)) return "Kit de prensa";
  if (/eventos|firmas/i.test(text)) return "Eventos y firmas";
  if (/contactar/i.test(text)) return "Contactar con David";
  if (/qué libros/i.test(text)) return "¿Qué libros hay?";
  if (/qué puedo encontrar/i.test(text)) return "¿Qué puedo encontrar?";
  return text.length > 34 ? `${text.slice(0, 31).trim()}…` : text;
}

buttons.forEach((button, index) => {
  const value = starters[index] || starters[0];
  button.dataset.assistantExample = value;
  button.textContent = compactLabel(value);
});

addEventListener("message", (event) => {
  if (event.origin !== location.origin || event.source !== parent) return;
  if (event.data?.type === "assistant:focus") query?.focus({ preventScroll: true });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || parent === window) return;
  event.preventDefault();
  parent.postMessage({ type: "assistant:close" }, location.origin);
});

if (parent !== window) parent.postMessage({ type: "assistant:ready" }, location.origin);
