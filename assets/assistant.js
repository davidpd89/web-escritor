import { PROTOCOL_VERSION, normalizeQuery, isValidAssistantResponse, rankLocalSources, makeSessionId } from "/assets/assistant-core.mjs";

const form = document.querySelector("[data-assistant-form]");
const input = document.querySelector("[data-assistant-query]");
const submit = document.querySelector("[data-assistant-submit]");
const status = document.querySelector("[data-assistant-status]");
const answer = document.querySelector("[data-assistant-answer]");
const sourcesList = document.querySelector("[data-assistant-sources]");
const localBox = document.querySelector("[data-assistant-local]");
const localList = document.querySelector("[data-assistant-local-list]");

let requestSerial = 0;
let registryPromise;

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
  if (!registryPromise) {
    registryPromise = fetch("/data/assistant-source-registry.json", { credentials: "same-origin", cache: "force-cache" })
      .then((response) => {
        if (!response.ok) throw new Error("registry-unavailable");
        return response.json();
      })
      .then((data) => Array.isArray(data.sources) ? data.sources : []);
  }
  return registryPromise;
}

async function pagefindFallback(query) {
  try {
    const pagefind = await import("/pagefind/pagefind.js");
    const search = await pagefind.search(query);
    const first = await Promise.all((search.results || []).slice(0, 5).map((item) => item.data()));
    return first.map((item) => ({
      id: item.meta?.source_id || item.url,
      url: item.url,
      title: item.meta?.title || item.meta?.source_title || item.url,
    }));
  } catch {
    const sources = await getRegistry();
    return rankLocalSources(query, sources);
  }
}

function setBusy(busy) {
  submit.disabled = busy;
  input.setAttribute("aria-busy", busy ? "true" : "false");
}

function clearResult() {
  answer.hidden = true;
  answer.textContent = "";
  sourcesList.replaceChildren();
  localBox.hidden = true;
  localList.replaceChildren();
}

function renderSources(sources) {
  sourcesList.replaceChildren(...sources.map((source) => {
    const li = document.createElement("li");
    const link = document.createElement("a");
    link.href = source.url;
    link.textContent = source.title;
    li.append(link);
    return li;
  }));
}

async function renderLocalFallback(query, reason) {
  const local = await pagefindFallback(query);
  status.textContent = reason;
  if (!local.length) return;
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

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = normalizeQuery(input.value);
  if (query.length < 2) {
    status.textContent = "Escribe una pregunta un poco más concreta.";
    input.focus();
    return;
  }

  clearResult();
  const serial = ++requestSerial;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 9000);
  setBusy(true);
  status.textContent = "Buscando en la web…";

  try {
    const response = await fetch("/api/assistant", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ protocol_version: PROTOCOL_VERSION, query, session_id: getSessionId(), locale: "es" }),
      signal: controller.signal,
    });

    if (serial !== requestSerial) return;
    if (response.status === 429) {
      await renderLocalFallback(query, "Se ha alcanzado el límite temporal del asistente. Te dejo resultados locales.");
      return;
    }
    if (!response.ok) {
      await renderLocalFallback(query, "El asistente no está disponible ahora. La búsqueda local sigue funcionando.");
      return;
    }

    const payload = await response.json();
    if (!isValidAssistantResponse(payload)) {
      await renderLocalFallback(query, "La respuesta remota no pasó la validación. Te dejo resultados locales.");
      return;
    }

    answer.textContent = payload.answer;
    answer.hidden = false;
    renderSources(payload.sources);
    status.textContent = payload.abstained ? "No hay evidencia suficiente para responder con seguridad." : "Respuesta basada en páginas públicas de esta web.";
  } catch (error) {
    if (serial !== requestSerial) return;
    await renderLocalFallback(query, error?.name === "AbortError" ? "La respuesta tardó demasiado. Te dejo resultados locales." : "No hay conexión con el asistente. Te dejo resultados locales.");
  } finally {
    clearTimeout(timer);
    if (serial === requestSerial) setBusy(false);
  }
});
