import { ASSISTANT_PUBLIC_CONFIG } from "./assistant-config.js";

export const PROTOCOL_VERSION = ASSISTANT_PUBLIC_CONFIG.protocolVersion;
export const QUERY_MIN_LENGTH = ASSISTANT_PUBLIC_CONFIG.queryMinLength;
export const QUERY_MAX_LENGTH = ASSISTANT_PUBLIC_CONFIG.queryMaxLength;

export function normalizeQuery(value) {
  return String(value ?? "").normalize("NFC").replace(/\s+/g, " ").trim().slice(0, QUERY_MAX_LENGTH);
}

export function foldQuery(value) {
  return normalizeQuery(value)
    .normalize("NFD")
    .replace(/\p{M}+/gu, "")
    .toLocaleLowerCase("es");
}

export function isSafeInternalPath(value) {
  if (typeof value !== "string" || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return false;
  if (/[\u0000-\u001F\u007F]/u.test(value)) return false;
  try {
    const parsed = new URL(value, "https://davidportodiaz.com");
    return parsed.origin === "https://davidportodiaz.com" && parsed.pathname === value.split(/[?#]/, 1)[0] && !parsed.pathname.split("/").includes("..");
  } catch {
    return false;
  }
}

export function isValidAssistantResponse(payload) {
  if (!payload || payload.protocol_version !== PROTOCOL_VERSION || payload.ok !== true) return false;
  if (typeof payload.answer !== "string" || !payload.answer.trim() || payload.answer.length > 6000) return false;
  if (typeof payload.abstained !== "boolean" || !Array.isArray(payload.sources) || payload.sources.length > 8) return false;
  if (!payload.abstained && payload.sources.length === 0) return false;

  const ids = new Set();
  for (const source of payload.sources) {
    if (!source || typeof source.id !== "string" || !/^[a-z0-9][a-z0-9-]{0,80}$/i.test(source.id) || ids.has(source.id)) return false;
    if (!isSafeInternalPath(source.url) || typeof source.title !== "string" || !source.title.trim() || source.title.length > 180) return false;
    ids.add(source.id);
  }

  const markers = [...payload.answer.matchAll(/\[([a-z0-9][a-z0-9-]{0,80})\]/gi)].map((match) => match[1]);
  if (!payload.abstained && markers.length === 0) return false;
  if (markers.some((id) => !ids.has(id))) return false;
  return true;
}

export function formatCitationMarkers(value, sources) {
  let text = String(value ?? "");
  const indexById = new Map((Array.isArray(sources) ? sources : []).map((source, index) => [source.id, index + 1]));
  return text.replace(/\[([a-z0-9][a-z0-9-]{0,80})\]/gi, (match, id) => {
    const index = indexById.get(id);
    return index ? `[${index}]` : match;
  });
}

export function rankLocalSources(query, sources, limit = 5) {
  const q = foldQuery(query);
  if (!q) return [];
  const terms = [...new Set(q.split(/[^\p{L}\p{N}]+/u).filter((term) => term.length > 1))];
  return sources
    .filter((source) => source.visibility === "public" && isSafeInternalPath(source.url))
    .map((source) => {
      const title = String(source.title || "");
      const keywords = Array.isArray(source.keywords) ? source.keywords.map(String) : [];
      const titleFolded = foldQuery(title);
      const keywordFolded = keywords.map(foldQuery);
      const haystack = [titleFolded, foldQuery(source.territory), ...keywordFolded].join(" ");
      let score = haystack.includes(q) ? 20 : 0;
      for (const term of terms) {
        if (titleFolded.includes(term)) score += 5;
        if (keywordFolded.some((keyword) => keyword.includes(term))) score += 3;
        if (haystack.includes(term)) score += 1;
      }
      score -= Number(source.priority || 3) * 0.1;
      return { source, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || String(a.source.title).localeCompare(String(b.source.title), "es"))
    .slice(0, limit)
    .map((entry) => entry.source);
}

export function makeSessionId(cryptoObject = globalThis.crypto) {
  if (!cryptoObject?.getRandomValues) throw new Error("secure-random-unavailable");
  if (cryptoObject.randomUUID) return cryptoObject.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoObject.getRandomValues(bytes);
  return [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
}
