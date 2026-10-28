import vm from 'node:vm';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const SOURCE = readFileSync(resolve(fileURLToPath(new URL('../service-worker.js', import.meta.url))), 'utf8');
const VERSION = SOURCE.match(/CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`/)?.[1];
if (!VERSION) throw Error('No se encuentra CACHE_VERSION');
const ORIGIN = 'https://qa.invalid';
const key = request => new URL(typeof request === 'string' ? request : request.url, ORIGIN).href;

export function createWorker(network = async () => new Response('ok')) {
  const listeners = new Map();
  const stored = new Map();
  let rejectPut = () => false;
  let skipWaitingCalled = false;
  let networkHandler = network;
  const cacheFor = name => {
    if (!stored.has(name)) stored.set(name, new Map());
    const entries = stored.get(name);
    return {
      async match(request) { return entries.get(key(request))?.clone(); },
      async put(request, response) {
        if (rejectPut(name, key(request))) throw Error('quota exceeded');
        entries.set(key(request), response.clone());
      },
      async addAll(requests) {
        const fetched = [];
        for (const request of requests) {
          const response = await networkHandler(request);
          if (!response.ok) throw Error('precache rejected');
          fetched.push([request, response]);
        }
        for (const [request, response] of fetched) await this.put(request, response);
      },
    };
  };
  const caches = {
    open: async name => cacheFor(name),
    keys: async () => [...stored.keys()],
    delete: async name => stored.delete(name),
  };
  class LocalRequest {
    constructor(url, options = {}) {
      this.url = key(url);
      this.method = options.method || 'GET';
      this.headers = new Headers(options.headers || {});
      this.cache = options.cache;
    }
  }
  const self = {
    location: { origin: ORIGIN },
    addEventListener: (name, fn) => listeners.set(name, fn),
    skipWaiting: async () => { skipWaitingCalled = true; },
    clients: { claim: async () => {} },
  };
  vm.runInNewContext(SOURCE, {
    self, caches, fetch: request => networkHandler(request),
    Response, Request: LocalRequest, URL, Headers, Set, Promise,
  }, { filename: 'service-worker.js' });
  const dispatch = async (name, request) => {
    const waits = [];
    let responsePromise;
    const event = {
      request,
      respondWith: response => { responsePromise = Promise.resolve(response); },
      waitUntil: promise => waits.push(Promise.resolve(promise)),
    };
    listeners.get(name)(event);
    if (name === 'fetch' && !responsePromise) return { intercepted: false };
    const response = responsePromise ? await responsePromise : null;
    await Promise.all(waits);
    return { intercepted: true, response };
  };
  return {
    origin: ORIGIN,
    pageCache: `david-porto-pwa-${VERSION}-pages`,
    staticCache: `david-porto-pwa-${VERSION}-static`,
    caches,
    cacheFor,
    entries: name => [...(stored.get(name)?.keys() || [])],
    request(path, { mode = 'cors', method = 'GET', destination = '', headers = {} } = {}) {
      return { url: key(path), mode, method, destination, headers: new Headers(headers) };
    },
    fetch: request => dispatch('fetch', request),
    install: () => dispatch('install'),
    setNetwork: handler => { networkHandler = handler; },
    setPutFailure: predicate => { rejectPut = predicate; },
    wasSkipped: () => skipWaitingCalled,
  };
}
