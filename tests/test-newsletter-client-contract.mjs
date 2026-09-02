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
// Author decision (2026-09-01): no consent checkbox anywhere on the site --
// every newsletter surface uses a plain privacy-policy note instead, so
// submitNewsletter is always called with a null gdprId now. The gdprId
// parameter/branch stays in the function as a general capability (harmless,
// simply unused by every current call site) rather than being ripped out.
assert.match(scriptSource, /const gdprEl = document\.getElementById\(gdprId\)/,
  'generic legacy helper must resolve gdprId instead of leaving it dead');
assert.match(scriptSource, /if \(gdprId && \(!gdprEl \|\| !gdprEl\.checked\)\)/,
  'generic legacy helper must still support blocking on an unchecked consent box, even though no current call site uses it');
assert.doesNotMatch(scriptSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'legacy client must not add consent to the Worker payload');
for (const source of ['home', 'fragmento', 'manecillas', 'cuaderno', 'explore']) {
  assert.match(scriptSource, new RegExp(`submitNewsletter\\("newsletter-form-${source}",\\s*"nl-email-${source}",\\s*null,`),
    `legacy fallback wiring for ${source} must pass a null gdprId (no checkbox to resolve)`);
}

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
assert.doesNotMatch(generalSource, /input\[name="consent"\]/,
  'shared client (Explore form) must not look for a consent checkbox that no longer exists');
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

// Author decision (2026-09-01): no consent checkbox anywhere on the site --
// friction-free "just email + submit", every surface uses the same plain
// privacy-policy note instead of a required checkbox.
for (const [file, suffix] of [
  ['fragmento/index.html', 'fragmento'],
  ['las-manecillas-del-recuerdo/index.html', 'manecillas'],
  ['cuaderno/index.html', 'cuaderno'],
  ['index.html', 'home']
]) {
  const html = read(...file.split('/'));
  assert.doesNotMatch(html, new RegExp(`id="nl-gdpr-${suffix}"`), `${file} must not render a consent checkbox`);
  assert.match(html, /Al enviar tu email, aceptas la <a href="\/privacidad\.html">pol[ií]tica de privacidad<\/a>/,
    `${file} must keep the plain privacy-policy note`);
}

assert.doesNotMatch(builderSource, /nl-gdpr-explore/,
  'shell builder must not generate an Explore consent checkbox');
assert.match(builderSource, /Al enviar tu email, aceptas la <a href="\/privacidad\.html">pol[ií]tica de privacidad<\/a>/,
  'shell builder must generate the Explore privacy-policy note');
assert.match(builderSource, /newsletter-general\.js/,
  'shell builder must load the shared general newsletter runtime');
assert.match(builderSource, /allow_newsletter/,
  'shell builder must conditionally omit newsletter UI for stricter custom CSP pages');
assert.match(builderSource, /subscribe\.davidpd89\.workers\.dev/,
  'shell builder CSP boundary must key off the canonical subscription Worker');

assert.doesNotMatch(popupSource, /nl-popup-gdpr/,
  'newsletter popup must not render a consent checkbox');
assert.match(popupSource, /Al enviar tu email, aceptas la <a href="\/privacidad\.html">pol[ií]tica de privacidad<\/a>/,
  'newsletter popup must keep the plain privacy-policy note');
assert.doesNotMatch(popupSource, /if \(!gdprEl\.checked\)/,
  'newsletter popup must not block submission on a checkbox that no longer exists');
assert.doesNotMatch(popupSource, /postNewsletter\(\{[^}]*consent\s*:/s,
  'popup must not add consent to the Worker payload');

console.log('test-newsletter-client-contract: all assertions passed');
