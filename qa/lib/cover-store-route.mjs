// La QA de navegador sobre el dist publicado no depende del host del almacén de portadas.
// El dist lleva las portadas con la URL de GitHub Pages del almacén; con miles de páginas, Pages responde a ratos
// con un error HTML que Chromium bloquea (ERR_BLOCKED_BY_ORB) y la auditoría falla por la red, no por la web.
// `routeCoverStore` intercepta esas URL y las sirve desde una caché compartida, con reintentos y espera creciente.
// Si tras los reintentos la portada no baja, se responde con su error: un fallo real del almacén se sigue viendo.
import { loadCoverStore } from './cover-store-view.mjs';

export function storeOrigins(store = loadCoverStore()) {
  return [store.base, ...(store.extra || [])].filter(Boolean).map(url => { let u = url; while (u.endsWith('/')) u = u.slice(0, -1); return u + '/'; });
}

export function makeCoverFetcher({ fetchImpl = fetch, attempts = 4, delayMs = 500, sleep = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
  const cache = new Map();
  return url => {
    if (!cache.has(url)) {
      const pending = (async () => {
        let last = '';
        for (let i = 0; i < attempts; i += 1) {
          if (i) await sleep(delayMs * 2 ** (i - 1));
          try {
            const response = await fetchImpl(url);
            const type = response.headers.get('content-type') || '';
            if (response.ok && type.startsWith('image/')) {
              return { status: 200, contentType: type, body: Buffer.from(await response.arrayBuffer()) };
            }
            last = `${response.status} ${type}`;
            if (response.status === 404) break;  // no existe: no hay reintento que lo arregle
          } catch (error) {
            last = String(error);
          }
        }
        cache.delete(url);  // un fallo no se queda cacheado para las páginas siguientes
        return { status: 502, contentType: 'text/plain', body: Buffer.from(`almacén de portadas: ${url}: ${last}`) };
      })();
      cache.set(url, pending);
    }
    return cache.get(url);
  };
}

export async function routeCoverStore(context, { store = loadCoverStore(), fetcher = makeCoverFetcher() } = {}) {
  for (const origin of storeOrigins(store)) {
    await context.route(`${origin}**`, async route => {
      const { status, contentType, body } = await fetcher(route.request().url());
      await route.fulfill({ status, contentType, body, headers: { 'access-control-allow-origin': '*' } });
    });
  }
}

// Todos los contextos que abra `browser` sirven las portadas del almacén por la caché (una sola llamada tras launch).
export function withCoverStore(browser, options = {}) {
  const fetcher = options.fetcher || makeCoverFetcher();
  const open = browser.newContext.bind(browser);
  browser.newContext = async (...args) => {
    const context = await open(...args);
    await routeCoverStore(context, { ...options, fetcher });
    return context;
  };
  return browser;
}
