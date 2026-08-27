import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
const source = readFileSync(resolve(ROOT, 'service-worker.js'), 'utf8');

assert(
  source.includes('request.headers.has("Range")') &&
    source.includes('request.destination === "video"') &&
    source.includes('request.destination === "audio"'),
  'Media/range bypass must remain explicit before generic asset caching.'
);

const mediaGuard = source.indexOf('if (isRangeOrMediaRequest(request)) return;');
const assetRoute = source.indexOf('if (url.pathname.startsWith("/assets/"))');
assert(mediaGuard >= 0 && assetRoute >= 0 && mediaGuard < assetRoute, 'Media/range bypass must run before /assets/ caching.');

assert(
  source.includes('event.respondWith(staleWhileRevalidate(event, STATIC_CACHE));'),
  'Unversioned /assets/ must refresh in the background instead of using permanent cache-first.'
);
assert(
  !source.includes('event.respondWith(cacheFirstAsset(request))'),
  'Regression: cache-first returned for mutable /assets/ URLs.'
);
assert(
  !/async function cacheFirstAsset\s*\(/.test(source),
  'Dead cache-first asset strategy should not remain available for accidental reuse.'
);

const version = source.match(/const CACHE_VERSION = `\$\{CACHE_NAMESPACE\}-(v\d+)`;/)?.[1];
assert(version, 'PWA cache version declaration missing.');
assert(Number(version.slice(1)) >= 13, 'Freshness strategy change must invalidate the v12 cache that reproduced the incident.');

console.log(`OK: PWA cache freshness contract satisfied (${version}).`);
