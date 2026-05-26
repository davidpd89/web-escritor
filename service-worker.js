const CACHE_VERSION = "david-porto-v2026-05-26-8";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

// Critical app shell — assets that MUST be cached for offline to work.
// Do NOT include frequently-changing pages (eventos, ferias) here.
const APP_SHELL = [
  "/",
  "/offline.html",
  "/manifest.json",
  "/styles.css",
  "/script.js",
  "/autor.html",
  "/prensa.html",
  "/premios.html",
  "/privacidad.html",
  "/libros/samuel-entre-mundos/",
  "/universo/noveris/",
  "/fragmento/",
  "/las-manecillas-del-recuerdo/",
  "/assets/logo-david-porto-diaz-escritor-176.webp",
  "/assets/david-porto-favicon.png",
  "/assets/mapa-noveris-ciudad-fantasia-urban-lore.avif",
  "/assets/david-porto-autor-700.webp",
  "/assets/david-porto-autor-400.webp",
  "/assets/fonts/cg-normal-latin.woff2",
  "/assets/fonts/inter-normal-latin.woff2",
  "/empieza-aqui/",
  "/aviso-legal.html",
  "/clubes-de-lectura/samuel-entre-mundos/"
];

// Install: cache each asset individually so one failure does not abort the whole install
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(async (cache) => {
      await Promise.allSettled(
        APP_SHELL.map((url) =>
          fetch(url).then((res) => {
            if (!res.ok) throw new Error(`${res.status} ${url}`);
            return cache.put(url, res);
          }).catch((err) => {
            console.warn("[SW] Failed to cache:", err.message);
          })
        )
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => !key.startsWith(CACHE_VERSION))
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirstPage(request));
    return;
  }

  if (url.pathname.startsWith("/assets/") || url.pathname.endsWith(".css") || url.pathname.endsWith(".js")) {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(staleWhileRevalidate(request));
});

async function networkFirstPage(request) {
  const cache = await caches.open(PAGE_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    return (await cache.match(request)) || (await caches.match("/offline.html"));
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, response.clone());
  }
  return response;
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(PAGE_CACHE);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);

  return cached || fetchPromise;
}
