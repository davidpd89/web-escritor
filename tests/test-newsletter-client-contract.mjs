import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const scriptSource = readFileSync(path.join(ROOT, 'script.js'), 'utf8');
const popupSource = readFileSync(path.join(ROOT, 'assets', 'newsletter-popup.js'), 'utf8');
const workerSource = readFileSync(path.join(ROOT, 'cloudflare-worker-subscribe.js'), 'utf8');

function setFromArrayLiteral(content, label) {
  const re = new RegExp(`${label}\\s*=\\s*\\{([\\s\\S]*?)\\n\\}`);
  const match = content.match(re);
  assert.ok(match, `${label} not found`);
  const body = match[1];
  const keys = [...body.matchAll(/\n\s*([a-z_][a-z0-9_-]*)\s*:/gi)].map((m) => m[1]);
  return new Set(keys);
}

function setFromSubmitCalls(content) {
  const calls = [...content.matchAll(/submitNewsletter\([^\)]*?"([a-z]+)"\)\s*;/g)].map((m) => m[1]);
  return new Set(calls);
}

assert.match(scriptSource, /NEWSLETTER_CONFIG\s*=\s*\{\s*endpoint:\s*"https:\/\/subscribe\.davidpd89\.workers\.dev"\s*\}/s,
  'newsletter endpoint must stay on the production Worker URL');

assert.match(scriptSource, /NEWSLETTER_TIMEOUT_MS\s*=\s*12000/, 'newsletter timeout constant must exist');
assert.match(scriptSource, /function postNewsletter\(payload\)/, 'postNewsletter helper must exist');
assert.match(scriptSource, /new AbortController\(\)/, 'newsletter flow must use AbortController timeout');
assert.match(scriptSource, /if \(res\.status === 429\)/, 'newsletter flow must handle 429 explicitly');
assert.match(scriptSource, /navigator\.onLine === false/, 'newsletter flow must detect offline state');

const workerSources = setFromArrayLiteral(workerSource, 'SOURCE_MAP');
const formSources = setFromSubmitCalls(scriptSource);
assert.ok(formSources.has('home') && formSources.has('fragmento') && formSources.has('manecillas') && formSources.has('cuaderno'),
  'generic forms must keep all expected source labels');

const specialSources = new Set(['quiz', 'popup']);
const clientSources = new Set([...formSources, ...specialSources]);
assert.deepEqual([...clientSources].sort(), [...workerSources].sort(),
  'client source labels must stay in parity with Worker SOURCE_MAP keys');

assert.ok(!/localStorage\.setItem\([^\)]*emailEl\.value/i.test(scriptSource),
  'email value must never be stored in localStorage');
assert.ok(!/sessionStorage\.setItem\([^\)]*emailEl\.value/i.test(scriptSource),
  'email value must never be stored in sessionStorage');

assert.match(popupSource, /id=\\?"nl-popup-gdpr\\?"[^>]*name=\\?"consent\\?"[^>]*required/,
  'newsletter popup must render a required privacy-consent checkbox');
assert.match(popupSource, /href=\\?"\/privacidad\.html\\?"/,
  'newsletter popup consent must link to the privacy policy');
assert.match(popupSource, /const gdprEl = d\.querySelector\("#nl-popup-gdpr"\)/,
  'newsletter popup must resolve its consent checkbox before submission');
assert.match(popupSource, /if \(!gdprEl\.checked\)/,
  'newsletter popup must block submission when privacy consent is unchecked');
assert.doesNotMatch(popupSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'privacy consent must not be silently added to the existing Worker payload contract');

console.log('test-newsletter-client-contract: all assertions passed');
