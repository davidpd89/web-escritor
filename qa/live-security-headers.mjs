import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const BASE_URL = new URL(process.env.LIVE_SECURITY_BASE_URL || 'https://davidportodiaz.com/');
const OUTPUT = resolve(process.env.LIVE_SECURITY_HEADERS_OUTPUT || 'artifacts/security-headers/live-security-headers.json');
const MAX_REDIRECTS = 8;
const TIMEOUT_MS = 15_000;

const ROUTES = [
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
  '/asistente/',
  '/lectores-beta/',
];

const SECURITY_HEADERS = [
  'content-security-policy',
  'strict-transport-security',
  'x-content-type-options',
  'referrer-policy',
  'permissions-policy',
  'x-frame-options',
  'cross-origin-resource-policy',
  'cross-origin-opener-policy',
  'cross-origin-embedder-policy',
];

const DIAGNOSTIC_HEADERS = [
  'server',
  'cache-control',
  'content-type',
  'location',
  'x-xss-protection',
  'expect-ct',
  'public-key-pins',
];

function pickHeaders(headers) {
  return Object.fromEntries(
    [...SECURITY_HEADERS, ...DIAGNOSTIC_HEADERS].map((name) => [name, headers.get(name)]),
  );
}

async function fetchOne(url) {
  const response = await fetch(url, {
    method: 'GET',
    redirect: 'manual',
    headers: {
      accept: 'text/html,application/xhtml+xml,*/*;q=0.1',
      'user-agent': 'web-escritor-live-security-headers-audit/1.0',
    },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });

  const observed = {
    url: url.toString(),
    status: response.status,
    headers: pickHeaders(response.headers),
  };
  await response.body?.cancel().catch(() => {});
  return observed;
}

async function follow(url) {
  const hops = [];
  let current = new URL(url);

  for (let index = 0; index <= MAX_REDIRECTS; index += 1) {
    const observed = await fetchOne(current);
    hops.push(observed);

    if (![301, 302, 303, 307, 308].includes(observed.status)) {
      return {
        requestedUrl: new URL(url).toString(),
        redirects: hops.slice(0, -1),
        final: observed,
      };
    }

    const location = observed.headers.location;
    if (!location) {
      throw new Error(`${current}: redirect ${observed.status} without Location`);
    }
    current = new URL(location, current);
  }

  throw new Error(`${url}: exceeded ${MAX_REDIRECTS} redirects`);
}

function classify(observation) {
  const headers = observation.final.headers;
  return {
    missingSecurityHeaders: SECURITY_HEADERS.filter((name) => !headers[name]),
    obsoleteHeadersPresent: ['x-xss-protection', 'expect-ct', 'public-key-pins'].filter((name) => headers[name]),
    hasHttpCsp: Boolean(headers['content-security-policy']),
    hasFramingHeader: Boolean(headers['x-frame-options']) || /(?:^|;)\s*frame-ancestors\b/i.test(headers['content-security-policy'] || ''),
    hasHsts: Boolean(headers['strict-transport-security']),
    hasNosniff: /^nosniff$/i.test(headers['x-content-type-options'] || ''),
  };
}

async function audit(label, url) {
  try {
    const observation = await follow(url);
    return { label, ok: true, ...observation, classification: classify(observation) };
  } catch (error) {
    return {
      label,
      ok: false,
      requestedUrl: new URL(url).toString(),
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

const httpsOrigin = new URL('/', BASE_URL);
httpsOrigin.protocol = 'https:';
const httpOrigin = new URL('/', BASE_URL);
httpOrigin.protocol = 'http:';

const results = [];
results.push(await audit('http-entry', httpOrigin));
for (const route of ROUTES) {
  results.push(await audit(route, new URL(route, httpsOrigin)));
}

const report = {
  schemaVersion: 1,
  checkedAt: new Date().toISOString(),
  baseUrl: httpsOrigin.toString(),
  mode: 'REPORT_ONLY',
  semantics: {
    missingHeaderIsFailure: false,
    observationFailureIsFailure: true,
    note: 'Absence is evidence to classify ownership, not an automatic hardening mandate.',
  },
  headersObserved: SECURITY_HEADERS,
  results,
};

await mkdir(dirname(OUTPUT), { recursive: true });
await writeFile(OUTPUT, `${JSON.stringify(report, null, 2)}\n`, 'utf8');

for (const result of results) {
  if (!result.ok) {
    console.error(`OBSERVATION ERROR ${result.label}: ${result.error}`);
    continue;
  }
  const final = result.final;
  const missing = result.classification.missingSecurityHeaders.join(', ') || 'none';
  const redirects = result.redirects.map((hop) => `${hop.status} ${hop.url}`).join(' -> ') || 'none';
  console.log(`${result.label}: ${final.status} ${final.url}`);
  console.log(`  redirects: ${redirects}`);
  console.log(`  missing observed security headers: ${missing}`);
  console.log(`  HTTP CSP=${result.classification.hasHttpCsp} HSTS=${result.classification.hasHsts} nosniff=${result.classification.hasNosniff} framing=${result.classification.hasFramingHeader}`);
}

console.log(`Report written to ${OUTPUT}`);

if (results.some((result) => !result.ok)) {
  process.exitCode = 1;
}
