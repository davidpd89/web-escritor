import { ASSISTANT_PUBLIC_CONFIG } from "/assets/assistant-config.js";
import { ASSISTANT_COPY } from "/assets/assistant-copy.js";
import {
  PROTOCOL_VERSION,
  QUERY_MIN_LENGTH,
  QUERY_MAX_LENGTH,
  normalizeQuery,
  isSafeInternalPath,
  isValidAssistantResponse,
  formatCitationMarkers,
  rankLocalSources,
  makeSessionId,
} from "/assets/assistant-core.mjs";
import { resolveLocalAnswer } from "/assets/assistant-local-knowledge.mjs";

upgradeStandaloneMarkup();

function makeSendIcon() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", "m5 12 14-7-4 14-3-5-7-2Zm7 2 3-5");
  svg.append(path);
  return svg;
}

function upgradeStandaloneMarkup() {
  const panel = document.querySelector(".assistant-panel");
  if (!panel || panel.querySelector("[data-assistant-log]")) return;

  const oldExamples = [...panel.querySelectorAll("[data-assistant-example]")].map((button) => ({
    query: button.dataset.assistantExample || button.textContent || "",
    label: button.textContent?.trim() || "Pregunta sugerida",
  }));

  const hero = document.querySelector(".tool-hero");
  const heroTitle = hero?.querySelector("h1");
  const heroLead = hero?.querySelector(".tool-hero__lead");
  if (heroTitle) heroTitle.textContent = ASSISTANT_COPY.heroTitle;
  if (heroLead) heroLead.textContent = ASSISTANT_COPY.heroLead;
  document.getElementById("limites-title")?.closest(".v1-section")?.remove();

  panel.classList.remove("assistant-panel");
  panel.classList.add("assistant-chat");
  panel.removeAttribute("aria-labelledby");
  panel.setAttribute("aria-label", ASSISTANT_COPY.chatPanelLabel);

  const chatLog = document.createElement("section");
  chatLog.className = "assistant-chat__log";
  chatLog.setAttribute("role", "log");
  chatLog.setAttribute("aria-live", "polite");
  chatLog.setAttribute("aria-relevant", "additions");
  chatLog.setAttribute("aria-label", ASSISTANT_COPY.chatLogLabel);
  chatLog.dataset.assistantLog = "";

  const welcome = document.createElement("article");
  welcome.className = "assistant-message assistant-message--assistant";
  const welcomeBubble = document.createElement("div");
  welcomeBubble.className = "assistant-message__bubble";
  const welcomeText = document.createElement("p");
  welcomeText.textContent = ASSISTANT_COPY.welcomeMessage;
  welcomeBubble.append(welcomeText);
  welcome.append(welcomeBubble);
  chatLog.append(welcome);

  const starterWrap = document.createElement("div");
  starterWrap.className = "assistant-starters";
  starterWrap.setAttribute("aria-label", "Preguntas sugeridas");
  starterWrap.dataset.assistantStarters = "";
  oldExamples.slice(0, 3).forEach(({ query, label }) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "assistant-example";
    button.dataset.assistantExample = query;
    button.textContent = label;
    starterWrap.append(button);
  });

  const composer = document.createElement("form");
  composer.className = "assistant-composer";
  composer.dataset.assistantForm = "";
  const label = document.createElement("label");
  label.className = "sr-only";
  label.htmlFor = "assistant-query";
  label.textContent = ASSISTANT_COPY.queryLabel;
  const row = document.createElement("div");
  row.className = "assistant-composer__row";
  const textarea = document.createElement("textarea");
  textarea.id = "assistant-query";
  textarea.name = "query";
  textarea.rows = 1;
  textarea.maxLength = QUERY_MAX_LENGTH;
  textarea.required = true;
  textarea.autocomplete = "off";
  textarea.enterKeyHint = "send";
  textarea.placeholder = ASSISTANT_COPY.placeholder;
  textarea.dataset.assistantQuery = "";
  const send = document.createElement("button");
  send.className = "assistant-send";
  send.type = "submit";
  send.dataset.assistantSubmit = "";
  send.setAttribute("aria-label", ASSISTANT_COPY.submitAriaLabel);
  send.title = ASSISTANT_COPY.submitTitle;
  send.append(makeSendIcon());
  const cancel = document.createElement("button");
  cancel.className = "assistant-stop";
  cancel.type = "button";
  cancel.dataset.assistantStop = "";
  cancel.hidden = true;
  cancel.setAttribute("aria-label", ASSISTANT_COPY.stopAriaLabel);
  const stopShape = document.createElement("span");
  stopShape.setAttribute("aria-hidden", "true");
  cancel.append(stopShape);
  row.append(textarea, send, cancel);
  const liveStatus = document.createElement("p");
  liveStatus.className = "assistant-status";
  liveStatus.setAttribute("role", "status");
  liveStatus.setAttribute("aria-live", "polite");
  liveStatus.dataset.assistantStatus = "";
  const turnstile = document.createElement("div");
  turnstile.className = "assistant-turnstile";
  turnstile.dataset.assistantTurnstile = "";
  turnstile.setAttribute("aria-hidden", "true");
  composer.append(label, row, liveStatus, turnstile);

  panel.replaceChildren(chatLog, starterWrap, composer);
  document.querySelector(".assistant-shell")?.classList.add("assistant-shell--ready");
}

const form = document.querySelector("[data-assistant-form]");
const input = document.querySelector("[data-assistant-query]");
const submit = document.querySelector("[data-assistant-submit]");
const stop = document.querySelector("[data-assistant-stop]");
const status = document.querySelector("[data-assistant-status]");
const log = document.querySelector("[data-assistant-log]");
const starters = document.querySelector("[data-assistant-starters]");
const turnstileBox = document.querySelector("[data-assistant-turnstile]");
const examples = [...document.querySelectorAll("[data-assistant-example]")];

let requestSerial = 0;
let activeController = null;
let registryModulePromise;
let configPromise;
let turnstileScriptPromise;
let turnstileWidgetId = null;
let turnstileResolve = null;
let turnstileReject = null;
let localContext = { pending: null, lastIntent: null };

function setStatus(message = "") {
  if (status) status.textContent = message;
}

function getSessionId() {
  const key = "davidporto-assistant-session-v1";
  try {
    let value = sessionStorage.getItem(key);
    if (!value) {
      value = makeSessionId();
      sessionStorage.setItem(key, value);
    }
    return value;
  } catch {
    return makeSessionId();
  }
}

async function getRegistry() {
  if (!registryModulePromise) {
    registryModulePromise = import("/assets/assistant-source-registry.js")
      .then((module) => Array.isArray(module.ASSISTANT_SOURCE_REGISTRY) ? module.ASSISTANT_SOURCE_REGISTRY : [])
      .catch(() => []);
  }
  return registryModulePromise;
}

function normalizeRemoteConfig(data) {
  if (data?.protocol_version !== PROTOCOL_VERSION || data?.ok !== true || data?.enabled !== true) return { enabled: false };
  const sitekey = typeof data.turnstile_site_key === "string" ? data.turnstile_site_key.trim() : "";
  if (!sitekey || sitekey.length > 256) return { enabled: false };
  return { enabled: true, turnstile_site_key: sitekey };
}

async function getRemoteConfig() {
  if (!ASSISTANT_PUBLIC_CONFIG.remoteEnabled || !isSafeInternalPath(ASSISTANT_PUBLIC_CONFIG.assistantUrl) || !isSafeInternalPath(ASSISTANT_PUBLIC_CONFIG.configUrl)) {
    return { enabled: false };
  }
  if (!configPromise) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2500);
    configPromise = fetch(ASSISTANT_PUBLIC_CONFIG.configUrl, { credentials: "same-origin", cache: "no-store", signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then(normalizeRemoteConfig)
      .catch(() => ({ enabled: false }))
      .finally(() => clearTimeout(timer));
  }
  return configPromise;
}

function normalizeLocalResult(item) {
  if (!item || !isSafeInternalPath(item.url)) return null;
  const title = String(item.title || item.url).trim();
  if (!title) return null;
  const excerpt = String(item.plain_excerpt || item.excerpt || item.summary || "").replace(/\s+/g, " ").trim();
  const action = String(item.action || "").replace(/\s+/g, " ").trim();
  return {
    id: String(item.id || item.url),
    url: item.url,
    title: title.slice(0, 180),
    excerpt: excerpt.slice(0, 240),
    action: action.slice(0, 80),
  };
}

async function pagefindFallback(query) {
  try {
    const pagefind = await import("/pagefind/pagefind.js");
    const search = await pagefind.search(query);
    const first = await Promise.all((search.results || []).slice(0, 5).map((item) => item.data()));
    return first.map((item) => normalizeLocalResult({
      id: item.meta?.source_id || item.url,
      url: item.url,
      title: item.meta?.title || item.meta?.source_title || item.url,
      plain_excerpt: item.plain_excerpt || item.sub_results?.[0]?.plain_excerpt || "",
      action: "Abrir página",
    })).filter(Boolean);
  } catch {
    const sources = await getRegistry();
    return rankLocalSources(query, sources).map(normalizeLocalResult).filter(Boolean);
  }
}

function sourcesById(sourceIds, registry) {
  const byId = new Map(registry.map((source) => [source.id, source]));
  return [...new Set(sourceIds || [])]
    .map((id) => normalizeLocalResult(byId.get(id)))
    .filter(Boolean);
}

function createSourceLinks(sources) {
  const safe = (sources || []).filter((source) => isSafeInternalPath(source.url)).slice(0, 4);
  if (!safe.length) return null;
  const nav = document.createElement("nav");
  nav.className = "assistant-message__sources";
  nav.setAttribute("aria-label", safe.length === 1 ? "Fuente" : "Fuentes");
  safe.forEach((source, index) => {
    const link = document.createElement("a");
    link.href = source.url;

    const copy = document.createElement("span");
    copy.className = "assistant-source__copy";
    const title = document.createElement("span");
    title.className = "assistant-source__title";
    title.textContent = safe.length === 1 ? source.title : `${index + 1}. ${source.title}`;
    copy.append(title);
    if (source.excerpt) {
      const excerpt = document.createElement("span");
      excerpt.className = "assistant-source__excerpt";
      excerpt.textContent = source.excerpt;
      copy.append(excerpt);
    }

    const action = document.createElement("span");
    action.className = "assistant-source__action";
    action.textContent = source.action || "Abrir";
    link.append(copy, action);
    nav.append(link);
  });
  return nav;
}

function createSuggestions(suggestions) {
  if (!Array.isArray(suggestions) || !suggestions.length) return null;
  const wrap = document.createElement("div");
  wrap.className = "assistant-message__suggestions";
  suggestions.slice(0, 3).forEach((suggestion) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "assistant-reply-chip";
    button.textContent = suggestion.label;
    button.addEventListener("click", () => submitQuery(suggestion.query));
    wrap.append(button);
  });
  return wrap;
}

function appendMessage(role, text, { sources = [], suggestions = [], pending = false } = {}) {
  if (!log) return null;
  const article = document.createElement("article");
  article.className = `assistant-message assistant-message--${role}`;
  if (pending) article.dataset.pending = "true";

  const bubble = document.createElement("div");
  bubble.className = "assistant-message__bubble";
  const body = document.createElement("p");
  body.textContent = text;
  bubble.append(body);

  const sourceLinks = createSourceLinks(sources);
  if (sourceLinks) bubble.append(sourceLinks);
  const suggestionButtons = createSuggestions(suggestions);
  if (suggestionButtons) bubble.append(suggestionButtons);

  article.append(bubble);
  log.append(article);
  scrollToMessageStart(article);
  return article;
}

function scrollToMessageStart(article) {
  // A long reply (e.g. the "no encontré nada, prueba estas rutas" fallback
  // with several sources) can be taller than the visible viewport, so
  // scrolling to the bottom of the transcript lands the reader past the
  // start of the reply instead of at it. scrollIntoView({block:"start"})
  // handles both layouts this widget runs in: the embedded panel, where
  // the log itself scrolls internally, and the standalone /asistente/
  // page, where the log grows to fit its content and the document is
  // what actually scrolls -- a manual scrollTop tweak only covers the
  // first case.
  article.scrollIntoView({ block: "start", inline: "nearest" });
}

function appendTyping() {
  const node = appendMessage("assistant", "", { pending: true });
  if (!node) return null;
  const bubble = node.querySelector(".assistant-message__bubble");
  bubble?.replaceChildren();
  const dots = document.createElement("span");
  dots.className = "assistant-typing";
  dots.setAttribute("aria-label", "Buscando respuesta");
  for (let index = 0; index < 3; index += 1) dots.append(document.createElement("i"));
  bubble?.append(dots);
  return node;
}

function setBusy(busy) {
  if (submit) submit.disabled = busy;
  if (stop) stop.hidden = !busy;
  form?.setAttribute("aria-busy", busy ? "true" : "false");
}

function hideStarters() {
  if (starters) starters.hidden = true;
}

function resizeComposer() {
  if (!input) return;
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 112)}px`;
}

function loadTurnstileScript() {
  if (globalThis.turnstile) return Promise.resolve();
  if (!turnstileScriptPromise) {
    turnstileScriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-assistant-turnstile-script]');
      if (existing && !globalThis.turnstile) existing.remove();
      const script = document.createElement("script");
      const timeout = setTimeout(() => { script.remove(); reject(new Error("turnstile-script-timeout")); }, 8000);
      const finish = (callback) => (...args) => { clearTimeout(timeout); callback(...args); };
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.dataset.assistantTurnstileScript = "true";
      script.addEventListener("load", finish(resolve), { once: true });
      script.addEventListener("error", finish(() => { script.remove(); reject(new Error("turnstile-script-failed")); }), { once: true });
      document.head.append(script);
    }).catch((error) => { turnstileScriptPromise = null; throw error; });
  }
  return turnstileScriptPromise;
}

async function getTurnstileToken(sitekey) {
  if (!sitekey || !turnstileBox) throw new Error("turnstile-unavailable");
  await loadTurnstileScript();
  if (!globalThis.turnstile) throw new Error("turnstile-unavailable");
  if (turnstileWidgetId === null) {
    turnstileWidgetId = globalThis.turnstile.render(turnstileBox, {
      sitekey,
      appearance: "interaction-only",
      execution: "execute",
      action: "assistant_query",
      language: "es",
      callback(token) { turnstileResolve?.(token); },
      "error-callback"() { turnstileReject?.(new Error("turnstile-failed")); return true; },
      "expired-callback"() { turnstileReject?.(new Error("turnstile-expired")); },
      "timeout-callback"() { turnstileReject?.(new Error("turnstile-timeout")); },
    });
  }
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("turnstile-callback-timeout")), 10000);
    turnstileResolve = (token) => { clearTimeout(timeout); resolve(token); };
    turnstileReject = (error) => { clearTimeout(timeout); reject(error); };
    globalThis.turnstile.execute(turnstileWidgetId);
  }).finally(() => { turnstileResolve = null; turnstileReject = null; });
}

function resetTurnstile() {
  if (turnstileWidgetId !== null && globalThis.turnstile) {
    try { globalThis.turnstile.reset(turnstileWidgetId); } catch {}
  }
}

function cancelCurrentRequest(message = "Respuesta detenida.") {
  requestSerial += 1;
  activeController?.abort();
  activeController = null;
  turnstileReject?.(new DOMException("Aborted", "AbortError"));
  resetTurnstile();
  setBusy(false);
  log?.querySelector('[data-pending="true"]')?.remove();
  setStatus(message);
}

async function renderSearchFallback(query, message = "") {
  let local = [];
  try { local = await pagefindFallback(query); } catch { local = []; }
  if (!local.length) {
    const registry = await getRegistry();
    const stable = sourcesById(["site-map", "works-hub", "tools-hub", "notebook-hub", "press"], registry).slice(0, 3);
    appendMessage(
      "assistant",
      "No encuentro una coincidencia clara en el contenido de la web. Puedes orientarte desde estas rutas o abrir el mapa del sitio.",
      { sources: stable },
    );
    return;
  }
  const fallbackMessage = message || (local.length === 1
    ? "He encontrado una página que encaja con lo que buscas. Empezaría por esta:"
    : "He encontrado varias páginas relacionadas. Empezaría por estas:");
  appendMessage("assistant", fallbackMessage, { sources: local.slice(0, 3) });
}

async function queryRemote(query, config, serial) {
  let turnstileToken;
  try {
    turnstileToken = await getTurnstileToken(config.turnstile_site_key);
  } catch {
    resetTurnstile();
    if (serial === requestSerial) await renderSearchFallback(query);
    return;
  }
  if (serial !== requestSerial) return;

  let sessionId;
  try { sessionId = getSessionId(); } catch {
    await renderSearchFallback(query);
    return;
  }

  const controller = new AbortController();
  activeController = controller;
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(ASSISTANT_PUBLIC_CONFIG.assistantUrl, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ protocol_version: PROTOCOL_VERSION, query, session_id: sessionId, locale: "es", turnstile_token: turnstileToken }),
      signal: controller.signal,
    });
    if (serial !== requestSerial) return;

    if (!response.ok) {
      const message = response.status === 429
        ? "Ahora mismo he llegado al límite de respuestas ampliadas, pero estas páginas pueden ayudarte."
        : "Ahora no puedo ampliar esa respuesta, pero estas páginas pueden ayudarte.";
      await renderSearchFallback(query, message);
      return;
    }

    let payload;
    try { payload = await response.json(); } catch { payload = null; }
    if (!isValidAssistantResponse(payload)) {
      await renderSearchFallback(query);
      return;
    }

    appendMessage("assistant", formatCitationMarkers(payload.answer, payload.sources), { sources: payload.sources });
  } catch (error) {
    if (serial !== requestSerial) return;
    if (error?.name !== "AbortError") await renderSearchFallback(query);
    else appendMessage("assistant", "He tardado demasiado en responder. Prueba de nuevo o abre una de estas páginas relacionadas.", { sources: (await pagefindFallback(query)).slice(0, 3) });
  } finally {
    clearTimeout(timer);
    if (activeController === controller) activeController = null;
    resetTurnstile();
  }
}

async function submitQuery(value) {
  const rawQuery = String(value ?? input?.value ?? "").normalize("NFC").replace(/\s+/g, " ").trim();
  if (rawQuery.length > QUERY_MAX_LENGTH) {
    setStatus(`La pregunta es demasiado larga. Usa un máximo de ${QUERY_MAX_LENGTH} caracteres.`);
    input?.focus();
    return;
  }
  const query = normalizeQuery(rawQuery);
  if (query.length < QUERY_MIN_LENGTH) {
    setStatus("Escribe una pregunta un poco más concreta.");
    input?.focus();
    return;
  }

  activeController?.abort();
  const serial = ++requestSerial;
  setBusy(true);
  setStatus("");
  hideStarters();
  appendMessage("user", query);
  if (input) { input.value = ""; resizeComposer(); }

  try {
    const registry = await getRegistry();
    if (serial !== requestSerial) return;

    const localAnswer = resolveLocalAnswer(query, localContext);
    if (localAnswer) {
      const sources = sourcesById(localAnswer.sourceIds, registry);
      appendMessage("assistant", localAnswer.answer, { sources, suggestions: localAnswer.suggestions });
      localContext = { pending: localAnswer.pending, lastIntent: localAnswer.intent };
      return;
    }
    localContext = { pending: null, lastIntent: null };

    const config = await getRemoteConfig();
    if (serial !== requestSerial) return;
    if (!config.enabled) {
      await renderSearchFallback(query);
      return;
    }

    const typing = appendTyping();
    await queryRemote(query, config, serial);
    typing?.remove();
  } finally {
    if (serial === requestSerial) {
      setBusy(false);
      setStatus("");
      input?.focus({ preventScroll: true });
    }
  }
}

examples.forEach((button) => {
  button.addEventListener("click", () => submitQuery(button.dataset.assistantExample || button.textContent || ""));
});

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  void submitQuery(input?.value || "");
});

stop?.addEventListener("click", () => cancelCurrentRequest());
input?.addEventListener("input", resizeComposer);
input?.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    form?.requestSubmit();
  }
});
resizeComposer();
