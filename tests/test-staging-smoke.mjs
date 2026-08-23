import assert from 'node:assert/strict';
import http from 'node:http';
import https from 'node:https';

const BASE_URL = (process.env.STAGING_BASE_URL || 'https://david-porto-preview.davidpd89.workers.dev').replace(/\/$/, '');
const REQUEST_TIMEOUT_MS = 10_000;
const INSECURE_TLS = process.env.STAGING_SMOKE_INSECURE_TLS === '1';

const PUBLIC_ROUTES = [
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
];

const INTERNAL_ROUTES = [
  '/scripts/',
  '/tests/',
  '/data/',
  '/.env.example',
  '/lecturas/',
  '/publicar-web/',
  '/editorial-facts.json',
  '/cloudflare-worker-subscribe.js',
];

// AF -- assets/assistant.js does `import('/pagefind/pagefind.js')` before
// falling back to local ranking; if staging doesn't actually serve these,
// the fallback masks it silently in the UI and nothing else here would
// notice. Asset routes only (no <title>, unlike PUBLIC_ROUTES).
const PAGEFIND_ASSET_ROUTES = [
  '/pagefind/pagefind.js',
  '/pagefind/eligible-manifest.json',
];

function requestText(url, timeoutMs) {
  const target = new URL(url);
  const client = target.protocol === 'https:' ? https : http;

  return new Promise((resolve, reject) => {
    const req = client.request(
      target,
      {
        method: 'GET',
        rejectUnauthorized: target.protocol === 'https:' ? !INSECURE_TLS : undefined,
        headers: {
          'user-agent': 'staging-smoke-test/1.0',
          accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        },
      },
      (res) => {
        let body = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => {
          body += chunk;
        });
        res.on('end', () => {
          resolve({ status: res.statusCode ?? 0, body });
        });
      },
    );

    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error(`timeout after ${timeoutMs}ms`));
    });
    req.on('error', reject);
    req.end();
  });
}

function extractTitle(html) {
  const m = html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i);
  if (!m) {
    return '';
  }
  return m[1].replace(/\s+/g, ' ').trim();
}

function extractJsonLdBlocks(html) {
  const blocks = [];
  const re = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const raw = m[1].trim();
    if (raw) {
      blocks.push(raw);
    }
  }
  return blocks;
}

function parseAnyJsonLd(html) {
  const blocks = extractJsonLdBlocks(html);
  assert.ok(blocks.length > 0, 'missing JSON-LD block');
  for (const raw of blocks) {
    try {
      JSON.parse(raw);
      return;
    } catch {
      // Try next block.
    }
  }
  throw new Error('all JSON-LD blocks failed to parse as JSON');
}

async function checkPublicRoute(pathname) {
  const url = `${BASE_URL}${pathname}`;
  let response;
  try {
    response = await requestText(url, REQUEST_TIMEOUT_MS);
  } catch (err) {
    throw new Error(`${pathname}: request failed (${err?.name || 'error'}: ${err?.message || err})`);
  }

  assert.equal(response.status, 200, `${pathname}: expected HTTP 200, got ${response.status}`);
  const title = extractTitle(response.body);
  assert.ok(title.length > 0, `${pathname}: missing non-empty <title>`);
  return response.body;
}

async function checkAssetRoute(pathname) {
  const url = `${BASE_URL}${pathname}`;
  let response;
  try {
    response = await requestText(url, REQUEST_TIMEOUT_MS);
  } catch (err) {
    throw new Error(`${pathname}: request failed (${err?.name || 'error'}: ${err?.message || err})`);
  }
  assert.equal(response.status, 200, `${pathname}: expected HTTP 200, got ${response.status}`);
  assert.ok(response.body.length > 0, `${pathname}: empty body`);
}

async function checkInternalRoute(pathname) {
  const url = `${BASE_URL}${pathname}`;
  let response;
  try {
    response = await requestText(url, REQUEST_TIMEOUT_MS);
  } catch (err) {
    throw new Error(`${pathname}: request failed (${err?.name || 'error'}: ${err?.message || err})`);
  }
  assert.equal(response.status, 404, `${pathname}: expected HTTP 404, got ${response.status}`);
}

async function main() {
  if (INSECURE_TLS) {
    console.warn('WARN: STAGING_SMOKE_INSECURE_TLS=1 enabled (certificate validation disabled for this run).');
  }

  const failures = [];
  const htmlByRoute = new Map();

  for (const route of PUBLIC_ROUTES) {
    try {
      const body = await checkPublicRoute(route);
      htmlByRoute.set(route, body);
      console.log(`OK public ${route}`);
    } catch (err) {
      failures.push(String(err?.message || err));
      console.error(`FAIL public ${route}: ${err?.message || err}`);
    }
  }

  for (const route of PAGEFIND_ASSET_ROUTES) {
    try {
      await checkAssetRoute(route);
      console.log(`OK asset ${route}`);
    } catch (err) {
      failures.push(String(err?.message || err));
      console.error(`FAIL asset ${route}: ${err?.message || err}`);
    }
  }

  for (const route of INTERNAL_ROUTES) {
    try {
      await checkInternalRoute(route);
      console.log(`OK internal ${route} -> 404`);
    } catch (err) {
      failures.push(String(err?.message || err));
      console.error(`FAIL internal ${route}: ${err?.message || err}`);
    }
  }

  for (const route of ['/', '/las-manecillas-del-recuerdo/']) {
    try {
      const html = htmlByRoute.get(route);
      assert.ok(typeof html === 'string' && html.length > 0, `${route}: missing HTML for JSON-LD check`);
      parseAnyJsonLd(html);
      console.log(`OK jsonld ${route}`);
    } catch (err) {
      failures.push(`${route}: ${err?.message || err}`);
      console.error(`FAIL jsonld ${route}: ${err?.message || err}`);
    }
  }

  if (failures.length > 0) {
    console.error(`\nSTAGING SMOKE FAIL (${failures.length} issue(s))`);
    for (const item of failures) {
      console.error(` - ${item}`);
    }
    process.exit(1);
  }

  console.log('\nSTAGING SMOKE PASS');
}

main().catch((err) => {
  console.error(`UNEXPECTED ERROR: ${err?.stack || err}`);
  process.exit(1);
});
