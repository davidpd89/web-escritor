import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const SENTINEL = 'LOCAL_QA_SENTINEL_582931';
const ARTIFACT_DIR = path.resolve('qa-artifacts/tools-events-memory');
await fs.mkdir(ARTIFACT_DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const failures = [];
const privacy = new Map();

function check(condition, message) {
  try { assert.ok(condition, message); }
  catch (error) { failures.push(error.message); console.error(`FALLA: ${error.message}`); }
}

function equal(actual, expected, message) {
  try { assert.equal(actual, expected, message); }
  catch (error) { failures.push(error.message); console.error(`FALLA: ${error.message}`); }
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
  const errors = [];
  const consoleErrors = [];
  const requests = [];
  page.on('pageerror', (error) => errors.push(String(error)));
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('request', (request) => requests.push({ url: request.url(), method: request.method(), body: request.postData() || '' }));
  await page.addInitScript(() => {
    window.__qaApiCalls = [];
    window.__qaCls = 0;
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__qaCls += entry.value;
        }
      }).observe({ type: 'layout-shift', buffered: true });
    } catch {}

    const record = (type, url, body = '') => window.__qaApiCalls.push({ type, url: String(url || ''), body: String(body || '') });
    if (window.fetch) {
      const originalFetch = window.fetch.bind(window);
      window.fetch = (input, init = {}) => {
        record('fetch', typeof input === 'string' ? input : input?.url, init?.body);
        return originalFetch(input, init);
      };
    }
    if (window.XMLHttpRequest) {
      const OriginalXHR = window.XMLHttpRequest;
      window.XMLHttpRequest = class extends OriginalXHR {
        open(method, url, ...rest) { this.__qaUrl = url; return super.open(method, url, ...rest); }
        send(body) { record('xhr', this.__qaUrl, body); return super.send(body); }
      };
    }
    if (navigator.sendBeacon) {
      const originalBeacon = navigator.sendBeacon.bind(navigator);
      navigator.sendBeacon = (url, data) => { record('beacon', url, data); return originalBeacon(url, data); };
    }
    if (window.WebSocket) {
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = class extends OriginalWebSocket {
        constructor(url, protocols) { record('websocket', url); super(url, protocols); }
      };
    }
  });
  privacy.set(key, { page, errors, consoleErrors, requests });
  return { errors, consoleErrors, requests };
}

async function assertRuntimeClean(key) {
  const state = privacy.get(key);
  const apiCalls = await state.page.evaluate(() => window.__qaApiCalls || []);
  const leaked = [
    ...state.requests.map((r) => `${r.url}\n${r.body}`),
    ...apiCalls.map((r) => `${r.url}\n${r.body}`),
  ].filter((value) => value.includes(SENTINEL));
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
  const unlabeled = await page.evaluate(() => [...document.querySelectorAll('input, select, textarea')]
    .filter((el) => el.type !== 'hidden')
    .filter((el) => {
      if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return false;
      if (el.closest('label')) return false;
      return !(el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`));
    })
    .map((el) => el.outerHTML.slice(0, 180)));
  check(unlabeled.length === 0, `${key}: controles sin label: ${unlabeled.join(' || ')}`);
  const positiveTabindex = await page.locator('[tabindex]').evaluateAll((nodes) => nodes.filter((n) => Number(n.getAttribute('tabindex')) > 0).length);
  equal(positiveTabindex, 0, `${key}: no debe haber tabindex positivo`);
}

async function assertSkipLink(page, key) {
  await page.evaluate(() => document.activeElement?.blur());
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => document.activeElement?.classList.contains('skip-link'));
  check(focused, `${key}: el primer Tab debe alcanzar el skip link`);
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
    await page.waitForTimeout(40);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(overflow <= 1, `${key}: overflow horizontal ${overflow}px en ${viewport.width}x${viewport.height}`);
  }
}

async function assertTextResilience(page, key) {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addStyleTag({ content: `html { font-size: 200% !important; } body { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; }` });
  await page.waitForTimeout(50);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  check(overflow <= 1, `${key}: overflow con texto al 200% / text-spacing (${overflow}px)`);
}

async function screenshot(page, filename, width, height) {
  await page.setViewportSize({ width, height });
  await page.screenshot({ path: path.join(ARTIFACT_DIR, filename), fullPage: true });
}

async function testEvent() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Eventos');
  await page.goto(`${BASE}/herramientas/eventos-ics/`, { waitUntil: 'networkidle' });
  await assertSkipLink(page, 'Eventos');

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
  check(html.includes('Presentación de novela'), 'Eventos E1: HTML conserva el nombre');
  check(html.includes('&lt;script&gt;alert(1)&lt;/script&gt;'), 'Eventos E1: HTML escapa script');
  check(!html.includes('<script>alert'), 'Eventos E1: HTML no ejecutable');

  const wrapped = await page.locator('[data-event-jsonld]').inputValue();
  const jsonText = wrapped.replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  const schema = JSON.parse(jsonText);
  equal(schema['@type'], 'Event', 'Eventos E1: JSON-LD Event');
  equal(schema.startDate, '2026-09-10T19:00:00+02:00', 'Eventos E1: startDate');
  equal(schema.endDate, '2026-09-10T20:30:00+02:00', 'Eventos E1: endDate');
  equal(schema.location.name, 'Librería Ejemplo', 'Eventos E1: lugar');
  equal(schema.organizer.name, 'Editorial Ejemplo', 'Eventos E1: organizador');

  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-event-ics]');
  const download = await downloadPromise;
  const icsPath = path.join(ARTIFACT_DIR, 'event-test.ics');
  await download.saveAs(icsPath);
  const ics = await fs.readFile(icsPath, 'utf8');
  const unfolded = ics.replace(/\r\n[ \t]/g, '');
  for (const required of ['BEGIN:VCALENDAR', 'VERSION:2.0', 'BEGIN:VEVENT', 'DTSTART:20260910T170000Z', 'DTEND:20260910T183000Z', 'SUMMARY:Presentación de novela', 'LOCATION:Librería Ejemplo\\, Calle Mayor 1\\, 28013\\, Madrid\\, Madrid\\, ES', 'URL:https://example.test/eventos/presentacion/', 'UID:', 'DTSTAMP:', 'END:VEVENT', 'END:VCALENDAR']) {
    check(unfolded.includes(required), `Eventos E1 ICS: falta ${required}`);
  }
  check(unfolded.includes('punto y coma\\; barra \\\\'), 'Eventos E1 ICS: escapado de ; y \\');
  for (const line of ics.split('\r\n')) check(new TextEncoder().encode(line).length <= 75, `Eventos ICS: línea >75 bytes: ${line.slice(0, 30)}`);

  await screenshot(page, 'event-1440-result.png', 1440, 1000);
  await screenshot(page, 'event-390-result.png', 390, 844);

  // All-day one-day and multi-day through the real UI.
  await page.check('input[name="allDay"]');
  await page.fill('#ev-start-date', '2026-09-10');
  await page.fill('#ev-end-date', '');
  await page.click('button[type="submit"]');
  let allDayJson = (await page.locator('[data-event-jsonld]').inputValue()).replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  equal(JSON.parse(allDayJson).startDate, '2026-09-10', 'Eventos E2: JSON-LD día completo');
  const oneDay = await page.evaluate(async () => {
    const { buildEventOutputs } = await import('/assets/evento-escritor-core.js');
    return buildEventOutputs({ name:'Día completo', url:'https://example.test/e/', description:'', venueName:'Lugar', streetAddress:'Calle 1', addressLocality:'Madrid', postalCode:'', addressRegion:'', addressCountry:'ES', organizerName:'', organizerUrl:'', imageUrl:'', allDay:true, startDate:'2026-09-10', endDate:'', startDateTime:'', endDateTime:'', utcOffset:'', confirmed:true }).ics;
  });
  check(oneDay.includes('DTSTART;VALUE=DATE:20260910') && oneDay.includes('DTEND;VALUE=DATE:20260911'), 'Eventos E2: DTEND all-day exclusivo');

  await page.fill('#ev-end-date', '2026-09-12');
  await page.click('button[type="submit"]');
  const multiHtml = await page.locator('[data-event-html]').inputValue();
  check(multiHtml.includes('2026-09-10 — 2026-09-12'), 'Eventos E3: HTML multiday coherente');
  allDayJson = (await page.locator('[data-event-jsonld]').inputValue()).replace(/^<script[^>]*>\s*/i, '').replace(/\s*<\/script>$/i, '');
  equal(JSON.parse(allDayJson).endDate, '2026-09-12', 'Eventos E3: JSON-LD último día');

  const invalidCount = await page.evaluate(async () => {
    const { validateEventModel } = await import('/assets/evento-escritor-core.js');
    const base = { name:'Evento', url:'https://example.test/e/', description:'', venueName:'Lugar', streetAddress:'Calle 1', addressLocality:'Madrid', postalCode:'', addressRegion:'', addressCountry:'ES', organizerName:'Org', organizerUrl:'https://example.test/', imageUrl:'https://example.test/x.jpg', allDay:false, startDateTime:'2026-09-10T19:00', endDateTime:'2026-09-10T20:00', utcOffset:'+02:00', confirmed:true };
    const patches = [
      {name:''},{url:''},{url:'http://example.test/'},{startDateTime:''},{endDateTime:'2026-09-10T18:00'},
      {utcOffset:'x'},{utcOffset:'+14:30'},{venueName:''},{streetAddress:''},{addressLocality:''},{addressCountry:''},
      {confirmed:false},{imageUrl:'javascript:alert(1)'},{organizerUrl:'http://example.test/'},{startDateTime:'2026-02-31T19:00'}
    ];
    return patches.filter((patch) => validateEventModel({...base,...patch}).length > 0).length;
  });
  equal(invalidCount, 15, 'Eventos E4: combinaciones inválidas rechazadas');

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
  await assertSkipLink(page, 'Lectura');

  await page.fill('[data-readaloud-manual-words]', '930');
  await page.fill('[data-readaloud-wpm]', '155');
  await page.fill('[data-readaloud-buffer]', '10');
  await page.fill('[data-readaloud-target]', '5');
  await page.click('[data-readaloud-form] button[type="submit"]');
  equal(await page.locator('[data-readaloud-word-count]').textContent(), '930', 'Lectura R2: palabras manuales');
  equal(await page.locator('[data-readaloud-duration]').textContent(), '6 min 36 s', 'Lectura: duración 930/155/+10%');
  check((await page.locator('[data-readaloud-capacity]').textContent()).startsWith('704 '), 'Lectura: capacidad 704');
  equal(await page.locator('[data-readaloud-effective]').textContent(), '141 ppm efectivas', 'Lectura: ritmo efectivo');

  await page.click('[data-wpm-reference="183"]');
  equal(await page.locator('[data-readaloud-wpm]').inputValue(), '183', 'Lectura: botón de referencia actualiza WPM');
  check((await page.locator('[data-readaloud-status]').textContent()).includes('Referencia de investigación'), 'Lectura: explica la referencia');

  await page.fill('[data-readaloud-text]', `${SENTINEL} —rayas «comillas» ¿signos?\ntexto español`);
  await page.fill('[data-readaloud-manual-words]', '9999');
  await page.click('[data-readaloud-form] button[type="submit"]');
  const wordText = await page.locator('[data-readaloud-word-count]').textContent();
  check(wordText !== '9.999', 'Lectura R3: el texto prevalece sobre manual');
  const resultText = await page.locator('[data-readaloud-results]').innerText();
  check(!/NaN|Infinity|undefined|null/.test(resultText), 'Lectura: UI sin NaN/Infinity/undefined/null');

  await screenshot(page, 'read-390-result.png', 390, 844);
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
  await assertSkipLink(page, 'Club');

  await page.fill('#club-title', `${SENTINEL} · El reloj y la memoria`);
  await page.fill('#club-author', 'Elena Ñúñez');
  await page.selectOption('#club-kind', 'fiction');
  await page.selectOption('#club-genre', 'fantasy');
  await page.selectOption('#club-duration', '60');
  await page.selectOption('#club-tone', 'balanced');
  await page.selectOption('#club-scope', 'partial');
  await page.fill('#club-tokens', 'memoria, familia, Elena, reloj, ignorado');
  await page.click('[data-club-session-form] button[type="submit"]');
  const first = await page.locator('[data-club-session-output]').innerText();
  check(first.includes('60 min') && first.includes('lectura parcial'), 'Club: resultado 60 min parcial');
  check(!/\b(final|terminar|terminaste|acabó|cierre)\b|después de terminar|llegar al final|principio y el final/i.test(first.split('Cierre ·')[0]), 'Club: parcial no pregunta por desenlace antes del bloque Cierre');

  await page.click('[data-club-session-alt]');
  const second = await page.locator('[data-club-session-output]').innerText();
  check(first !== second, 'Club: Otra combinación cambia el resultado');
  equal(await page.locator('#club-title').inputValue(), `${SENTINEL} · El reloj y la memoria`, 'Club: Otra combinación conserva título');
  equal(await page.locator('#club-tokens').inputValue(), 'memoria, familia, Elena, reloj, ignorado', 'Club: Otra combinación conserva tokens');
  await page.click('[data-club-session-copy]');
  check((await page.locator('[data-club-session-status]').textContent()).includes('copiada'), 'Club: copiar confirma resultado');

  const engineMatrix = await page.evaluate(async () => {
    const { buildSession } = await import('/assets/club-session-engine.js');
    const genres = ['general','fantasy','scifi','mystery','romance','historical','contemporary','horror','memoir'];
    const durations = [30,60,90].map((duration) => {
      const result = buildSession({kind:'fiction',genre:'general',tone:'balanced',duration,scope:'complete'}, 0);
      return [duration, result.timing.opening + result.timing.core + result.timing.close, result.questions.length];
    });
    const validGenres = genres.every((genre) => {
      const result = buildSession({kind:'fiction',genre,tone:'balanced',duration:60,scope:'complete'}, 0);
      return result.questions.length > 0 && !JSON.stringify(result).includes('undefined');
    });
    const fiction = buildSession({kind:'fiction',genre:'general',tone:'balanced',duration:60,scope:'complete'},0);
    const nonfiction = buildSession({kind:'nonfiction',genre:'general',tone:'balanced',duration:60,scope:'complete'},0);
    const tones = ['social','balanced','deep'].map((tone) => buildSession({kind:'fiction',genre:'general',tone,duration:60,scope:'complete'},0).questions.join('\n'));
    return { durations, validGenres, kindsDiffer: fiction.questions.join('\n') !== nonfiction.questions.join('\n'), tonesDiffer: new Set(tones).size === 3 };
  });
  check(engineMatrix.validGenres, 'Club: todos los enfoques generan estructura válida');
  check(engineMatrix.kindsDiffer, 'Club: ficción y no ficción difieren');
  check(engineMatrix.tonesDiffer, 'Club: tonos producen selección distinta');
  for (const [duration, total] of engineMatrix.durations) equal(total, duration, `Club: agenda suma ${duration} min`);

  await page.selectOption('#club-duration', '60');
  await page.click('[data-club-session-form] button[type="submit"]');
  await screenshot(page, 'club-1440-result.png', 1440, 1000);
  await screenshot(page, 'club-390-result.png', 390, 844);
  await page.emulateMedia({ media: 'print' });
  equal(await page.locator('.site-header').evaluate((el) => getComputedStyle(el).display), 'none', 'Club print: oculta header');
  await page.pdf({ path: path.join(ARTIFACT_DIR, 'club-print.pdf'), format: 'A4', printBackground: true });
  await page.emulateMedia({ media: 'screen' });

  await assertLabels(page, 'Club');
  await assertResponsive(page, 'Club');
  await assertRuntimeClean('Club');
  await context.close();
}

async function testInterview() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Entrevista');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${BASE}/herramientas/entrevista-familiar/`, { waitUntil: 'networkidle' });
  await assertSkipLink(page, 'Entrevista');

  await page.fill('#family-name', `${SENTINEL} · María Ñúñez`);
  await page.fill('#family-relation', 'amigo de la familia');
  await page.selectOption('#family-duration', '30');
  await page.check('input[name="theme"][value="dificil"]');
  await page.check('input[name="objectMode"]');
  await page.click('[data-family-interview-form] button[type="submit"]');
  check(!(await page.locator('[data-family-sensitive-note]').isHidden()), 'Entrevista: aviso sensible visible');
  const interviewText = await page.locator('[data-family-interview-results]').innerText();
  check(interviewText.includes(SENTINEL), 'Entrevista: meta conserva nombre');
  check(/foto|objeto/i.test(interviewText), 'Entrevista: object mode enriquece el guion');
  check(interviewText.includes('prefiero no hablar de eso') && interviewText.includes('cambia de asunto'), 'Entrevista: aviso respeta no responder/cambiar tema');

  await page.uncheck('input[name="theme"][value="dificil"]');
  await page.click('[data-family-interview-form] button[type="submit"]');
  check(await page.locator('[data-family-sensitive-note]').isHidden(), 'Entrevista: aviso sensible se oculta sin tema difícil');

  const durationCounts = await page.evaluate(async () => {
    const { buildInterviewPlan } = await import('/assets/entrevista-familiar-core.js');
    return [15,30,45,60].map((duration) => [duration, buildInterviewPlan({duration,themes:['infancia','familia'],objectMode:false}).questions.length]);
  });
  for (const [duration, count] of durationCounts) check(count > 0, `Entrevista ${duration}: preguntas generadas`);

  for (const link of await page.locator('.tool-caveat a[target="_blank"]').all()) {
    const rel = await link.getAttribute('rel');
    check(rel?.includes('noopener') && rel?.includes('noreferrer'), 'Entrevista: enlace externo target=_blank con rel seguro');
  }

  await screenshot(page, 'interview-1440-result.png', 1440, 1000);
  await screenshot(page, 'interview-390-result.png', 390, 844);
  await assertLabels(page, 'Entrevista');
  await assertResponsive(page, 'Entrevista');
  await assertRuntimeClean('Entrevista');
  await context.close();
}

async function fillRow(page, kind, index, values) {
  const row = page.locator(`[data-rows="${kind}"] [data-row]`).nth(index);
  for (const [key, value] of Object.entries(values)) {
    await row.locator(`[data-key="${key}"]`).fill(String(value));
  }
}

async function exportObject(page, filename) {
  const downloadPromise = page.waitForEvent('download');
  await page.click('[data-record-export]');
  const download = await downloadPromise;
  const file = path.join(ARTIFACT_DIR, filename);
  await download.saveAs(file);
  return { file, text: await fs.readFile(file, 'utf8') };
}

function semanticRecord(value) {
  const copy = structuredClone(value);
  delete copy.exported_at;
  return copy;
}

async function testObject() {
  const context = await makeContext();
  const page = await context.newPage();
  await instrument(page, 'Objeto');
  await page.goto(`${BASE}/recursos/ficha-historia-objeto-heredado/`, { waitUntil: 'networkidle' });
  await assertSkipLink(page, 'Objeto');
  await assertLabels(page, 'Objeto');

  const staticFields = {
    title: `${SENTINEL} · Reloj «A Coruña» — ñ`, type:'Reloj mecánico', materials:'Madera, latón y vidrio', techniques:'Torneado y grabado', dimensions:'62 × 28 × 14 cm', maker:'Taller García', date_period:'ca. 1938–1942', current_location:'Madrid', marks:'N.º 1842\nÁÉÍÓÚ · ü', distinguishing_features:'Reparación visible en 1978', condition_notes:'Arañazo lateral'
  };
  for (const [key, value] of Object.entries(staticFields)) await page.locator(`[data-object-field="${key}"]`).fill(value);
  await page.locator('[data-conservation-field="observed_on"]').fill('2026-08-21');
  await page.locator('[data-conservation-field="risks"]').fill('Humedad y sol directo');
  await page.locator('[data-conservation-field="changes_observed"]').fill('Madera algo más oscura');
  await page.locator('[data-conservation-field="next_steps"]').fill('Consultar a un conservador');
  await page.locator('[data-open-questions]').fill('¿Quién cambió la esfera?\n¿Existe una foto de 1960?\n¿Qué significa GN-42?');

  // Initial row + additions to the controlled minimums.
  for (let i = 1; i < 2; i++) await page.click('[data-add-row="photos"]');
  for (let i = 1; i < 3; i++) await page.click('[data-add-row="owners"]');
  for (let i = 1; i < 3; i++) await page.click('[data-add-row="evidence"]');
  for (let i = 1; i < 2; i++) await page.click('[data-add-row="oral_history"]');
  for (let i = 1; i < 4; i++) await page.click('[data-add-row="timeline"]');

  await fillRow(page,'photos',0,{filename:'frente-ñ.jpg',view:'Frente',note:'Esfera'});
  await fillRow(page,'photos',1,{filename:'reverso.jpg',view:'Reverso',note:'Marca — detalle'});
  await fillRow(page,'owners',0,{person:'María Núñez',from:'ca. 1942',to:'1968',location:'A Coruña',transfer:'Compra',source_ids:'F01'});
  await fillRow(page,'owners',1,{person:'José Díaz',from:'1968',to:'2003',location:'Pontevedra',transfer:'Herencia',source_ids:'F02, F03'});
  await fillRow(page,'owners',2,{person:'Elena Porto',from:'2003',to:'actualidad',location:'Madrid',transfer:'Regalo',source_ids:'F03'});
  await fillRow(page,'evidence',0,{id:'F01',type:'Factura',description:'Compra por 125 pesetas',location:'Caja 2',checked_on:'2026-08-18'});
  await fillRow(page,'evidence',1,{id:'F02',type:'Entrevista',description:'Recuerdo de la mudanza',location:'Audio local',checked_on:'2026-08-19'});
  await fillRow(page,'evidence',2,{id:'F03',type:'Fotografía',description:'Reloj en el salón',location:'Álbum 4',checked_on:'2026-08-20'});
  await fillRow(page,'oral_history',0,{speaker:'Ana Núñez',interview_date:'2026-08-18',summary:`${SENTINEL}: «Sonaba cada media hora»`,source_ids:'F02'});
  await fillRow(page,'oral_history',1,{speaker:'Elena Porto',interview_date:'2026-08-19',summary:'No sabe quién cambió la esfera',source_ids:'F03'});
  for (let i=0;i<4;i++) await fillRow(page,'timeline',i,{from:['ca. 1942','1968','1978','2003'][i],to:i===3?'actualidad':'',event:['Compra','Herencia','Reparación probable','Traslado a Madrid'][i],source_ids:i===0?'F01':'F02, F03'});

  await screenshot(page, 'object-1440-populated.png', 1440, 1000);
  await screenshot(page, 'object-390-populated.png', 390, 844);

  const first = await exportObject(page, 'object-roundtrip.json');
  const parsedFirst = JSON.parse(first.text);
  equal(parsedFirst.photos.length, 2, 'Objeto: 2 fotografías exportadas');
  equal(parsedFirst.owners.length, 3, 'Objeto: 3 propietarios exportados');
  equal(parsedFirst.evidence.length, 3, 'Objeto: 3 evidencias exportadas');
  equal(parsedFirst.oral_history.length, 2, 'Objeto: 2 recuerdos exportados');
  equal(parsedFirst.timeline.length, 4, 'Objeto: 4 hechos exportados');
  equal(parsedFirst.open_questions.length, 3, 'Objeto: 3 preguntas exportadas');

  page.once('dialog', async (dialog) => dialog.dismiss());
  await page.click('[data-record-clear]');
  equal(await page.locator('[data-object-field="title"]').inputValue(), staticFields.title, 'Objeto: cancelar Vaciar conserva datos');
  page.once('dialog', async (dialog) => dialog.accept());
  await page.click('[data-record-clear]');
  equal(await page.locator('[data-object-field="title"]').inputValue(), '', 'Objeto: confirmar Vaciar elimina la ficha de la página');

  await page.locator('[data-record-import]').setInputFiles({ name:'roundtrip.json', mimeType:'application/json', buffer:Buffer.from(first.text) });
  equal(await page.locator('[data-object-field="title"]').inputValue(), staticFields.title, 'Objeto: import restaura título Unicode');
  const second = await exportObject(page, 'object-roundtrip-reexport.json');
  assert.deepEqual(semanticRecord(JSON.parse(second.text)), semanticRecord(parsedFirst));

  const beforeInvalid = await page.locator('[data-object-field="title"]').inputValue();
  await page.locator('[data-record-import]').setInputFiles({ name:'malformed.json', mimeType:'application/json', buffer:Buffer.from('{ "foo":') });
  equal(await page.locator('[data-object-field="title"]').inputValue(), beforeInvalid, 'Objeto: JSON malformado no destruye ficha');
  check((await page.locator('[data-record-status]').textContent()).includes('No se pudo abrir'), 'Objeto: JSON malformado produce error comprensible');

  await page.click('[data-add-row="photos"]');
  equal(await page.evaluate(() => document.activeElement?.getAttribute('data-key')), 'filename', 'Objeto: añadir fila mueve foco al primer campo');
  await page.locator('[data-rows="photos"] [data-row]').last().locator('[data-remove]').click();
  check(await page.locator('[data-add-row="photos"]').evaluate((el) => document.activeElement === el), 'Objeto: eliminar fila devuelve foco a Añadir fotografía');

  await page.emulateMedia({ media:'print' });
  equal(await page.locator('.site-header').evaluate((el) => getComputedStyle(el).display), 'none', 'Objeto print: oculta header');
  await page.pdf({ path:path.join(ARTIFACT_DIR,'object-print.pdf'), format:'A4', printBackground:true });
  await page.emulateMedia({ media:'screen' });

  await assertResponsive(page, 'Objeto');
  await assertRuntimeClean('Objeto');
  await context.close();
}

async function testNoJs() {
  const context = await makeContext({ javaScriptEnabled: false });
  const cases = [
    ['/herramientas/eventos-ics/', 'Privacidad:', 'No uses esta herramienta'],
    ['/herramientas/tiempo-lectura-voz-alta/', 'Privacidad', 'Una estimación, no un cronómetro'],
    ['/clubes-de-lectura/preparar-sesion/', 'No se guarda ni se envía', 'Cómo usar las preguntas'],
    ['/herramientas/entrevista-familiar/', 'No se guarda ningún nombre', 'Cómo está diseñada'],
    ['/recursos/ficha-historia-objeto-heredado/', 'Privacidad:', 'no sustituye asesoramiento profesional'],
  ];
  for (const [route, privacyText, limitationText] of cases) {
    const page = await context.newPage();
    await page.goto(`${BASE}${route}`, { waitUntil:'domcontentloaded' });
    for (const selector of ['.site-header','.primary-nav','h1','.site-footer']) check(await page.locator(selector).count() > 0, `No-JS ${route}: falta ${selector}`);
    const body = await page.locator('body').innerText();
    check(body.includes(privacyText), `No-JS ${route}: falta privacidad visible`);
    check(body.includes(limitationText), `No-JS ${route}: falta limitación/metodología visible`);
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

  // Text-spacing / 200% text resize is run on fresh pages so injected QA CSS
  // cannot alter screenshots or the functional cases above.
  for (const [key, route] of [
    ['Eventos','/herramientas/eventos-ics/'],
    ['Lectura','/herramientas/tiempo-lectura-voz-alta/'],
    ['Club','/clubes-de-lectura/preparar-sesion/'],
    ['Entrevista','/herramientas/entrevista-familiar/'],
    ['Objeto','/recursos/ficha-historia-objeto-heredado/'],
  ]) {
    const context = await makeContext();
    const page = await context.newPage();
    await page.goto(`${BASE}${route}`, { waitUntil:'networkidle' });
    await assertTextResilience(page, key);
    await context.close();
  }

  console.log('INPUT EXFILTRATION: 0/5');
  console.log(`QA artifacts: ${ARTIFACT_DIR}`);
} finally {
  await browser.close();
}

if (failures.length) {
  console.error(`\n${failures.length} fallo(s) de QA:`);
  failures.forEach((failure, index) => console.error(`${index + 1}. ${failure}`));
  process.exit(1);
}

console.log('qa/tools-events-memory-browser: OK');