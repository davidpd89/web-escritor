// Peticiones a producción para las auditorías que recorren todo el catálogo (miles de URL).
// GitHub Pages responde 429 cuando su origen recibe demasiadas peticiones seguidas. Tres defensas:
// 1. Clave anti-caché común (auditUrl): todas las auditorías de un release piden la misma URL
//    (?__qa_release=<sha>). El primer recorrido va al origen y llena la CDN; los demás se sirven de
//    caché, que sigue siendo de ese release porque la clave cambia con cada uno. Antes cada script
//    usaba su propio parámetro y cada recorrido volvía a golpear el origen (~12.000 peticiones).
// 2. Pausa común: ante un 429 esperan todos los hilos (Retry-After si viene; si no, espera creciente).
// 3. Ritmo adaptativo (AIMD, como TCP): cada 429 duplica la separación mínima entre peticiones del
//    proceso (hasta 1 s) y cada respuesta buena la reduce un poco.

const MAX_RETRY_AFTER_MS = 60000;
const MAX_PAUSE_MS = 30000;
const MAX_GAP_MS = 1000;
let pausedUntil = 0;
let gapMs = 0;
let nextStart = 0;
export const fetchStats = { requests: 0, rateLimited: 0, maxGapMs: 0 };

export const RELEASE_KEY = (process.env.EXPECTED_RELEASE_SHA || '').trim().toLowerCase()
  || process.env.GITHUB_RUN_ID
  || Date.now().toString(36);

export function auditUrl(route, origin) {
  const u = new URL(route, origin);
  u.searchParams.set('__qa_release', RELEASE_KEY);
  return u;
}

export const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

export function isTransientStatus(status) {
  return status === 429 || (status >= 500 && status <= 599);
}

async function waitTurn() {
  const now = Date.now();
  const at = Math.max(now, pausedUntil, nextStart);
  nextStart = at + gapMs;
  if (at > now) await sleep(at - now);
}

function noteRateLimited(retryAfter, attempt) {
  fetchStats.rateLimited++;
  gapMs = Math.min(Math.max(gapMs * 2, 50), MAX_GAP_MS);
  fetchStats.maxGapMs = Math.max(fetchStats.maxGapMs, gapMs);
  const seconds = Number(retryAfter);
  const pause = Number.isFinite(seconds) && seconds > 0
    ? Math.min(seconds * 1000, MAX_RETRY_AFTER_MS)
    : Math.min(2000 * 2 ** attempt, MAX_PAUSE_MS);
  pausedUntil = Math.max(pausedUntil, Date.now() + pause);
}

process.on('exit', () => {
  if (fetchStats.rateLimited) {
    console.log(`production-fetch: ${fetchStats.rateLimited} respuestas 429 en ${fetchStats.requests} peticiones; separación máxima ${fetchStats.maxGapMs} ms`);
  }
});

// Devuelve {status, headers, body, url}. Con un estado transitorio (429 o 5xx) reintenta hasta `attempts`
// veces y, si no se recupera, devuelve el último para que el script lo informe. Lanza solo si ningún
// intento obtuvo respuesta (timeout o error de red).
// read: 'text' (por defecto), 'buffer' o 'none' (descarta el cuerpo).
export async function fetchWithBackoff(url, init = {}, { attempts = 8, read = 'text', timeoutMs = 20000 } = {}) {
  let last;
  for (let attempt = 0; attempt < attempts; attempt++) {
    await waitTurn();
    try {
      fetchStats.requests++;
      const r = await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
      let body = null;
      if (read === 'buffer') body = Buffer.from(await r.arrayBuffer());
      else if (read === 'none') await r.body?.cancel().catch(() => {});
      else body = await r.text();
      last = { status: r.status, headers: r.headers, body, url: r.url };
      if (!isTransientStatus(r.status)) {
        if (gapMs > 0) gapMs = Math.max(0, gapMs - 2);
        return last;
      }
      if (r.status === 429) noteRateLimited(r.headers.get('retry-after'), attempt);
    } catch (e) {
      last = e;
    }
    if (attempt < attempts - 1) await sleep(Math.min(500 * 2 ** attempt, 8000) + Math.random() * 250);
  }
  if (last?.status !== undefined) return last;
  throw last;
}
