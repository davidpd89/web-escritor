// Peticiones a producción para las auditorías que recorren todo el catálogo (miles de URL).
// GitHub Pages responde 429 cuando se le piden demasiadas seguidas. Si cada hilo reintenta por su
// cuenta, los demás siguen pidiendo y el 429 no se va. Por eso la pausa se comparte en todo el proceso:
// ante un 429 esperan todos los hilos (Retry-After si viene; si no, espera creciente).

const MAX_RETRY_AFTER_MS = 60000;
const MAX_PAUSE_MS = 30000;
let pausedUntil = 0;

export const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

export function isTransientStatus(status) {
  return status === 429 || (status >= 500 && status <= 599);
}

function notePause(retryAfter, attempt) {
  const seconds = Number(retryAfter);
  const pause = Number.isFinite(seconds) && seconds > 0
    ? Math.min(seconds * 1000, MAX_RETRY_AFTER_MS)
    : Math.min(2000 * 2 ** attempt, MAX_PAUSE_MS);
  pausedUntil = Math.max(pausedUntil, Date.now() + pause);
}

// Devuelve {status, headers, body, url}. Con un estado transitorio (429 o 5xx) reintenta hasta `attempts`
// veces y, si no se recupera, devuelve el último para que el script lo informe. Lanza solo si ningún
// intento obtuvo respuesta (timeout o error de red).
// read: 'text' (por defecto), 'buffer' o 'none' (descarta el cuerpo).
export async function fetchWithBackoff(url, init = {}, { attempts = 6, read = 'text', timeoutMs = 20000 } = {}) {
  let last;
  for (let attempt = 0; attempt < attempts; attempt++) {
    const wait = pausedUntil - Date.now();
    if (wait > 0) await sleep(wait);
    try {
      const r = await fetch(url, { ...init, signal: AbortSignal.timeout(timeoutMs) });
      let body = null;
      if (read === 'buffer') body = Buffer.from(await r.arrayBuffer());
      else if (read === 'none') await r.body?.cancel().catch(() => {});
      else body = await r.text();
      last = { status: r.status, headers: r.headers, body, url: r.url };
      if (!isTransientStatus(r.status)) return last;
      if (r.status === 429) notePause(r.headers.get('retry-after'), attempt);
    } catch (e) {
      last = e;
    }
    if (attempt < attempts - 1) await sleep(Math.min(500 * 2 ** attempt, 8000) + Math.random() * 250);
  }
  if (last?.status !== undefined) return last;
  throw last;
}
