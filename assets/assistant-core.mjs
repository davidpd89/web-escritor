export const PROTOCOL_VERSION = 1;
export const QUERY_MAX_LENGTH = 500;

export function normalizeQuery(value) {
  return String(value ?? "").normalize("NFC").replace(/\s+/g, " ").trim().slice(0, QUERY_MAX_LENGTH);
}

export function isValidAssistantResponse(payload) {
  if (!payload || payload.protocol_version !== PROTOCOL_VERSION) return false;
  if (payload.ok !== true) return false;
  if (typeof payload.answer !== "string" || !payload.answer.trim()) return false;
  if (!Array.isArray(payload.sources)) return false;
  return payload.sources.every((source) =>
    source && typeof source.id === "string" && typeof source.url === "string" && source.url.startsWith("/") && typeof source.title === "string"
  );
}

export function rankLocalSources(query, sources, limit = 5) {
  const q = normalizeQuery(query).toLocaleLowerCase("es");
  if (!q) return [];
  const terms = [...new Set(q.split(/[^\p{L}\p{N}]+/u).filter((term) => term.length > 1))];
  return sources
    .filter((source) => source.visibility === "public")
    .map((source) => {
      const haystack = [source.title, source.territory, ...(source.keywords || [])].join(" ").toLocaleLowerCase("es");
      let score = haystack.includes(q) ? 20 : 0;
      for (const term of terms) {
        if (source.title.toLocaleLowerCase("es").includes(term)) score += 5;
        if ((source.keywords || []).some((keyword) => keyword.toLocaleLowerCase("es").includes(term))) score += 3;
        if (haystack.includes(term)) score += 1;
      }
      score -= Number(source.priority || 3) * 0.1;
      return { source, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.source.title.localeCompare(b.source.title, "es"))
    .slice(0, limit)
    .map((entry) => entry.source);
}

export function makeSessionId(cryptoObject = globalThis.crypto) {
  if (cryptoObject?.randomUUID) return cryptoObject.randomUUID();
  const bytes = new Uint8Array(16);
  cryptoObject.getRandomValues(bytes);
  return [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
}
