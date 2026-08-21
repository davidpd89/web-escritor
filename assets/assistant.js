import { ASSISTANT_PUBLIC_CONFIG } from "/assets/assistant-config.js";
import { PROTOCOL_VERSION, QUERY_MIN_LENGTH, QUERY_MAX_LENGTH, normalizeQuery, isSafeInternalPath, isValidAssistantResponse, formatCitationMarkers, rankLocalSources, makeSessionId } from "/assets/assistant-core.mjs";

const form = document.querySelector("[data-assistant-form]");
const input = document.querySelector("[data-assistant-query]");
const submit = document.querySelector("[data-assistant-submit]");
const stop = document.querySelector("[data-assistant-stop]");
const status = document.querySelector("[data-assistant-status]");
const answer = document.querySelector("[data-assistant-answer]");
const sourcesList = document.querySelector("[data-assistant-sources]");
const localBox = document.querySelector("[data-assistant-local]");
const localList = document.querySelector("[data-assistant-local-list]");
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
  return { id: String(item.id || item.url), url: item.url, title: title.slice(0, 180) };
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
    })).filter(Boolean);
  } catch {
    const sources = await getRegistry();
    return rankLocalSources(query, sources).map(normalizeLocalResult).filter(Boolean);
  }
}

function setBusy(busy) {
  submit.disabled = busy;
  if (stop) stop.hidden = !busy;
  form?.setAttribute("aria-busy", busy ? "true" : "false");
}

function clearResult() {
  answer.hidden = true;
  answer.textContent = "";
  sourcesList.replaceChildren();
  localBox.hidden = true;
  localList.replaceChildren();
}

function renderSources(sources) {
  const safe = sources.filter((source) => isSafeInternalPath(source.url));
  sourcesList.replaceChildren(...safe.map((source) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = source.url;
    link.textContent = source.title;
    li.append(link);
    return li;
  }));
}

async function renderLocalSuggestions(query, message) {
  status.textContent = message;
  let local = [];
  try { local = await pagefindFallback(query); } catch { local = []; }
  if (!local.length) {
    localBox.hidden = true;
    return;
  }
  localBox.hidden = false;
  localList.replaceChildren(...local.map((source) => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = source.url;
    a.textContent = source.title;
    li.append(a);
    return li;
  }));
}

function loadTurnstileScript() {
  if (globalThis.turnstile) return Promise.resolve();
  if (!turnstileScriptPromise) {
    turnstileScriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-assistant-turnstile-script]');
      if (existing && !globalThis.turnstile) existing.remove();

      const script = document.createElement("script");
      const timeout = setTimeout(() => {
        script.remove();
        reject(new Error("turnstile-script-timeout"));
      }, 8000);
      const finish = (callback) => (...args) => {
        clearTimeout(timeout);
        callback(...args);
      };
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.dataset.assistantTurnstileScript = "true";
      script.addEventListener("load", finish(resolve), { once: true });
      script.addEventListener("error", finish(() => {
        script.remove();
        reject(new Error("turnstile-script-failed"));
      }), { once: true });
      document.head.append(script);
    }).catch((error) => {
      turnstileScriptPromise = null;
      throw error;
    });
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
  }).finally(() => {
    turnstileResolve = null;
    turnstileReject = null;
  });
}

function resetTurnstile() {
  if (turnstileWidgetId !== null && globalThis.turnstile) {
    try { globalThis.turnstile.reset(turnstileWidgetId); } catch {}
  }
}

function cancelCurrentRequest(message = "Búsqueda detenida. Los resultados locales siguen disponibles.") {
  requestSerial += 1;
  activeController?.abort();
  activeController = null;
  turnstileReject?.(new DOMException("Aborted", "AbortError"));
  resetTurnstile();
  setBusy(false);
  status.textContent = message;
}

examples.forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.assistantExample || "";
    input.focus();
  });
});
stop?.addEventListener("click", () => cancelCurrentRequest());

void getRemoteConfig();

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const rawQuery = String(input.value ?? "").normalize("NFC").replace(/\s+/g, " ").trim();
  if (rawQuery.length > QUERY_MAX_LENGTH) {
    status.textContent = `La pregunta no puede superar ${QUERY_MAX_LENGTH} caracteres.`;
    input.focus();
    return;
  }
  const query = normalizeQuery(rawQuery);
  if (query.length < QUERY_MIN_LENGTH) {
    status.textContent = "Escribe una pregunta un poco más concreta.";
    input.focus();
    return;
  }

  activeController?.abort();
  clearResult();
  const serial = ++requestSerial;
  setBusy(true);
  await renderLocalSuggestions(query, "Buscando páginas relacionadas…");
  if (serial !== requestSerial) return;

  try {
    const config = await getRemoteConfig();
    if (!config.enabled) {
      status.textContent = localBox.hidden ? "El asistente remoto está desactivado; prueba con otra búsqueda local." : "Te dejo los resultados disponibles en la web.";
      return;
    }

    status.textContent = "Preparando una respuesta basada en la web…";
    let turnstileToken;
    try {
      turnstileToken = await getTurnstileToken(config.turnstile_site_key);
    } catch {
      resetTurnstile();
      if (serial !== requestSerial) return;
      status.textContent = "No se pudo completar la verificación antiabuso. Los resultados locales siguen disponibles.";
      return;
    }
    if (serial !== requestSerial) return;

    let sessionId;
    try { sessionId = getSessionId(); } catch {
      status.textContent = "Este navegador no permite crear una sesión segura. Los resultados locales siguen disponibles.";
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
        body: JSON.stringify({
          protocol_version: PROTOCOL_VERSION,
          query,
          session_id: sessionId,
          locale: "es",
          turnstile_token: turnstileToken,
        }),
        signal: controller.signal,
      });

      if (serial !== requestSerial) return;
      if (response.status === 429) {
        status.textContent = "Se ha alcanzado el límite temporal del asistente. Los resultados locales siguen disponibles.";
        return;
      }
      if (!response.ok) {
        status.textContent = "La respuesta con IA no está disponible ahora. Los resultados locales siguen funcionando.";
        return;
      }

      let payload;
      try { payload = await response.json(); } catch { payload = null; }
      if (!isValidAssistantResponse(payload)) {
        status.textContent = "La respuesta remota no pasó la validación. Los resultados locales siguen disponibles.";
        return;
      }

      answer.textContent = formatCitationMarkers(payload.answer, payload.sources);
      answer.hidden = false;
      renderSources(payload.sources);
      status.textContent = payload.abstained ? "No hay evidencia suficiente para responder con seguridad." : "Respuesta basada en páginas públicas de esta web.";
    } catch (error) {
      if (serial !== requestSerial) return;
      status.textContent = error?.name === "AbortError" ? "La respuesta tardó demasiado. Los resultados locales siguen disponibles." : "No hay conexión con la respuesta remota. Los resultados locales siguen disponibles.";
    } finally {
      clearTimeout(timer);
      if (activeController === controller) activeController = null;
      resetTurnstile();
    }
  } finally {
    if (serial === requestSerial) setBusy(false);
  }
});
