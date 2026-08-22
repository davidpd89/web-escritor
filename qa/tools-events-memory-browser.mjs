import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const SENTINEL = 'LOCAL_QA_SENTINEL_582931';
const ARTIFACT_DIR = path.resolve('qa-artifacts/tools-events-memory');
await fs.mkdir(ARTIFACT_DIR, { recursive: true });

const CASES = [
  ['Eventos', '/herramientas/eventos-ics/', 'https://davidportodiaz.com/herramientas/eventos-ics/', 'Privacidad:', 'No uses esta herramienta'],
  ['Lectura', '/herramientas/tiempo-lectura-voz-alta/', 'https://davidportodiaz.com/herramientas/tiempo-lectura-voz-alta/', 'Privacidad', 'Una estimación, no un cronómetro'],
  ['Club', '/clubes-de-lectura/preparar-sesion/', 'https://davidportodiaz.com/clubes-de-lectura/preparar-sesion/', 'No se guarda ni se envía', 'Cómo usar las preguntas'],
  ['Entrevista', '/herramientas/entrevista-familiar/', 'https://davidportodiaz.com/herramientas/entrevista-familiar/', 'No se guarda ningún nombre', 'Cómo está diseñada'],
  ['Objeto', '/recursos/ficha-historia-objeto-heredado/', 'https://davidportodiaz.com/recursos/ficha-historia-objeto-heredado/', 'Privacidad:', 'no sustituye asesoramiento profesional'],
];

const browser = await chromium.launch({ headless: true });
const failures = [];
const runtime = new Map();

function check(condition, message) {
  try { assert.ok(condition, message); }
  catch (error) { failures.push(error.message); console.error(`FALLA: ${error.message}`); }
}

function equal(actual, expected, message) {
  try { assert.equal(actual, expected, message); }
  catch (error) { failures.push(error.message); console.error(`FALLA: ${error.message}\n${error.message.includes('Expected') ? '' : ''}`); }
}

async function makeContext(options = {}) {
  return browser.newContext({
    viewport: { width: 1440, height: 1000 },
    locale: 'es-ES',
    permissions: ['clipboard-read', 'clipboard-write'],
    ...options,
  });
}

async function instrument(page, key) {
  const state = { page, errors: [], consoleErrors: [], requests: [] };
  page.on('pageerror', (error) => state.errors.push(String(error)));
  page.on('console', (msg) => { if (msg.type() === 'error') state.consoleErrors.push(msg.text()); });
  page.on('request', (request) => state.requests.push({ url: request.url(), method: request.method(), body: request.postData() || '' }));
  await page.addInitScript(() => {
    window.__qaApiCalls = [];
    window.__qaCls = 0;
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__qaCls += entry.value;
      }).observe({ type: 'layout-shift', buffered: true });
    } catch {}
    const record = (type, url, body = '') => window.__qaApiCalls.push({ type, url: String(url || ''), body: String(body || '') });
    if (window.fetch) {
      const original = window.fetch.bind(window);
      window.fetch = (input, init = {}) => { record('fetch', typeof input === 'string' ? input : input?.url, init?.body); return original(input, init); };
    }
    if (window.XMLHttpRequest) {
      const Original = window.XMLHttpRequest;
      window.XMLHttpRequest = class extends Original {
        open(method, url, ...rest) { this.__qaUrl = url; return super.open(method, url, ...rest); }
        send(body) { record('xhr', this.__qaUrl, body); return super.send(body); }
      };
    }
    if (navigator.sendBeacon) {
      const original = navigator.sendBeacon.bind(navigator);
      navigator.sendBeacon = (url, data) => { record('beacon', url, data); return original(url, data); };
    }
    if (window.WebSocket) {
      const Original = window.WebSocket;
      window.WebSocket = class extends Original {
        constructor(url, protocols) { record('websocket', url); super(url, protocols); }
      };
    }
  });
  runtime.set(key, state);
}

async function assertRuntimeClean(key) {
  const state = runtime.get(key);
  const apiCalls = await state.page.evaluate(() => window.__qaApiCalls || []);
  const leaked = [...state.requests, ...apiCalls]
    .map((r) => `${r.url || ''}\n${r.body || ''}`)
    .filter((value) => value.includes(SENTINEL));
  check(leaked.length === 0, `${key}: el sentinel apareció en una operación de red`);
  check(state.errors.length === 0, `${key}: pageerror: ${state.errors.join(' | ')}`);
  check(state.consoleErrors.length === 0, `${key}: console.error: ${state.consoleErrors.join(' | ')}`);
  const external = state.requests.filter((r) => {
    try { return new URL(r.url).origin !== new URL(BASE).origin; } catch { return true; }
  });
  check(external.length === 0, `${key}: hubo solicitudes externas automáticas: ${external.map((r) => r.url).join(', ')}`);
  const cls = await state.page.evaluate(() => window.__qaCls || 0);
  check(cls <= 0.1, `${key}: CLS ${cls.toFixed(4)} > 0.1`);
}

async function assertLabels(page, key) {
  const result = await page.evaluate(() => {
    const controls = [...document.querySelectorAll('input, select, textarea')].filter((el) => el.type !== 'hidden');
    const unlabeled = controls.filter((el) => {
      if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return false;
      if (el.closest('label')) return false;
      return !(el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`));
    }).map((el) => el.outerHTML.slice(0, 180));
    const positiveTabindex = [...document.querySelectorAll('[tabindex]')].filter((el) => Number(el.getAttribute('tabindex')) > 0).length;
    const inaccessibleVisible = [...document.querySelectorAll('a[href],button,input,select,textarea')]
      .filter((el) => !el.disabled && el.type !== 'hidden' && getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden')
      .filter((el) => el.tabIndex < 0)
      .map((el) => el.outerHTML.slice(0, 180));
    return { unlabeled, positiveTabindex, inaccessibleVisible };
  });
  check(result.unlabeled.length === 0, `${key}: controles sin label: ${result.unlabeled.join(' || ')}`);
  equal(result.positiveTabindex, 0, `${key}: no debe haber tabindex positivo`);
  check(result.inaccessibleVisible.length === 0, `${key}: controles visibles fuera del orden de tabulación: ${result.inaccessibleVisible.join(' || ')}`);
}

async function assertSkipLink(page, key) {
  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('Tab');
  check(await page.evaluate(() => document.activeElement?.classList.contains('skip-link')), `${key}: el primer Tab debe alcanzar el skip link`);
}

async function assertMetadata(page, key, canonical) {
  check((await page.title()).trim().length > 0, `${key}: falta title`);
  equal(await page.locator('link[rel="canonical"]').getAttribute('href'), canonical, `${key}: canonical`);
  check((await page.locator('meta[name="robots"]').getAttribute('content') || '').includes('index'), `${key}: robots index`);
  const ld = await page.locator('script[type="application/ld+json"]').first().textContent();
  try { JSON.parse(ld); } catch { check(false, `${key}: JSON-LD estático no parseable`); }
}

async function assertResponsive(page, key) {
  for (const viewport of [
    { width: 320, height: 900 },
    { width: 390, height: 844 },
    { width: 768, height: 900 },
    { width: 1024, height: 900 },
    { width: 1440, height: 1000 },
    { width: 844, height: 390 },
  ]) {
    await page.setViewportSize(viewport);
    await page.waitForTimeout(50);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(overflow <= 1, `${key}: overflow horizontal ${overflow}px en ${viewport.width}x${viewport.height}`);
  }
}

async function addQaStyles(page) {
  await page.evaluate(() => new Promise((resolve, reject) => {
    if (document.querySelector('link[data-qa-text-resilience]')) return resolve();
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/qa/tools-events-memory-text-resilience.css';
    link.dataset.qaTextResilience = 'true';
    link.onload = resolve;
    link.onerror = reject;
    document.head.append(link);
  }));
}

async function assertTextResilience(page, key) {
  await addQaStyles(page);
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.evaluate(() => document.documentElement.classList.add('qa-text-200'));
  await page.waitForTimeout(80);
  let overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${key}: overflow con texto al 200% (${overflow}px)`);
  await page.evaluate(() => document.documentElement.classList.remove('qa-text-200'));

  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => document.documentElement.classList.add('qa-text-spacing'));
  await page.waitForTimeout(80);
  overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${key}: overflow con text-spacing (${overflow}px)`);
}

async function screenshot(page, filename, width, height) {
  await page.setViewportSize({ width, height });
  await page.screenshot({ path: path.join(ARTIFACT_DIR, filename), fullPage: true });
}

async function waitStatus(page, selector, text) {
  await page.waitForFunction(({ selector, text }) => document.querySelector(selector)?.textContent?.includes(text), { selector, text });
}

async function testEvent() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Eventos');
  await page.goto(`${BASE}/herramientas/eventos-ics/`, { waitUntil: 'networkidle' });
  await assertMetadata(page, 'Eventos', CASES[0][2]);
  await assertSkipLink(page, 'Eventos');

  await page.fill('#ev-offset', '+02:00');
  check(await page.locator('#ev-offset').evaluate((el) => el.checkValidity()), 'Eventos: +02:00 debe ser válido en HTML');
  await page.fill('#ev-offset', '+14:30');
  check(!(await page.locator('#ev-offset').evaluate((el) => el.checkValidity())), 'Eventos: +14:30 debe ser inválido en HTML');
  await page.fill('#ev-offset', '-14:00');
  check(await page.locator('#ev-offset').evaluate((el) => el.checkValidity()), 'Eventos: -14:00 debe ser válido en HTML');

  const description = `${SENTINEL}\nCon ñ, áéíóú, coma, punto y coma; barra \\ — y «comillas».\n<script>alert(1)</script>`;
  await page.fill('#ev-name', 'Presentación de novela');
  await page.fill('#ev-url', 'https://example.test/eventos/presentacion/');
  await page.fill('#ev-desc', description);
  await page.fill('#ev-start-dt', '2026-09-10T19:00');
  await page.fill('#ev-end-dt', '2026-09-10T20:30');
  await page.fill('#ev-offset', '+02:00');
  await page.fill('#ev-venue', 'Librería Ejemplo');
  await page.fill('#ev-street', 'Calle Mayor 1');
  await page.fill('#ev-locality', 'Madrid');
  await page.fill('#ev-postal', '28013');
  await page.fill('#ev-region', 'Madrid');
  await page.fill('#ev-country', 'ES');
  await page.fill('#ev-org', 'Editorial Ejemplo');
  await page.fill('#ev-org-url', 'https://example.test/');
  await page.check('input[name="confirmed"]');
  await page.click('button[type="submit"]');
  check(!(await page.locator('[data-event-results]').isHidden()), 'Eventos E1: resultado visible');

  const html = await page.locator('[data-event-html]').inputValue();
  check(html.includes('&lt;script&gt;alert(1)&lt;/script&gt;') && !html.includes('<script>alert'), 'Eventos E1: HTML escapa input hostil');
  const wrapped = await page.locator('[data-event-jsonld]').inputValue();
  const jsonText = wrapped.replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  const schema = JSON.parse(jsonText);
  equal(schema['@type'], 'Event', 'Eventos E1: JSON-LD Event');
  equal(schema.startDate, '2026-09-10T19:00:00+02:00', 'Eventos E1: startDate');
  equal(schema.endDate, '2026-09-10T20:30:00+02:00', 'Eventos E1: endDate');

  await page.click('[data-copy-target="[data-event-html]"]');
  await page.waitForFunction(() => [...document.querySelectorAll('[data-copy-target]')].some((b) => b.textContent === 'Copiado'));

  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-event-ics]');
  const download = await downloadPromise;
  const icsPath = path.join(ARTIFACT_DIR, 'event-test.ics');
  await download.saveAs(icsPath);
  const ics = await fs.readFile(icsPath, 'utf8');
  const unfolded = ics.replace(/\r\n[ \t]/g, '');
  for (const required of ['BEGIN:VCALENDAR','VERSION:2.0','BEGIN:VEVENT','DTSTART:20260910T170000Z','DTEND:20260910T183000Z','SUMMARY:Presentación de novela','UID:','DTSTAMP:','END:VEVENT','END:VCALENDAR']) {
    check(unfolded.includes(required), `Eventos E1 ICS: falta ${required}`);
  }
  check(!/(^|[^\r])\n/.test(ics), 'Eventos ICS: no debe contener LF sin CR');
  check(unfolded.includes('punto y coma\\; barra \\\\'), 'Eventos ICS: escapado de ; y \\');
  for (const line of ics.split('\r\n')) check(new TextEncoder().encode(line).length <= 75, `Eventos ICS: línea >75 bytes`);

  await page.check('input[name="allDay"]');
  await page.fill('#ev-start-date', '2026-09-10');
  await page.fill('#ev-end-date', '');
  await page.click('button[type="submit"]');
  let json = (await page.locator('[data-event-jsonld]').inputValue()).replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  equal(JSON.parse(json).startDate, '2026-09-10', 'Eventos E2: JSON-LD all-day');
  const oneDay = await page.evaluate(async () => {
    const { buildEventOutputs } = await import('/assets/evento-escritor-core.js');
    return buildEventOutputs({ name:'Día completo', url:'https://example.test/e/', description:'', venueName:'Lugar', streetAddress:'Calle 1', addressLocality:'Madrid', postalCode:'', addressRegion:'', addressCountry:'ES', organizerName:'', organizerUrl:'', imageUrl:'', allDay:true, startDate:'2026-09-10', endDate:'', startDateTime:'', endDateTime:'', utcOffset:'', confirmed:true }).ics;
  });
  check(oneDay.includes('DTSTART;VALUE=DATE:20260910') && oneDay.includes('DTEND;VALUE=DATE:20260911'), 'Eventos E2: DTEND exclusivo');
  await page.fill('#ev-end-date', '2026-09-12');
  await page.click('button[type="submit"]');
  json = (await page.locator('[data-event-jsonld]').inputValue()).replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  equal(JSON.parse(json).endDate, '2026-09-12', 'Eventos E3: JSON-LD multiday');

  const invalidCount = await page.evaluate(async () => {
    const { validateEventModel } = await import('/assets/evento-escritor-core.js');
    const base = { name:'Evento', url:'https://example.test/e/', description:'', venueName:'Lugar', streetAddress:'Calle 1', addressLocality:'Madrid', postalCode:'', addressRegion:'', addressCountry:'ES', organizerName:'Org', organizerUrl:'https://example.test/', imageUrl:'https://example.test/x.jpg', allDay:false, startDateTime:'2026-09-10T19:00', endDateTime:'2026-09-10T20:00', utcOffset:'+02:00', confirmed:true };
    const patches = [{name:''},{url:''},{url:'http://example.test/'},{startDateTime:''},{endDateTime:'2026-09-10T18:00'},{utcOffset:'x'},{utcOffset:'+14:30'},{venueName:''},{streetAddress:''},{addressLocality:''},{addressCountry:''},{confirmed:false},{imageUrl:'javascript:alert(1)'},{organizerUrl:'http://example.test/'},{startDateTime:'2026-02-31T19:00'}];
    return patches.filter((patch) => validateEventModel({...base,...patch}).length > 0).length;
  });
  equal(invalidCount, 15, 'Eventos E4: inválidos rechazados');

  await screenshot(page, 'event-390-result.png', 390, 844);
  await assertLabels(page, 'Eventos');
  await assertResponsive(page, 'Eventos');
  await assertRuntimeClean('Eventos');
  await context.close();
}

async function testReadAloud() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Lectura');
  await page.goto(`${BASE}/herramientas/tiempo-lectura-voz-alta/`, { waitUntil: 'networkidle' });
  await assertMetadata(page, 'Lectura', CASES[1][2]);
  await assertSkipLink(page, 'Lectura');
  await page.fill('[data-readaloud-manual-words]', '930');
  await page.fill('[data-readaloud-wpm]', '155');
  await page.fill('[data-readaloud-buffer]', '10');
  await page.fill('[data-readaloud-target]', '5');
  await page.click('[data-readaloud-form] button[type="submit"]');
  equal(await page.locator('[data-readaloud-word-count]').textContent(), '930', 'Lectura: palabras');
  equal(await page.locator('[data-readaloud-duration]').textContent(), '6 min 36 s', 'Lectura: duración');
  check((await page.locator('[data-readaloud-capacity]').textContent()).startsWith('704 '), 'Lectura: capacidad 704');
  equal(await page.locator('[data-readaloud-effective]').textContent(), '141 ppm efectivas', 'Lectura: ritmo efectivo');
  await page.fill('[data-readaloud-text]', `${SENTINEL} —rayas «comillas» ¿signos?\ntexto español`);
  await page.fill('[data-readaloud-manual-words]', '9999');
  await page.click('[data-readaloud-form] button[type="submit"]');
  check((await page.locator('[data-readaloud-word-count]').textContent()) !== '9.999', 'Lectura: texto prevalece sobre manual');
  check(!/NaN|Infinity|undefined|null/.test(await page.locator('[data-readaloud-results]').innerText()), 'Lectura: UI finita');
  await page.click('[data-readaloud-clear]');
  check(await page.locator('[data-readaloud-results]').isHidden(), 'Lectura: Borrar oculta resultado');
  await assertLabels(page, 'Lectura');
  await assertResponsive(page, 'Lectura');
  await assertRuntimeClean('Lectura');
  await context.close();
}

async function testClub() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Club');
  await page.goto(`${BASE}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'networkidle' });
  await assertMetadata(page, 'Club', CASES[2][2]);
  await assertSkipLink(page, 'Club');
  const hostileTitle = `${SENTINEL} <img src=x onerror=alert(1)> El reloj`;
  await page.fill('#club-title', hostileTitle);
  await page.fill('#club-author', 'Elena Ñúñez');
  await page.selectOption('#club-kind', 'fiction');
  await page.selectOption('#club-genre', 'fantasy');
  await page.selectOption('#club-duration', '60');
  await page.selectOption('#club-tone', 'balanced');
  await page.selectOption('#club-scope', 'partial');
  await page.fill('#club-tokens', 'memoria, familia, Elena, reloj, ignorado');
  await page.click('[data-club-session-form] button[type="submit"]');
  const first = await page.locator('[data-club-session-output]').innerText();
  check(first.includes('60 min') && first.includes('lectura parcial'), 'Club: resultado parcial');
  check(!/\b(final|terminar|terminaste|acabó|cierre)\b|después de terminar|llegar al final|principio y el final/i.test(first.split('Cierre ·')[0]), 'Club: parcial sin preguntas de desenlace');
  equal(await page.locator('[data-club-session-output] img, [data-club-session-output] script').count(), 0, 'Club: input hostil no crea nodos');
  await page.click('[data-club-session-alt]');
  const second = await page.locator('[data-club-session-output]').innerText();
  check(first !== second, 'Club: Otra combinación cambia resultado');
  equal(await page.locator('#club-title').inputValue(), hostileTitle, 'Club: conserva título');
  await page.click('[data-club-session-copy]');
  await waitStatus(page, '[data-club-session-status]', 'copiada');

  const matrix = await page.evaluate(async () => {
    const { buildSession } = await import('/assets/club-session-engine.js');
    const genres = ['general','fantasy','scifi','mystery','romance','historical','contemporary','horror','memoir'];
    const durations = [30,60,90].map((duration) => { const r = buildSession({kind:'fiction',genre:'general',tone:'balanced',duration,scope:'complete'}, 0); return [duration, r.timing.opening + r.timing.core + r.timing.close]; });
    const validGenres = genres.every((genre) => buildSession({kind:'fiction',genre,tone:'balanced',duration:60,scope:'complete'},0).questions.length > 0);
    const kindsDiffer = buildSession({kind:'fiction',duration:60},0).questions.join('\n') !== buildSession({kind:'nonfiction',duration:60},0).questions.join('\n');
    const tones = ['social','balanced','deep'].map((tone) => buildSession({kind:'fiction',tone,duration:60},0).questions.join('\n'));
    return { durations, validGenres, kindsDiffer, tonesDiffer:new Set(tones).size === 3 };
  });
  check(matrix.validGenres && matrix.kindsDiffer && matrix.tonesDiffer, 'Club: matriz de tipo/género/tono');
  for (const [duration,total] of matrix.durations) equal(total, duration, `Club: agenda ${duration}`);

  await screenshot(page, 'club-390-result.png', 390, 844);
  await page.emulateMedia({ media:'print' });
  equal(await page.locator('.site-header').evaluate((el) => getComputedStyle(el).display), 'none', 'Club print: header oculto');
  await page.pdf({ path:path.join(ARTIFACT_DIR,'club-print.pdf'), format:'A4', printBackground:true });
  await page.emulateMedia({ media:'screen' });
  await assertLabels(page, 'Club');
  await assertResponsive(page, 'Club');
  await assertRuntimeClean('Club');
  await context.close();
}

async function testInterview() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Entrevista');
  await page.emulateMedia({ reducedMotion:'reduce' });
  await page.goto(`${BASE}/herramientas/entrevista-familiar/`, { waitUntil:'networkidle' });
  await assertMetadata(page, 'Entrevista', CASES[3][2]);
  await assertSkipLink(page, 'Entrevista');
  await page.fill('#family-name', `${SENTINEL} <img src=x onerror=alert(1)> María Ñúñez`);
  await page.fill('#family-relation', 'amigo de la familia');
  await page.selectOption('#family-duration', '30');
  await page.check('input[name="theme"][value="dificil"]');
  await page.check('input[name="objectMode"]');
  await page.click('[data-family-interview-form] button[type="submit"]');
  check(!(await page.locator('[data-family-sensitive-note]').isHidden()), 'Entrevista: aviso sensible visible');
  const text = await page.locator('[data-family-interview-results]').innerText();
  check(text.includes(SENTINEL) && /foto|objeto/i.test(text), 'Entrevista: meta y object mode');
  check(text.includes('prefiero no hablar de eso') && text.includes('cambia de asunto'), 'Entrevista: límites sensibles');
  equal(await page.locator('[data-family-interview-results] img, [data-family-interview-results] script').count(), 0, 'Entrevista: input hostil no crea nodos');
  await page.uncheck('input[name="theme"][value="dificil"]');
  await page.click('[data-family-interview-form] button[type="submit"]');
  check(await page.locator('[data-family-sensitive-note]').isHidden(), 'Entrevista: aviso sensible se oculta');
  const durationCounts = await page.evaluate(async () => { const { buildInterviewPlan } = await import('/assets/entrevista-familiar-core.js'); return [15,30,45,60].map((duration) => buildInterviewPlan({duration,themes:['infancia','familia'],objectMode:false}).questions.length); });
  check(durationCounts.every((n) => n > 0), 'Entrevista: 15/30/45/60 generan preguntas');
  for (const link of await page.locator('.tool-caveat a[target="_blank"]').all()) {
    const rel = await link.getAttribute('rel');
    check(rel?.includes('noopener') && rel?.includes('noreferrer'), 'Entrevista: enlace externo seguro');
  }
  await page.emulateMedia({ media:'print' });
  equal(await page.locator('.site-header').evaluate((el) => getComputedStyle(el).display), 'none', 'Entrevista print: header oculto');
  await page.pdf({ path:path.join(ARTIFACT_DIR,'interview-print.pdf'), format:'A4', printBackground:true });
  await page.emulateMedia({ media:'screen' });
  await assertLabels(page, 'Entrevista');
  await assertResponsive(page, 'Entrevista');
  await assertRuntimeClean('Entrevista');
  await context.close();
}

async function fillRow(page, kind, index, values) {
  const row = page.locator(`[data-rows="${kind}"] [data-row]`).nth(index);
  for (const [key,value] of Object.entries(values)) await row.locator(`[data-key="${key}"]`).fill(String(value));
}

async function exportObject(page, filename) {
  const promise = page.waitForEvent('download');
  await page.click('[data-record-export]');
  const download = await promise;
  const file = path.join(ARTIFACT_DIR, filename);
  await download.saveAs(file);
  return { file, text:await fs.readFile(file,'utf8') };
}

function semanticRecord(value) { const copy = structuredClone(value); delete copy.exported_at; return copy; }

async function testObject() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Objeto');
  await page.goto(`${BASE}/recursos/ficha-historia-objeto-heredado/`, { waitUntil:'networkidle' });
  await assertMetadata(page, 'Objeto', CASES[4][2]);
  await assertSkipLink(page, 'Objeto');
  await assertLabels(page, 'Objeto');
  for (const kind of ['photos','owners','evidence','oral_history','timeline']) equal(await page.locator(`[data-rows="${kind}"] [data-row]`).count(), 1, `Objeto: fila inicial ${kind}`);

  const title = `${SENTINEL} · Reloj «A Coruña» — ñ`;
  await page.locator('[data-object-field="title"]').fill(title);
  await page.locator('[data-object-field="marks"]').fill('N.º 1842\nÁÉÍÓÚ · ü');
  await page.locator('[data-conservation-field="observed_on"]').fill('2026-08-21');
  await page.locator('[data-conservation-field="risks"]').fill('Humedad y sol directo');
  await page.locator('[data-open-questions]').fill('¿Quién cambió la esfera?\n¿Existe una foto de 1960?\n¿Qué significa GN-42?');
  await page.click('[data-add-row="photos"]');
  for (let i=1;i<3;i++) await page.click('[data-add-row="owners"]');
  for (let i=1;i<3;i++) await page.click('[data-add-row="evidence"]');
  await page.click('[data-add-row="oral_history"]');
  for (let i=1;i<4;i++) await page.click('[data-add-row="timeline"]');
  await fillRow(page,'photos',0,{filename:'frente-ñ.jpg',view:'Frente',note:'Esfera'});
  await fillRow(page,'photos',1,{filename:'reverso.jpg',view:'Reverso',note:'Marca'});
  await fillRow(page,'owners',0,{person:'María Núñez',from:'1942',to:'1968',location:'A Coruña',transfer:'Compra',source_ids:'F01'});
  await fillRow(page,'owners',1,{person:'José Díaz',from:'1968',to:'2003',location:'Pontevedra',transfer:'Herencia',source_ids:'F02, F03'});
  await fillRow(page,'owners',2,{person:'Elena Porto',from:'2003',to:'actualidad',location:'Madrid',transfer:'Regalo',source_ids:'F03'});
  await fillRow(page,'evidence',0,{id:'F01',type:'Factura',description:'Compra',location:'Caja 2',checked_on:'2026-08-18'});
  await fillRow(page,'evidence',1,{id:'F02',type:'Entrevista',description:'Mudanza',location:'Audio local',checked_on:'2026-08-19'});
  await fillRow(page,'evidence',2,{id:'F03',type:'Fotografía',description:'Reloj en salón',location:'Álbum 4',checked_on:'2026-08-20'});
  await fillRow(page,'oral_history',0,{speaker:'Ana Núñez',interview_date:'2026-08-18',summary:`${SENTINEL}: «Sonaba cada media hora»`,source_ids:'F02'});
  await fillRow(page,'oral_history',1,{speaker:'Elena Porto',interview_date:'2026-08-19',summary:'No sabe quién cambió la esfera',source_ids:'F03'});
  for (let i=0;i<4;i++) await fillRow(page,'timeline',i,{from:['1942','1968','1978','2003'][i],to:i===3?'actualidad':'',event:['Compra','Herencia','Reparación probable','Traslado'][i],source_ids:i===0?'F01':'F02, F03'});

  const first = await exportObject(page,'object-roundtrip.json');
  const parsed = JSON.parse(first.text);
  equal(parsed.photos.length,2,'Objeto: 2 fotos'); equal(parsed.owners.length,3,'Objeto: 3 propietarios'); equal(parsed.evidence.length,3,'Objeto: 3 evidencias'); equal(parsed.oral_history.length,2,'Objeto: 2 memorias'); equal(parsed.timeline.length,4,'Objeto: 4 hechos');

  page.once('dialog', (dialog) => dialog.dismiss());
  await page.click('[data-record-clear]');
  equal(await page.locator('[data-object-field="title"]').inputValue(), title, 'Objeto: cancelar Vaciar conserva datos');
  page.once('dialog', (dialog) => dialog.accept());
  await page.click('[data-record-clear]');
  equal(await page.locator('[data-object-field="title"]').inputValue(), '', 'Objeto: Vaciar limpia datos');
  check(await page.locator('[data-object-field="title"]').evaluate((el) => document.activeElement === el), 'Objeto: Vaciar devuelve foco al inicio');
  for (const kind of ['photos','owners','evidence','oral_history','timeline']) equal(await page.locator(`[data-rows="${kind}"] [data-row]`).count(),1,`Objeto: Vaciar restaura fila ${kind}`);

  await page.locator('[data-record-import]').setInputFiles({ name:'roundtrip.json', mimeType:'application/json', buffer:Buffer.from(first.text) });
  await waitStatus(page,'[data-record-status]','cargado');
  equal(await page.locator('[data-object-field="title"]').inputValue(), title, 'Objeto: import restaura Unicode');
  const second = await exportObject(page,'object-roundtrip-reexport.json');
  try { assert.deepEqual(semanticRecord(JSON.parse(second.text)), semanticRecord(parsed)); } catch (error) { check(false, `Objeto: roundtrip semántico: ${error.message}`); }

  const before = await page.locator('[data-object-field="title"]').inputValue();
  await page.locator('[data-record-import]').setInputFiles({ name:'malformed.json', mimeType:'application/json', buffer:Buffer.from('{ "foo":') });
  await waitStatus(page,'[data-record-status]','No se pudo abrir');
  equal(await page.locator('[data-object-field="title"]').inputValue(), before, 'Objeto: JSON malformado conserva ficha');

  const hostile = JSON.stringify({ schema_version:1, object:{title:'<img src=x onerror=alert(1)>'} });
  await page.locator('[data-record-import]').setInputFiles({ name:'hostile.json', mimeType:'application/json', buffer:Buffer.from(hostile) });
  await waitStatus(page,'[data-record-status]','cargado');
  equal(await page.locator('[data-object-record] img, [data-object-record] script').count(),0,'Objeto: JSON hostil no crea nodos');

  await page.click('[data-add-row="photos"]');
  equal(await page.evaluate(() => document.activeElement?.getAttribute('data-key')), 'filename', 'Objeto: añadir mueve foco');
  await page.locator('[data-rows="photos"] [data-row]').last().locator('[data-remove]').click();
  check(await page.locator('[data-add-row="photos"]').evaluate((el) => document.activeElement === el), 'Objeto: eliminar devuelve foco');
  await page.emulateMedia({ media:'print' });
  equal(await page.locator('.site-header').evaluate((el) => getComputedStyle(el).display), 'none', 'Objeto print: header oculto');
  await page.pdf({ path:path.join(ARTIFACT_DIR,'object-print.pdf'), format:'A4', printBackground:true });
  await page.emulateMedia({ media:'screen' });
  await assertResponsive(page,'Objeto');
  await assertRuntimeClean('Objeto');
  await context.close();
}

async function testNoJs() {
  const context = await makeContext({ javaScriptEnabled:false });
  for (const [key,route,canonical,privacyText,limitationText] of CASES) {
    const page = await context.newPage();
    await page.goto(`${BASE}${route}`, { waitUntil:'load' });
    await assertMetadata(page,key,canonical);
    for (const selector of ['.site-header','.primary-nav','h1','.site-footer']) check(await page.locator(selector).count() > 0, `No-JS ${key}: falta ${selector}`);
    const body = await page.locator('body').innerText();
    check(body.includes(privacyText), `No-JS ${key}: falta privacidad visible`);
    check(body.includes(limitationText), `No-JS ${key}: falta limitación/metodología visible`);
    await assertLabels(page,`No-JS ${key}`);
    await page.close();
  }
  await context.close();
}

try {
  await testEvent();
  await testReadAloud();
  await testClub();
  await testInterview();
  await testObject();
  await testNoJs();

  for (const [key,route] of CASES.map(([key,route]) => [key,route])) {
    const context = await makeContext();
    const page = await context.newPage();
    await page.goto(`${BASE}${route}`, { waitUntil:'networkidle' });
    await assertTextResilience(page,key);
    await context.close();
  }

  console.log('INPUT EXFILTRATION: 0/5');
  console.log(`QA artifacts: ${ARTIFACT_DIR}`);
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(`\n${failures.length} fallo(s) de QA:`);
  failures.forEach((failure,index) => console.error(`${index + 1}. ${failure}`));
  process.exit(1);
}

console.log('qa/tools-events-memory-browser: OK');
