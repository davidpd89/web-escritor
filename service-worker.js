const CACHE_VERSION = "david-porto-v2026-05-07-2";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

const APP_SHELL = [
  "/",
  "/index.html",
  "/offline.html",
  "/manifest.json",
  "/styles.css",
  "/script.js",
  "/autor.html",
  "/prensa.html",
  "/eventos.html",
  "/premios.html",
  "/privacidad.html",
  "/libros/samuel-entre-mundos/",
  "/universo/noveris/",
  "/fragmento/",
  "/las-manecillas-del-recuerdo/",
  "/llms.txt",
  "/llms-full.txt",
  "/assets/logo-david-porto-diaz-escritor.webp",
  "/assets/david-porto-favicon.png",
  "/assets/david-porto-favicon.webp",
  "/assets/mapa-noveris-ciudad-fantasia-urban-lore.avif",
  "/assets/david-porto-diaz-escritor-fantasia-madrid-autor.avif",
  "/assets/portada-novela-samuel-entre-mundos-fantasia-david-porto.avif",
  "/assets/portada-novela-samuel-entre-mundos-fantasia-david-porto.webp",
  "/assets/diagrama-tecnico-canalizadores-magia-noveris.avif",
  "/assets/fonts/cg-normal-latin.woff2",
  "/assets/fonts/inter-normal-latin.woff2"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
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
    cache.put(request, response.clone());
    return response;
  } catch {
    return (await cache.match(request)) || (await caches.match("/offline.html"));
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  const cache = await caches.open(STATIC_CACHE);
  cache.put(request, response.clone());
  return response;
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(PAGE_CACHE);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);

  return cached || fetchPromise;
}
