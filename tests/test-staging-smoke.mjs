import assert from 'node:assert/strict';
import http from 'node:http';
import https from 'node:https';

// Generic HTTP smoke used by both staging and the post-deploy production gate.
// SITE_BASE_URL is the new neutral contract; STAGING_BASE_URL is kept for
// backwards compatibility with the existing scheduled staging workflow.
const SITE_BASE_URL = process.env.SITE_BASE_URL || '';
const BASE_URL = (
  SITE_BASE_URL ||
  process.env.STAGING_BASE_URL ||
  'https://david-porto-preview.davidpd89.workers.dev'
).replace(/\/$/, '');
const SMOKE_LABEL = (
  process.env.SMOKE_LABEL || (SITE_BASE_URL ? 'PRODUCTION' : 'STAGING')
).trim().toUpperCase();
const CANONICAL_ORIGIN = (process.env.CANONICAL_ORIGIN || 'https://davidportodiaz.com').replace(/\/$/, '');
const EXPECTED_RELEASE_SHA = (process.env.EXPECTED_RELEASE_SHA || '').trim().toLowerCase();
const REQUEST_TIMEOUT_MS = 10_000;
const INSECURE_TLS =
  process.env.SMOKE_INSECURE_TLS === '1' ||
  process.env.STAGING_SMOKE_INSECURE_TLS === '1';

if (EXPECTED_RELEASE_SHA && !/^[0-9a-f]{40}$/.test(EXPECTED_RELEASE_SHA)) {
  throw new Error('EXPECTED_RELEASE_SHA must be exactly 40 hexadecimal characters');
}

const PUBLIC_ROUTES = [
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
];

// These classes are deliberately broader than the historical staging list.
// The public artifact is allowlist-first; if one of these becomes HTTP 200,
// production has crossed the repo -> public boundary incorrectly.
const INTERNAL_ROUTES = [
  '/scripts/',
  '/tests/',
  '/data/',
  '/docs/',
  '/qa/',
  '/lab/',
  '/migrations/',
  '/.env.example',
  '/lecturas/',
  '/publicar-web/',
  '/editorial-facts.json',
  '/cloudflare-worker-subscribe.js',
  '/cloudflare-worker-assistant.js',
  '/wrangler.assistant.jsonc',
  '/package.json',
  '/package-lock.json',
  '/lighthouserc.json',
  '/press-kit/package-manifest.json',
  '/donde-empieza-la-jaula/',
];

const MACHINE_ROUTES = [
  ['/robots.txt', 'Sitemap:'],
  ['/sitemap.xml', '<urlset'],
  ['/llms.txt', 'David Porto'],
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
          'user-agent': `david-porto-${SMOKE_LABEL.toLowerCase()}-smoke/2.1`,
          accept: 'text/html,application/xhtml+xml,application/xml,application/json,text/plain;q=0.9,*/*;q=0.8',
          // Per-SHA marker URLs should not need this, but explicit no-cache makes
          // the intent clear to intermediaries and avoids validating a stale
          // browser/proxy object when this smoke is reused elsewhere.
          'cache-control': 'no-cache',
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

function extractCanonical(html) {
  const tags = html.match(/<link\b[^>]*>/gi) || [];
  for (const tag of tags) {
    if (!/\brel=["']canonical["']/i.test(tag)) {
      continue;
    }
    const href = tag.match(/\bhref=["']([^"']+)["']/i);
    if (href) {
      return href[1].trim();
    }
  }
  return '';
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

async function checkMachineRoute(pathname, marker) {
  const url = `${BASE_URL}${pathname}`;
  let response;
  try {
    response = await requestText(url, REQUEST_TIMEOUT_MS);
  } catch (err) {
    throw new Error(`${pathname}: request failed (${err?.name || 'error'}: ${err?.message || err})`);
  }
  assert.equal(response.status, 200, `${pathname}: expected HTTP 200, got ${response.status}`);
  assert.ok(response.body.includes(marker), `${pathname}: missing expected marker ${JSON.stringify(marker)}`);
}

async function checkReleaseIdentity() {
  if (!EXPECTED_RELEASE_SHA) {
    console.log('SKIP release identity (EXPECTED_RELEASE_SHA not set)');
    return;
  }

  const pathname = `/_release/${EXPECTED_RELEASE_SHA}.json`;
  let response;
  try {
    response = await requestText(`${BASE_URL}${pathname}`, REQUEST_TIMEOUT_MS);
  } catch (err) {
    throw new Error(`${pathname}: request failed (${err?.name || 'error'}: ${err?.message || err})`);
  }

  assert.equal(response.status, 200, `${pathname}: expected HTTP 200, got ${response.status}`);
  let payload;
  try {
    payload = JSON.parse(response.body);
  } catch (err) {
    throw new Error(`${pathname}: invalid JSON (${err?.message || err})`);
  }
  assert.deepEqual(
    payload,
    { schemaVersion: 1, sha: EXPECTED_RELEASE_SHA },
    `${pathname}: release identity does not match deployed SHA`,
  );
  console.log(`OK exact release ${EXPECTED_RELEASE_SHA}`);
}

async function main() {
  if (INSECURE_TLS) {
    console.warn(`WARN: ${SMOKE_LABEL} smoke has certificate validation disabled for this run.`);
  }

  console.log(`${SMOKE_LABEL} smoke target: ${BASE_URL}`);
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

  for (const route of INTERNAL_ROUTES) {
    try {
      await checkInternalRoute(route);
      console.log(`OK internal ${route} -> 404`);
    } catch (err) {
      failures.push(String(err?.message || err));
      console.error(`FAIL internal ${route}: ${err?.message || err}`);
    }
  }

  for (const [route, marker] of MACHINE_ROUTES) {
    try {
      await checkMachineRoute(route, marker);
      console.log(`OK machine ${route}`);
    } catch (err) {
      failures.push(String(err?.message || err));
      console.error(`FAIL machine ${route}: ${err?.message || err}`);
    }
  }

  for (const route of ['/', '/las-manecillas-del-recuerdo/']) {
    try {
      const html = htmlByRoute.get(route);
      assert.ok(typeof html === 'string' && html.length > 0, `${route}: missing HTML for machine checks`);
      parseAnyJsonLd(html);
      console.log(`OK jsonld ${route}`);

      const canonical = extractCanonical(html);
      const expected = `${CANONICAL_ORIGIN}${route}`;
      assert.equal(canonical, expected, `${route}: expected canonical ${expected}, got ${canonical || '(missing)'}`);
      console.log(`OK canonical ${route}`);
    } catch (err) {
      failures.push(`${route}: ${err?.message || err}`);
      console.error(`FAIL machine-contract ${route}: ${err?.message || err}`);
    }
  }

  try {
    await checkReleaseIdentity();
  } catch (err) {
    failures.push(String(err?.message || err));
    console.error(`FAIL release-identity: ${err?.message || err}`);
  }

  if (failures.length > 0) {
    console.error(`\n${SMOKE_LABEL} SMOKE FAIL (${failures.length} issue(s))`);
    for (const item of failures) {
      console.error(` - ${item}`);
    }
    process.exit(1);
  }

  console.log(`\n${SMOKE_LABEL} SMOKE PASS`);
}

main().catch((err) => {
  console.error(`UNEXPECTED ERROR: ${err?.stack || err}`);
  process.exit(1);
});
