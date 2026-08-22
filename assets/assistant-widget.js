import {
  ASSISTANT_WIDGET_HINT_KEY,
  shouldMountAssistantWidget,
} from "/assets/assistant-widget-core.mjs";

const EXPECTED_ORIGIN = location.origin;
const HINT_DELAY_MS = 3600;
const HINT_VISIBLE_MS = 6500;
let sessionStorageUsable = true;

if (shouldMountAssistantWidget(location.pathname) && !document.querySelector("[data-assistant-widget]")) {
  mountAssistantWidget();
}

function safeSessionGet(key) {
  try { return sessionStorage.getItem(key); } catch { sessionStorageUsable = false; return null; }
}

function safeSessionSet(key, value) {
  try { sessionStorage.setItem(key, value); } catch { sessionStorageUsable = false; }
}

function makeSvgIcon(kind) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "currentColor");
  path.setAttribute("stroke-width", "1.8");
  path.setAttribute("stroke-linecap", "round");
  path.setAttribute("stroke-linejoin", "round");
  if (kind === "chat") path.setAttribute("d", "M5 5.5h14v10H9l-4 3v-13Z M8 9h8 M8 12h5");
  else if (kind === "close") path.setAttribute("d", "M7 7l10 10M17 7 7 17");
  else path.setAttribute("d", "M7 17 17 7 M9 7h8v8");
  svg.append(path);
  return svg;
}

function mountAssistantWidget() {
  const root = document.createElement("aside");
  root.className = "assistant-widget";
  root.dataset.assistantWidget = "";
  root.setAttribute("aria-label", "Asistente de la web");

  const panelId = "assistant-widget-panel";
  const titleId = "assistant-widget-title";

  const panel = document.createElement("section");
  panel.className = "assistant-widget__panel";
  panel.id = panelId;
  panel.hidden = true;
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "false");
  panel.setAttribute("aria-labelledby", titleId);

  const header = document.createElement("header");
  header.className = "assistant-widget__header";
  const headingWrap = document.createElement("div");
  const title = document.createElement("strong");
  title.id = titleId;
  title.textContent = "Asistente";
  const subtitle = document.createElement("span");
  subtitle.className = "assistant-widget__subtitle";
  subtitle.textContent = "Pregunta sobre esta web";
  headingWrap.append(title, subtitle);

  const headerActions = document.createElement("div");
  headerActions.className = "assistant-widget__header-actions";
  const fullPage = document.createElement("a");
  fullPage.className = "assistant-widget__icon-action";
  fullPage.href = "/asistente/";
  fullPage.setAttribute("aria-label", "Abrir el asistente en página completa");
  fullPage.title = "Abrir en página completa";
  fullPage.append(makeSvgIcon("external"));
  const close = document.createElement("button");
  close.className = "assistant-widget__icon-action";
  close.type = "button";
  close.setAttribute("aria-label", "Cerrar asistente");
  close.title = "Cerrar";
  close.append(makeSvgIcon("close"));
  headerActions.append(fullPage, close);
  header.append(headingWrap, headerActions);

  const body = document.createElement("div");
  body.className = "assistant-widget__body";
  const loading = document.createElement("p");
  loading.className = "assistant-widget__loading";
  loading.textContent = "Abriendo…";
  body.append(loading);
  panel.append(header, body);

  const hint = document.createElement("button");
  hint.className = "assistant-widget__hint";
  hint.type = "button";
  hint.hidden = true;
  hint.textContent = "¿Buscas algo? Pregúntame";

  const launcher = document.createElement("button");
  launcher.className = "assistant-widget__launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-controls", panelId);
  launcher.setAttribute("aria-expanded", "false");
  launcher.setAttribute("aria-label", "Abrir asistente");
  launcher.title = "Asistente";
  launcher.append(makeSvgIcon("chat"));

  root.append(panel, hint, launcher);
  document.body.append(root);

  let frame = null;
  let frameReady = false;
  let pendingFrameFocus = false;
  let open = false;
  let hintTimer = null;

  function ensureFrame() {
    if (frame) return frame;
    frame = document.createElement("iframe");
    frame.className = "assistant-widget__frame";
    frame.title = "Chat con el asistente de davidportodiaz.com";
    frame.referrerPolicy = "strict-origin-when-cross-origin";
    const from = location.pathname.slice(0, 500);
    frame.src = `/asistente/embed.html?from=${encodeURIComponent(from)}`;
    body.replaceChildren(frame);
    return frame;
  }

  function focusFrameInput() {
    if (!frame?.contentWindow || !frameReady) {
      pendingFrameFocus = true;
      return;
    }
    pendingFrameFocus = false;
    frame.contentWindow.postMessage({ type: "assistant:focus" }, EXPECTED_ORIGIN);
  }

  function hideHint() {
    clearTimeout(hintTimer);
    hintTimer = null;
    hint.hidden = true;
  }

  function openWidget({ focus = true } = {}) {
    hideHint();
    if (open) {
      if (focus) focusFrameInput();
      return;
    }
    ensureFrame();
    open = true;
    panel.hidden = false;
    root.dataset.open = "true";
    launcher.setAttribute("aria-expanded", "true");
    launcher.setAttribute("aria-label", "Cerrar asistente");
    if (focus) focusFrameInput();
  }

  function closeWidget({ restoreFocus = true } = {}) {
    if (!open) return;
    open = false;
    panel.hidden = true;
    delete root.dataset.open;
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-label", "Abrir asistente");
    pendingFrameFocus = false;
    if (restoreFocus) launcher.focus({ preventScroll: true });
  }

  launcher.addEventListener("click", () => open ? closeWidget() : openWidget());
  hint.addEventListener("click", () => openWidget());
  close.addEventListener("click", () => closeWidget());

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && open && document.activeElement !== frame) closeWidget();
  });

  document.addEventListener("click", (event) => {
    const menuLink = event.target.closest?.("[data-assistant-menu-link]");
    if (!menuLink) return;
    event.preventDefault();
    const explore = menuLink.closest("dialog[open]");
    if (explore && typeof explore.close === "function") explore.close();
    setTimeout(() => openWidget(), 0);
  });

  const exploreTrigger = document.querySelector("[data-explore-open]");
  exploreTrigger?.addEventListener("click", () => {
    hideHint();
    if (open) closeWidget({ restoreFocus: false });
  });

  addEventListener("message", (event) => {
    if (!frame?.contentWindow || event.origin !== EXPECTED_ORIGIN || event.source !== frame.contentWindow) return;
    if (event.data?.type === "assistant:ready") {
      frameReady = true;
      if (pendingFrameFocus) focusFrameInput();
    } else if (event.data?.type === "assistant:close") {
      closeWidget();
    }
  });

  function showHintOnce() {
    if (!sessionStorageUsable || safeSessionGet(ASSISTANT_WIDGET_HINT_KEY) || open || document.visibilityState !== "visible" || document.querySelector("dialog[open]")) return;
    safeSessionSet(ASSISTANT_WIDGET_HINT_KEY, "1");
    if (!sessionStorageUsable) return;
    hint.hidden = false;
    hintTimer = setTimeout(hideHint, HINT_VISIBLE_MS);
  }

  if (sessionStorageUsable && !safeSessionGet(ASSISTANT_WIDGET_HINT_KEY)) {
    setTimeout(showHintOnce, HINT_DELAY_MS);
  }
}
