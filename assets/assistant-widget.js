import {
  ASSISTANT_WIDGET_AUTO_KEY,
  shouldMountAssistantWidget,
} from "/assets/assistant-widget-core.mjs";

const EXPECTED_ORIGIN = location.origin;
const AUTO_OPEN_DELAY_MS = 1100;
const MAX_AUTO_OPEN_ATTEMPTS = 6;

if (shouldMountAssistantWidget(location.pathname) && !document.querySelector("[data-assistant-widget]")) {
  mountAssistantWidget();
}

function safeSessionGet(key) {
  try { return sessionStorage.getItem(key); } catch { return null; }
}

function safeSessionSet(key, value) {
  try { sessionStorage.setItem(key, value); } catch {}
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
  else if (kind === "minus") path.setAttribute("d", "M6 12h12");
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
  const eyebrow = document.createElement("span");
  eyebrow.className = "assistant-widget__eyebrow";
  eyebrow.textContent = "Asistente";
  const title = document.createElement("strong");
  title.id = titleId;
  title.textContent = "¿Qué necesitas encontrar?";
  headingWrap.append(eyebrow, title);

  const headerActions = document.createElement("div");
  headerActions.className = "assistant-widget__header-actions";
  const fullPage = document.createElement("a");
  fullPage.className = "assistant-widget__icon-action";
  fullPage.href = "/asistente/";
  fullPage.setAttribute("aria-label", "Abrir el asistente en página completa");
  fullPage.title = "Abrir en página completa";
  fullPage.append(makeSvgIcon("external"));
  const minimize = document.createElement("button");
  minimize.className = "assistant-widget__icon-action";
  minimize.type = "button";
  minimize.setAttribute("aria-label", "Minimizar asistente");
  minimize.title = "Minimizar";
  minimize.append(makeSvgIcon("minus"));
  headerActions.append(fullPage, minimize);
  header.append(headingWrap, headerActions);

  const body = document.createElement("div");
  body.className = "assistant-widget__body";
  const loading = document.createElement("p");
  loading.className = "assistant-widget__loading";
  loading.textContent = "Cargando el asistente…";
  body.append(loading);

  panel.append(header, body);

  const launcher = document.createElement("button");
  launcher.className = "assistant-widget__launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-controls", panelId);
  launcher.setAttribute("aria-expanded", "false");
  launcher.setAttribute("aria-label", "Abrir asistente");
  launcher.title = "Asistente";
  launcher.append(makeSvgIcon("chat"));

  root.append(panel, launcher);
  document.body.append(root);

  let frame = null;
  let frameReady = false;
  let pendingFrameFocus = false;
  let open = false;
  let autoOpenAttempt = 0;

  function ensureFrame() {
    if (frame) return frame;
    frame = document.createElement("iframe");
    frame.className = "assistant-widget__frame";
    frame.title = "Chat con el asistente de davidportodiaz.com";
    frame.loading = "eager";
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

  function openWidget({ focus = true, auto = false } = {}) {
    if (open) {
      if (focus) focusFrameInput();
      return;
    }
    ensureFrame();
    open = true;
    panel.hidden = false;
    root.dataset.open = "true";
    launcher.setAttribute("aria-expanded", "true");
    launcher.setAttribute("aria-label", "Minimizar asistente");
    safeSessionSet(ASSISTANT_WIDGET_AUTO_KEY, "1");
    if (focus && !auto) focusFrameInput();
  }

  function minimizeWidget({ restoreFocus = true } = {}) {
    if (!open) return;
    open = false;
    panel.hidden = true;
    delete root.dataset.open;
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-label", "Abrir asistente");
    pendingFrameFocus = false;
    if (restoreFocus) launcher.focus({ preventScroll: true });
  }

  launcher.addEventListener("click", () => {
    if (open) minimizeWidget();
    else openWidget({ focus: true });
  });
  minimize.addEventListener("click", () => minimizeWidget());

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && open && document.activeElement !== frame) {
      minimizeWidget();
    }
  });

  document.addEventListener("click", (event) => {
    const menuLink = event.target.closest?.("[data-assistant-menu-link]");
    if (!menuLink) return;
    event.preventDefault();
    const explore = menuLink.closest("dialog[open]");
    if (explore && typeof explore.close === "function") explore.close();
    setTimeout(() => openWidget({ focus: true }), 0);
  });

  const exploreTrigger = document.querySelector("[data-explore-open]");
  exploreTrigger?.addEventListener("click", () => {
    if (open) minimizeWidget({ restoreFocus: false });
  });

  addEventListener("message", (event) => {
    if (!frame?.contentWindow || event.origin !== EXPECTED_ORIGIN || event.source !== frame.contentWindow) return;
    if (event.data?.type === "assistant:ready") {
      frameReady = true;
      if (pendingFrameFocus) focusFrameInput();
    } else if (event.data?.type === "assistant:close") {
      minimizeWidget();
    }
  });

  function tryAutoOpen() {
    if (safeSessionGet(ASSISTANT_WIDGET_AUTO_KEY) || open) return;
    if (document.visibilityState !== "visible" || document.querySelector("dialog[open]")) {
      autoOpenAttempt += 1;
      if (autoOpenAttempt < MAX_AUTO_OPEN_ATTEMPTS) setTimeout(tryAutoOpen, 1200);
      return;
    }
    openWidget({ focus: false, auto: true });
  }

  if (!safeSessionGet(ASSISTANT_WIDGET_AUTO_KEY)) {
    setTimeout(tryAutoOpen, AUTO_OPEN_DELAY_MS);
  }
}
