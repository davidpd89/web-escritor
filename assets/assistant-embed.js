import { assistantContextStarters, normalizeWidgetPath } from "/assets/assistant-widget-core.mjs";

const params = new URLSearchParams(location.search);
const from = normalizeWidgetPath(params.get("from") || "/");
const starters = assistantContextStarters(from);
const buttons = [...document.querySelectorAll("[data-assistant-example]")];
const query = document.querySelector("[data-assistant-query]");

buttons.forEach((button, index) => {
  const value = starters[index] || starters[0];
  button.dataset.assistantExample = value;
  button.textContent = value;
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
