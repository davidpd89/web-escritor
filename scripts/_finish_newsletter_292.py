#!/usr/bin/env python3
from pathlib import Path
import re
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(rel, old, new):
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{rel}: expected exactly one replacement, found {count}')
    write(rel, text.replace(old, new, 1))


# 1) Shared V1 newsletter runtime. It owns the general forms and exposes the
# transport so script.js/Beta/popup can reuse the same POST implementation.
newsletter_general = r'''(() => {
  'use strict';
  if (window.DPNewsletterGeneral) return;

  const ENDPOINT = 'https://subscribe.davidpd89.workers.dev';
  const TIMEOUT_MS = 12000;
  const EMAIL_RE = /^[^\s@]{1,64}@[^\s@]{1,253}\.[^\s@]{2,}$/;
  const STAGING_HOSTNAMES = new Set(['david-porto-preview.davidpd89.workers.dev']);
  const STAGING_MESSAGE = 'Formulario desactivado en el entorno de pruebas.';
  const PENDING_COPY = {
    home: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    fragmento: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    manecillas: 'Revisa tu correo y confirma la suscripción. Después te avisaré cuando Las manecillas del recuerdo esté disponible.',
    cuaderno: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.',
    explore: 'Revisa tu correo y confirma la suscripción para recibir las novedades de David Porto Díaz.'
  };

  function isValidEmail(value) {
    const normalized = String(value || '').trim();
    return normalized.length <= 254 && EMAIL_RE.test(normalized);
  }

  function honeypotValue(form) {
    const field = form?.querySelector('input[name="website"]');
    return field ? String(field.value || '').trim() : '';
  }

  function installHoneypot(form) {
    if (!form || form.querySelector('input[name="website"]')) return;
    const wrapper = document.createElement('div');
    wrapper.setAttribute('aria-hidden', 'true');
    wrapper.setAttribute('inert', '');
    wrapper.style.cssText = 'position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap;border:0;';
    const field = document.createElement('input');
    field.type = 'text';
    field.name = 'website';
    field.autocomplete = 'off';
    field.tabIndex = -1;
    wrapper.appendChild(field);
    form.appendChild(wrapper);
  }

  function errorMessage(code) {
    if (code === 'offline') return 'No hay conexión. Revisa tu red e inténtalo de nuevo.';
    if (code === 'timeout') return 'La solicitud está tardando demasiado. Inténtalo de nuevo en unos segundos.';
    if (code === 'rate_limited') return 'Has hecho demasiados intentos. Espera un minuto e inténtalo de nuevo.';
    return 'Error al suscribirse. Escríbenos a davidportodiaz@gmail.com.';
  }

  async function postNewsletter(payload) {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      return { ok: false, code: 'offline' };
    }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
    try {
      const response = await fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      if (response.ok) {
        const body = await response.json().catch(() => ({}));
        if (body && body.ok === true && body.state === 'pending_confirmation') {
          return { ok: true, state: 'pending_confirmation', code: 'pending_confirmation' };
        }
        return { ok: false, code: 'invalid_response' };
      }
      if (response.status === 400) return { ok: false, code: 'invalid_request' };
      if (response.status === 429) return { ok: false, code: 'rate_limited' };
      if (response.status >= 500) return { ok: false, code: 'server_error' };
      return { ok: false, code: 'request_failed' };
    } catch (error) {
      if (error && error.name === 'AbortError') return { ok: false, code: 'timeout' };
      return { ok: false, code: 'network_error' };
    } finally {
      clearTimeout(timer);
    }
  }

  function schedule(fn) {
    if (typeof scheduler !== 'undefined' && scheduler.postTask) {
      return scheduler.postTask(fn, { priority: 'user-blocking' });
    }
    return Promise.resolve().then(fn);
  }

  function bindForm(form) {
    if (!form || form.dataset.newsletterBound === 'true') return;
    const source = String(form.dataset.newsletterSource || '');
    if (!Object.hasOwn(PENDING_COPY, source)) return;
    form.dataset.newsletterBound = 'true';
    installHoneypot(form);

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      schedule(async () => {
        const email = form.querySelector('input[type="email"]');
        const consent = form.querySelector('input[name="consent"]');
        const status = form.querySelector('[role="status"]');
        const submit = form.querySelector('[type="submit"]');
        if (!submit || submit.dataset.submitting === 'true') return;
        if (STAGING_HOSTNAMES.has(window.location.hostname)) {
          if (status) status.textContent = STAGING_MESSAGE;
          return;
        }
        if (!email || !isValidEmail(email.value)) {
          if (status) status.textContent = 'Introduce un email válido.';
          email?.focus({ preventScroll: true });
          return;
        }
        if (!consent || !consent.checked) {
          if (status) status.textContent = 'Acepta la política de privacidad para continuar.';
          consent?.focus({ preventScroll: true });
          return;
        }

        if (status) status.textContent = '';
        const originalText = submit.textContent;
        submit.dataset.submitting = 'true';
        submit.disabled = true;
        submit.textContent = 'Enviando…';
        try {
          const result = await postNewsletter({
            email: email.value.trim(),
            source,
            website: honeypotValue(form)
          });
          if (!result.ok || result.state !== 'pending_confirmation') {
            throw new Error(result.code || 'request_failed');
          }
          form.innerHTML = '<p class="quiz-subscribe-ok">✓ ' + PENDING_COPY[source] + '</p>';
          if (typeof window._gcEvent === 'function') {
            window._gcEvent('newsletter-pending-' + source, 'Newsletter DOI pendiente: ' + source);
          }
        } catch (error) {
          if (status) status.textContent = errorMessage(error.message);
          delete submit.dataset.submitting;
          submit.disabled = false;
          submit.textContent = originalText;
        }
      });
    });
  }

  function init() {
    document.querySelectorAll('form[data-newsletter-source]').forEach(bindForm);
  }

  window.DPNewsletterGeneral = Object.freeze({
    bindForm,
    errorMessage,
    honeypotValue,
    installHoneypot,
    isValidEmail,
    postNewsletter
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
'''
write('assets/newsletter-general.js', newsletter_general)

# 2) Keep script.js's legacy fallback correct, and delegate the actual POST to
# the shared V1 transport whenever the generated shell has loaded it.
replace_once(
    'script.js',
    'async function postNewsletter(payload) {\n  if (typeof navigator !== "undefined" && navigator.onLine === false) {',
    'async function postNewsletter(payload) {\n  if (window.DPNewsletterGeneral?.postNewsletter) {\n    return window.DPNewsletterGeneral.postNewsletter(payload);\n  }\n  if (typeof navigator !== "undefined" && navigator.onLine === false) {'
)
replace_once(
    'script.js',
    '        const emailEl = document.getElementById(emailId);\n        const statusEl = document.getElementById(statusId);',
    '        const emailEl = document.getElementById(emailId);\n        const gdprEl = document.getElementById(gdprId);\n        const statusEl = document.getElementById(statusId);'
)
replace_once(
    'script.js',
    '        if (!emailEl || !isValidNewsletterEmail(emailEl.value)) {\n          if (statusEl) statusEl.textContent = "Introduce un email válido.";\n          return;\n        }\n        if (statusEl) statusEl.textContent = "";',
    '        if (!emailEl || !isValidNewsletterEmail(emailEl.value)) {\n          if (statusEl) statusEl.textContent = "Introduce un email válido.";\n          return;\n        }\n        if (!gdprEl || !gdprEl.checked) {\n          if (statusEl) statusEl.textContent = "Acepta la política de privacidad para continuar.";\n          gdprEl?.focus({ preventScroll: true });\n          return;\n        }\n        if (statusEl) statusEl.textContent = "";'
)

# 3) Canonical Explore markup: consent + the shared runtime, generated once
# and propagated to every V1 page by build-site-shell.py.
builder = read('scripts/build-site-shell.py')
old_status = "        '      <p id=\"nl-status-explore\" class=\"form-status\" role=\"status\" aria-live=\"polite\"></p>\\n'\n        '    </form>\\n'\n        '  </div>\\n'\n        '</dialog>'"
new_status = "        '      <label class=\"form-consent\" for=\"nl-gdpr-explore\">\\n'\n        '        <input id=\"nl-gdpr-explore\" name=\"consent\" type=\"checkbox\" required aria-describedby=\"nl-status-explore\">\\n'\n        '        <span>He leído y acepto la <a href=\"/privacidad.html\">política de privacidad</a>.</span>\\n'\n        '      </label>\\n'\n        '      <p id=\"nl-status-explore\" class=\"form-status\" role=\"status\" aria-live=\"polite\"></p>\\n'\n        '    </form>\\n'\n        '  </div>\\n'\n        '</dialog>\\n'\n        '<script defer src=\"/assets/newsletter-general.js\"></script>'"
if builder.count(old_status) != 1:
    raise SystemExit(f'build-site-shell.py: explore form tail pattern count={builder.count(old_status)}')
write('scripts/build-site-shell.py', builder.replace(old_status, new_status, 1))

# 4) Static/fallback and inline forms. Generated Explore is handled by builder;
# these four are authored page-level forms and need their own checkbox once.
def add_inline_consent(rel, form_id, suffix):
    text = read(rel)
    if f'id="nl-gdpr-{suffix}"' in text:
        return
    start = text.find(f'id="{form_id}"')
    if start < 0:
        raise SystemExit(f'{rel}: form {form_id} not found')
    form_start = text.rfind('<form', 0, start)
    form_end = text.find('</form>', start)
    if form_start < 0 or form_end < 0:
        raise SystemExit(f'{rel}: malformed form {form_id}')
    segment = text[form_start:form_end]
    status_token = f'<p id="nl-status-{suffix}"'
    status_rel = segment.find(status_token)
    if status_rel < 0:
        raise SystemExit(f'{rel}: status for {form_id} not found')
    status_abs = form_start + status_rel
    line_start = text.rfind('\n', 0, status_abs) + 1
    indent = text[line_start:status_abs]
    consent = (
        f'{indent}<label class="form-consent" for="nl-gdpr-{suffix}">\n'
        f'{indent}  <input id="nl-gdpr-{suffix}" name="consent" type="checkbox" required aria-describedby="nl-status-{suffix}">\n'
        f'{indent}  <span>He leído y acepto la <a href="/privacidad.html">política de privacidad</a>.</span>\n'
        f'{indent}</label>\n'
    )
    write(rel, text[:line_start] + consent + text[line_start:])

add_inline_consent('index.html', 'newsletter-form-home', 'home')
add_inline_consent('fragmento/index.html', 'newsletter-form-fragmento', 'fragmento')
add_inline_consent('las-manecillas-del-recuerdo/index.html', 'newsletter-form-manecillas', 'manecillas')
add_inline_consent('cuaderno/index.html', 'newsletter-form-cuaderno', 'cuaderno')

# 5) Static contract: authority, parity, consent, payload and generated shell.
static_test = r'''import assert from 'node:assert/strict';
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

assert.match(builderSource, /id=\\"nl-gdpr-explore\\" name=\\"consent\\" type=\\"checkbox\\" required/,
  'shell builder must generate Explore consent');
assert.match(builderSource, /newsletter-general\.js/,
  'shell builder must load the shared general newsletter runtime');

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
'''
write('tests/test-newsletter-client-contract.mjs', static_test)

# 6) Browser contract: popup + three inline forms + Explore with script.js +
# shell-only Explore on Privacidad. Every checked submit must produce exactly
# one 201 DOI request, which proves the double-binding guard too.
browser_test = r'''import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const WORKER_PATTERN = 'https://subscribe.davidpd89.workers.dev/**';

async function pageWithWorker(context) {
  const page = await context.newPage();
  const requests = [];
  await page.route(WORKER_PATTERN, async (route) => {
    requests.push(route.request().postDataJSON());
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, state: 'pending_confirmation' })
    });
  });
  return { page, requests };
}

async function assertGeneralFlow(context, spec) {
  const { page, requests } = await pageWithWorker(context);
  await page.addInitScript(() => {
    try { localStorage.setItem('nl-popup-ts', String(Date.now())); } catch {}
  });
  const response = await page.goto(`${ORIGIN}${spec.path}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${spec.name}: page must load`);

  if (spec.openExplore) {
    const trigger = page.locator('[data-explore-open]').first();
    await trigger.click();
    await page.locator('[data-explore-dialog]').waitFor({ state: 'visible' });
  }
  if (spec.shellOnly) {
    assert.equal(await page.locator('script[src*="/script.js"]').count(), 0,
      `${spec.name}: shell-only fixture must remain independent from script.js`);
  }

  const form = page.locator(spec.form);
  const email = page.locator(spec.email);
  const consent = page.locator(spec.consent);
  const status = page.locator(spec.status);
  await form.waitFor({ state: 'attached' });
  await email.fill(`qa-${spec.source}@example.com`);
  assert.equal(await consent.isChecked(), false, `${spec.name}: consent starts unchecked`);
  assert.equal(await consent.getAttribute('required'), '', `${spec.name}: consent is required`);

  await form.locator('[type="submit"]').click();
  await page.waitForFunction((selector) => /Acepta la política de privacidad/i.test(
    document.querySelector(selector)?.textContent || ''
  ), spec.status);
  assert.match(await status.textContent(), /Acepta la política de privacidad/i,
    `${spec.name}: unchecked submit explains consent`);
  assert.equal(requests.length, 0, `${spec.name}: unchecked submit must make zero requests`);

  await consent.check();
  await form.locator('[type="submit"]').click();
  await page.waitForFunction((selector) => /Revisa tu correo/i.test(
    document.querySelector(selector)?.textContent || ''
  ), spec.form);
  assert.equal(requests.length, 1, `${spec.name}: checked submit must make exactly one request`);
  assert.deepEqual(requests[0], {
    email: `qa-${spec.source}@example.com`,
    source: spec.source,
    website: ''
  }, `${spec.name}: Worker payload must stay exact`);
  assert.ok(!Object.hasOwn(requests[0], 'consent'), `${spec.name}: payload must not contain consent`);
  await page.close();
}

const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });

  for (const spec of [
    { name: 'Fragmento inline', path: '/fragmento/', form: '#newsletter-form-fragmento', email: '#nl-email-fragmento', consent: '#nl-gdpr-fragmento', status: '#nl-status-fragmento', source: 'fragmento' },
    { name: 'Manecillas inline', path: '/las-manecillas-del-recuerdo/', form: '#newsletter-form-manecillas', email: '#nl-email-manecillas', consent: '#nl-gdpr-manecillas', status: '#nl-status-manecillas', source: 'manecillas' },
    { name: 'Cuaderno inline', path: '/cuaderno/', form: '#newsletter-form-cuaderno', email: '#nl-email-cuaderno', consent: '#nl-gdpr-cuaderno', status: '#nl-status-cuaderno', source: 'cuaderno' },
    { name: 'Explore with script.js', path: '/fragmento/', form: '#newsletter-form-explore', email: '#nl-email-explore', consent: '#nl-gdpr-explore', status: '#nl-status-explore', source: 'explore', openExplore: true },
    { name: 'Explore shell-only', path: '/privacidad.html', form: '#newsletter-form-explore', email: '#nl-email-explore', consent: '#nl-gdpr-explore', status: '#nl-status-explore', source: 'explore', openExplore: true, shellOnly: true }
  ]) {
    await assertGeneralFlow(context, spec);
  }

  const { page, requests } = await pageWithWorker(context);
  await page.addInitScript(() => {
    try {
      localStorage.removeItem('nl-popup-ts');
      localStorage.removeItem('nl-subscribed');
    } catch {}
  });
  const response = await page.goto(`${ORIGIN}/cuaderno/que-es-el-portal-fantasy/`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), 'popup representative article must load');
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  const email = dialog.locator('#nl-popup-email');
  const consent = dialog.locator('#nl-popup-gdpr');
  const status = dialog.locator('#nl-popup-status');
  const submit = dialog.locator('#nl-popup-submit');
  await email.fill('qa-newsletter@example.com');
  assert.equal(await consent.isChecked(), false, 'popup consent starts unchecked');
  await submit.click();
  await page.waitForFunction(() => /Acepta la política de privacidad/i.test(document.querySelector('#nl-popup-status')?.textContent || ''));
  assert.match(await status.textContent(), /Acepta la política de privacidad/i, 'popup unchecked submit explains consent');
  assert.equal(requests.length, 0, 'popup unchecked submit makes zero requests');
  await consent.check();
  await submit.click();
  await page.waitForFunction(() => document.querySelector('#nl-popup-panel')?.textContent?.includes('Revisa tu correo'));
  assert.equal(requests.length, 1, 'popup checked submit makes exactly one request');
  assert.deepEqual(requests[0], { email: 'qa-newsletter@example.com', source: 'popup', website: '' }, 'popup payload stays exact');
  await page.close();

  await context.close();
  console.log('newsletter-consent-browser: inline + Explore + shell-only + popup contracts passed');
} finally {
  await browser.close();
}
'''
write('qa/newsletter-consent-browser.mjs', browser_test)

# Regenerate every canonical V1 shell copy, then prove parity and static contract.
subprocess.run(['python3', 'scripts/build-site-shell.py'], cwd=ROOT, check=True)
subprocess.run(['python3', 'scripts/build-site-shell.py', '--check'], cwd=ROOT, check=True)
subprocess.run(['node', 'tests/test-newsletter-client-contract.mjs'], cwd=ROOT, check=True)

print('finish_newsletter_292: patch + builder + static contract PASS')
