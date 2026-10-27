import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const ROUTES = ['/herramientas/eventos-ics/', '/herramientas/tiempo-lectura-voz-alta/', '/clubes-de-lectura/preparar-sesion/', '/herramientas/entrevista-familiar/', '/recursos/ficha-historia-objeto-heredado/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    try {
      const page = await context.newPage();
      for (const route of ROUTES) {
        const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'load' });
        assert.equal(response?.status(), 200, `${route} @ ${width}: HTTP ${response?.status()}`);
        await page.evaluate(() => document.fonts.ready);
        const controls = page.locator('main input:not([type="hidden"]):not([disabled]), main textarea:not([disabled]), main select:not([disabled]), main button:not([disabled])');
        let checked = 0;
        for (let i = 0; i < await controls.count(); i++) {
          const control = controls.nth(i);
          if (!await control.isVisible()) continue;
          if (await control.getAttribute('tabindex') === '-1') continue;
          if (await control.getAttribute('aria-hidden') === 'true') continue;
          await control.focus();
          const state = await control.evaluate(el => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return { focused: document.activeElement === el, left: r.left, right: r.right, top: r.top, bottom: r.bottom, outlineStyle: s.outlineStyle, outlineWidth: parseFloat(s.outlineWidth), boxShadow: s.boxShadow, borderWidth: parseFloat(s.borderTopWidth), borderStyle: s.borderTopStyle };
          });
          assert.ok(state.focused, `${route} @ ${width}: control ${i} no recibe foco`);
          assert.ok(state.right > 0 && state.left < width && state.bottom > 0 && state.top < 900, `${route} @ ${width}: control ${i} fuera del viewport: ${JSON.stringify(state)}`);
          assert.ok((state.outlineStyle !== 'none' && state.outlineWidth > 0) || state.boxShadow !== 'none' || (state.borderStyle !== 'none' && state.borderWidth > 0), `${route} @ ${width}: control ${i} sin indicador de foco computado`);
          checked++;
        }
        assert.ok(checked > 0, `${route} @ ${width}: ningún control de formulario visible comprobado`);
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
