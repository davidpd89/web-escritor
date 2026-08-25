const CACHE_NAMESPACE = "david-porto-pwa";
const CACHE_VERSION = `${CACHE_NAMESPACE}-v8`;
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;
const CURRENT_CACHES = new Set([STATIC_CACHE, PAGE_CACHE]);

// Known cache keys from previous versions of this PWA. Keep this explicit:
// activation must never delete unrelated CacheStorage entries on the origin.
const LEGACY_PWA_CACHES = new Set([
  "david-porto-v2026-08-20-launch-1-static",
  "david-porto-v2026-08-20-launch-1-pages",
  "david-porto-pwa-v2-20260813",
  "david-porto-pwa-v2-20260813-assets"
]);

// Stable offline shell only. Editorial pages remain network-first and are not
// precached. The two fonts are the minimum V1 subset used by offline.html.
const APP_SHELL = [
  "/offline.html",
  "/manifest.json",
  "/favicon.ico",
  "/assets/icon-512.png",
  "/assets/icon-512-maskable.png",
  "/assets/fonts/is-normal-400-latin.woff2",
  "/assets/fonts/mr-normal-400-700-latin.woff2"
];

function offlineResponse() {
  return new Response("Offline", {
    status: 504,
    statusText: "Offline",
    headers: { "Content-Type": "text/plain; charset=utf-8" }
  });
}

async function putIfCacheable(cache, request, response) {
  if (response && response.ok) {
    await cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);
    // Atomic by design: every APP_SHELL entry is contract-tested. If one is
    // missing, keep the previous worker rather than activating a partial shell.
    await cache.addAll(APP_SHELL.map((url) => new Request(url, { cache: "reload" })));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((key) => {
          const obsoleteNamespaced = key.startsWith(`${CACHE_NAMESPACE}-`) && !CURRENT_CACHES.has(key);
          return obsoleteNamespaced || LEGACY_PWA_CACHES.has(key);
        })
        .map((key) => caches.delete(key))
    );
    await self.clients.claim();
  })());
});

function isSameOriginGet(request) {
  if (request.method !== "GET") return false;
  return new URL(request.url).origin === self.location.origin;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (!isSameOriginGet(request)) return;

  const url = new URL(request.url);

  // API responses are never owned by the PWA cache. This includes assistant
  // config/response endpoints and any future same-origin API: let the browser
  // network stack handle them directly so authenticated/dynamic JSON cannot be
  // served stale or copied into PAGE_CACHE.
  if (url.pathname === "/api" || url.pathname.startsWith("/api/")) return;

  if (request.mode === "navigate") {
    event.respondWith(networkFirstPage(request));
    return;
  }

  // Mutable code stays network-first.
  if (url.pathname.endsWith(".css") || url.pathname.endsWith(".js")) {
    event.respondWith(networkFirstStatic(request));
    return;
  }

  // Images and fonts under /assets/ are cache-first.
  if (url.pathname.startsWith("/assets/")) {
    event.respondWith(cacheFirstAsset(request));
    return;
  }

  // Other same-origin GET requests remain stale-while-revalidate.
  event.respondWith(staleWhileRevalidate(event));
});

async function networkFirstPage(request) {
  const pageCache = await caches.open(PAGE_CACHE);
  try {
    const response = await fetch(request);
    await putIfCacheable(pageCache, request, response);
    return response;
  } catch {
    const cached = await pageCache.match(request);
    if (cached) return cached;
    const staticCache = await caches.open(STATIC_CACHE);
    return (await staticCache.match("/offline.html")) || offlineResponse();
  }
}

async function networkFirstStatic(request) {
  const cache = await caches.open(STATIC_CACHE);
  try {
    const response = await fetch(request);
    await putIfCacheable(cache, request, response);
    return response;
  } catch {
    return (await cache.match(request)) || offlineResponse();
  }
}

async function cacheFirstAsset(request) {
  const cache = await caches.open(STATIC_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    await putIfCacheable(cache, request, response);
    return response;
  } catch {
    return offlineResponse();
  }
}

async function staleWhileRevalidate(event) {
  const { request } = event;
  const cache = await caches.open(PAGE_CACHE);
  const cached = await cache.match(request);
  const networkPromise = (async () => {
    try {
      const response = await fetch(request);
      await putIfCacheable(cache, request, response);
      return response;
    } catch {
      return null;
    }
  })();

  if (cached) {
    event.waitUntil(networkPromise.then(() => undefined));
    return cached;
  }

  return (await networkPromise) || offlineResponse();
}
