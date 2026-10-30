// Campos editables visibles: tamaño efectivo >= 16px en móvil/tablet (320/390/768)
// y sin desbordamiento horizontal. Censa todos los controles editables visibles
// de cada ruta, no solo los enumerados; excluye honeypots, inert, ocultos,
// checkbox/radio/file/range/color y botones. El autozoom de Safari iOS no se
// reproduce en Chromium: esto prueba la política, no el dispositivo.
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROUTES = [
  { path: '/cuaderno/que-es-el-portal-fantasy/', popup: true, expect: ['#nl-email-cuaderno', '#nl-popup-email'] },
  { path: '/herramientas/distribucion-pov/', expect: ['#pov-format-mode', '#pov-input'] },
  { path: '/herramientas/personajes/', expect: ['#map-title', '#character-name', '#relation-label', '#relation-from', '#relation-to', '#relation-type', '#relation-evolution', '#map-focus'] },
  { path: '/herramientas/json-ld-escritores/', expect: ['#f-name', '#f-description'] },
  { path: '/recursos/ficha-historia-objeto-heredado/', expect: ['#object-title'] },
  { path: '/recomendaciones/', expect: [] },
];
const WIDTHS = [320, 390, 768];
const census = () => {
  const skipTypes = new Set(['hidden', 'checkbox', 'radio', 'file', 'range', 'color', 'submit', 'button', 'reset', 'image']);
  return [...document.querySelectorAll('input, select, textarea')].filter(el => {
    if (el.tagName === 'INPUT' && skipTypes.has((el.type || 'text').toLowerCase())) return false;
    if (el.closest('[inert], [hidden], [aria-hidden="true"]')) return false;
    if (el.tabIndex < 0 || el.autocomplete === 'off' && /honeypot|website|hp/i.test(el.name || el.id)) return false;
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (s.visibility === 'hidden' || s.display === 'none' || r.width < 2 || r.height < 2) return false;
    return true;
  }).map(el => ({
    id: el.id ? `#${el.id}` : `${el.tagName.toLowerCase()}[name=${el.name}]`,
    font: parseFloat(getComputedStyle(el).fontSize),
  }));
};

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const failures = [];
const report = [];
try {
  for (const width of WIDTHS) {
    for (const route of ROUTES) {
      const context = await browser.newContext({ viewport: { width, height: 844 }, reducedMotion: 'reduce', serviceWorkers: 'block', isMobile: width < 768, hasTouch: true });
      const page = await context.newPage();
      await page.addInitScript(() => { try { localStorage.removeItem('nl-popup-ts'); localStorage.removeItem('nl-subscribed'); } catch {} });
      const response = await page.goto(ORIGIN + route.path, { waitUntil: 'load' });
      assert.ok(response?.ok(), `${route.path}: página no disponible`);
      let fields = await page.evaluate(census);
      if (route.popup) {
        await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await page.locator('#nl-popup-email').waitFor({ state: 'visible' });
        fields = fields.concat(await page.evaluate(census));
      }
      const seen = new Map(fields.map(f => [f.id, f.font]));
      for (const id of route.expect) {
        if (!seen.has(id)) failures.push(`${width}px ${route.path}: ${id} no visible/censado`);
      }
      for (const [id, font] of seen) {
        report.push(`${width}px ${route.path} ${id} ${font}px`);
        if (font < 16) failures.push(`${width}px ${route.path}: ${id} ${font}px < 16px`);
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (overflow > 1) failures.push(`${width}px ${route.path}: desbordamiento horizontal ${overflow}px`);
      await context.close();
    }
  }
} finally { await browser.close(); }
if (process.env.QA_VERBOSE) console.log(report.join('\n'));
assert.deepEqual(failures, [], failures.join('\n'));
console.log(`mobile-form-typography-browser: PASS (${report.length} medidas)`);
