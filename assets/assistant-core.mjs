export const PROTOCOL_VERSION = 1;
export const QUERY_MAX_LENGTH = 500;

export function normalizeQuery(value) {
  return String(value ?? "").normalize("NFC").replace(/\s+/g, " ").trim().slice(0, QUERY_MAX_LENGTH);
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
  return payload.sources.every((source) =>
    source && typeof source.id === "string" && /^[a-z0-9][a-z0-9-]{0,80}$/i.test(source.id) &&
    isSafeInternalPath(source.url) && typeof source.title === "string" && source.title.trim().length > 0 && source.title.length <= 180
  );
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
  const q = normalizeQuery(query).toLocaleLowerCase("es");
  if (!q) return [];
  const terms = [...new Set(q.split(/[^\p{L}\p{N}]+/u).filter((term) => term.length > 1))];
  return sources
    .filter((source) => source.visibility === "public" && isSafeInternalPath(source.url))
    .map((source) => {
      const title = String(source.title || "");
      const keywords = Array.isArray(source.keywords) ? source.keywords.map(String) : [];
      const haystack = [title, source.territory, ...keywords].join(" ").toLocaleLowerCase("es");
      let score = haystack.includes(q) ? 20 : 0;
      for (const term of terms) {
        if (title.toLocaleLowerCase("es").includes(term)) score += 5;
        if (keywords.some((keyword) => keyword.toLocaleLowerCase("es").includes(term))) score += 3;
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
