import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (...parts) => readFileSync(path.join(ROOT, ...parts), 'utf8');
const scriptSource = read('script.js');
const generalSource = read('assets', 'newsletter-general.js');
const popupSource = read('assets', 'newsletter-popup.js');
const workerSource = read('cloudflare-worker-subscribe.js');
const builderSource = read('scripts', 'build-site-shell.py');

function setFromArrayLiteral(content, label) {
  const re = new RegExp(`${label}\\s*=\\s*\\{([\\s\\S]*?)\\n\\}`);
  const match = content.match(re);
  assert.ok(match, `${label} not found`);
  const keys = [...match[1].matchAll(/\n\s*([a-z_][a-z0-9_-]*)\s*:/gi)].map((m) => m[1]);
  return new Set(keys);
}

function setFromSubmitCalls(content) {
  const calls = [...content.matchAll(/submitNewsletter\([^\)]*?"([a-z-]+)"\)\s*;/g)].map((m) => m[1]);
  return new Set(calls);
}

assert.match(scriptSource, /NEWSLETTER_CONFIG\s*=\s*\{\s*endpoint:\s*"https:\/\/subscribe\.davidpd89\.workers\.dev"\s*\}/s,
  'legacy newsletter fallback must keep the production Worker URL');
assert.match(scriptSource, /window\.DPNewsletterGeneral\?\.postNewsletter/,
  'script.js must delegate POSTs to the shared V1 newsletter transport when available');
assert.match(scriptSource, /const gdprEl = document\.getElementById\(gdprId\)/,
  'generic legacy helper must resolve gdprId instead of leaving it dead');
assert.match(scriptSource, /if \(!gdprEl \|\| !gdprEl\.checked\)/,
  'generic legacy helper must block unchecked privacy consent');
assert.doesNotMatch(scriptSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'legacy client must not add consent to the Worker payload');

assert.match(generalSource, /const ENDPOINT = 'https:\/\/subscribe\.davidpd89\.workers\.dev'/,
  'shared general client must use the canonical Worker');
assert.match(generalSource, /TIMEOUT_MS = 12000/,
  'shared general client must preserve timeout contract');
assert.match(generalSource, /response\.status === 429/,
  'shared general client must preserve explicit rate-limit handling');
assert.match(generalSource, /navigator\.onLine === false/,
  'shared general client must preserve offline handling');
assert.match(generalSource, /form\.dataset\.newsletterBound === 'true'/,
  'shared client must protect against double binding');
assert.match(generalSource, /input\[name="consent"\]/,
  'shared client must resolve the privacy checkbox');
assert.match(generalSource, /!consent \|\| !consent\.checked/,
  'shared client must block missing or unchecked consent');
assert.doesNotMatch(generalSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'shared client must preserve the existing Worker payload without consent field');

const workerSources = setFromArrayLiteral(workerSource, 'SOURCE_MAP');
const formSources = setFromSubmitCalls(scriptSource);
assert.ok(formSources.has('home') && formSources.has('fragmento') && formSources.has('manecillas') && formSources.has('cuaderno') && formSources.has('explore'),
  'legacy fallback must keep all general source labels');
const specialSources = new Set(['quiz', 'popup']);
const clientSources = new Set([...formSources, ...specialSources]);
assert.deepEqual([...clientSources].sort(), [...workerSources].sort(),
  'client source labels must stay in parity with Worker SOURCE_MAP keys');

assert.ok(!/localStorage\.setItem\([^\)]*email/i.test(generalSource),
  'shared client must never persist email in localStorage');
assert.ok(!/sessionStorage\.setItem\([^\)]*email/i.test(generalSource),
  'shared client must never persist email in sessionStorage');

for (const [file, suffix] of [
  ['index.html', 'home'],
  ['fragmento/index.html', 'fragmento'],
  ['las-manecillas-del-recuerdo/index.html', 'manecillas'],
  ['cuaderno/index.html', 'cuaderno']
]) {
  const html = read(...file.split('/'));
  assert.match(html, new RegExp(`id="nl-gdpr-${suffix}"[^>]*name="consent"[^>]*required`), `${file} must render required consent`);
  assert.match(html, /href="\/privacidad\.html"/, `${file} consent must link to privacy policy`);
}

assert.ok(builderSource.includes('nl-gdpr-explore'),
  'shell builder must generate Explore consent');
assert.match(builderSource, /newsletter-general\.js/,
  'shell builder must load the shared general newsletter runtime');
assert.match(builderSource, /allow_newsletter/,
  'shell builder must conditionally omit newsletter UI for stricter custom CSP pages');
assert.match(builderSource, /subscribe\.davidpd89\.workers\.dev/,
  'shell builder CSP boundary must key off the canonical subscription Worker');

assert.match(popupSource, /id=\\?"nl-popup-gdpr\\?"[^>]*name=\\?"consent\\?"[^>]*required/,
  'newsletter popup must render a required privacy-consent checkbox');
assert.match(popupSource, /href=\\?"\/privacidad\.html\\?"/,
  'newsletter popup consent must link to the privacy policy');
assert.match(popupSource, /const gdprEl = d\.querySelector\("#nl-popup-gdpr"\)/,
  'newsletter popup must resolve its consent checkbox before submission');
assert.match(popupSource, /if \(!gdprEl\.checked\)/,
  'newsletter popup must block submission when privacy consent is unchecked');
assert.doesNotMatch(popupSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'popup must not add consent to the Worker payload');

console.log('test-newsletter-client-contract: all assertions passed');
