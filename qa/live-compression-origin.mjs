import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';

const BASE_URL = new URL(process.env.LIVE_COMPRESSION_BASE_URL || 'https://davidportodiaz.com/');
const OUTPUT = resolve(
  process.env.LIVE_COMPRESSION_OUTPUT || 'artifacts/compression/live-compression-origin.json',
);
const TIMEOUT_MS = 15_000;

const TARGETS = [
  { label: 'home-html', path: '/', expectedKind: 'html' },
  { label: 'shell-css', path: '/assets/v1-shell.css', expectedKind: 'css' },
  { label: 'runtime-js', path: '/script.js', expectedKind: 'javascript' },
];

const NEGOTIATIONS = [
  { label: 'modern', acceptEncoding: 'br, gzip' },
  { label: 'gzip', acceptEncoding: 'gzip' },
  { label: 'identity', acceptEncoding: 'identity' },
];

function parseVary(value) {
  return (value || '')
    .split(',')
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);
}

function classifyContentType(value) {
  const contentType = (value || '').toLowerCase();
  if (contentType.includes('text/html')) return 'html';
  if (contentType.includes('text/css')) return 'css';
  if (
    contentType.includes('javascript') ||
    contentType.includes('ecmascript') ||
    contentType.includes('text/js')
  ) {
    return 'javascript';
  }
  return 'other';
}

async function observe(target, negotiation) {
  const url = new URL(target.path, BASE_URL);
  try {
    const response = await fetch(url, {
      method: 'GET',
      redirect: 'follow',
      headers: {
        accept: '*/*',
        'accept-encoding': negotiation.acceptEncoding,
        'user-agent': 'web-escritor-live-compression-audit/1.0',
      },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    const headers = {
      'content-encoding': response.headers.get('content-encoding'),
      vary: response.headers.get('vary'),
      'content-type': response.headers.get('content-type'),
      'content-length': response.headers.get('content-length'),
      'cache-control': response.headers.get('cache-control'),
      etag: response.headers.get('etag'),
      server: response.headers.get('server'),
    };
    await response.body?.cancel().catch(() => {});

    const varyTokens = parseVary(headers.vary);
    const contentKind = classifyContentType(headers['content-type']);
    const encoding = (headers['content-encoding'] || 'identity').toLowerCase();

    return {
      ok: true,
      target: target.label,
      requestedUrl: url.toString(),
      finalUrl: response.url,
      status: response.status,
      negotiation: negotiation.label,
      acceptEncoding: negotiation.acceptEncoding,
      expectedKind: target.expectedKind,
      contentKind,
      headers,
      classification: {
        encoding,
        compressed: encoding !== 'identity',
        varyIncludesAcceptEncoding: varyTokens.includes('accept-encoding') || varyTokens.includes('*'),
        expectedContentType: contentKind === target.expectedKind,
        identityRequestEncoded: negotiation.label === 'identity' && encoding !== 'identity',
      },
    };
  } catch (error) {
    return {
      ok: false,
      target: target.label,
      requestedUrl: url.toString(),
      negotiation: negotiation.label,
      acceptEncoding: negotiation.acceptEncoding,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

const results = [];
for (const target of TARGETS) {
  for (const negotiation of NEGOTIATIONS) {
    results.push(await observe(target, negotiation));
  }
}

const successful = results.filter((result) => result.ok);
const failed = results.filter((result) => !result.ok);
const compressibleNegotiations = successful.filter(
  (result) => result.negotiation !== 'identity' && result.classification.expectedContentType,
);

const report = {
  schemaVersion: 1,
  checkedAt: new Date().toISOString(),
  baseUrl: BASE_URL.toString(),
  mode: 'REPORT_ONLY',
  semantics: {
    missingCompressionIsFailure: false,
    observationFailureIsFailure: true,
    note: 'E.7 observes origin/hosting negotiation. It does not authorize proxy/CDN or hosting changes.',
  },
  targets: TARGETS,
  negotiations: NEGOTIATIONS,
  summary: {
    observations: results.length,
    successful: successful.length,
    failed: failed.length,
    compressibleNegotiations: compressibleNegotiations.length,
    compressedNegotiations: compressibleNegotiations.filter(
      (result) => result.classification.compressed,
    ).length,
    varyAcceptEncodingNegotiations: compressibleNegotiations.filter(
      (result) => result.classification.varyIncludesAcceptEncoding,
    ).length,
  },
  results,
};

await mkdir(dirname(OUTPUT), { recursive: true });
await writeFile(OUTPUT, `${JSON.stringify(report, null, 2)}\n`, 'utf8');

for (const result of results) {
  if (!result.ok) {
    console.error(
      `OBSERVATION ERROR ${result.target}/${result.negotiation}: ${result.error}`,
    );
    continue;
  }
  const { classification, headers } = result;
  console.log(
    `${result.target}/${result.negotiation}: ${result.status} ` +
      `encoding=${classification.encoding} vary=${headers.vary || '(absent)'} ` +
      `type=${headers['content-type'] || '(absent)'}`,
  );
}

console.log(
  `Compression observations: ${report.summary.successful}/${report.summary.observations} successful; ` +
    `${report.summary.compressedNegotiations}/${report.summary.compressibleNegotiations} ` +
    'compressible negotiated responses encoded.',
);
console.log(`Report written to ${OUTPUT}`);

if (failed.length > 0) {
  process.exitCode = 1;
}
