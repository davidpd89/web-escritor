import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    try {
      const page = await context.newPage();
      const response = await page.goto(new URL('/recomendaciones/', BASE).href, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `/recomendaciones/ @ ${width}: HTTP incorrecto`);
      await page.locator('[data-catalogue-filters]').waitFor({ state: 'visible' });
      const groups = page.locator('details[data-facet-group]');
      assert.ok(await groups.count() > 0, `/recomendaciones/ @ ${width}: no se encontraron filtros`);
      for (let i = 0; i < await groups.count(); i++) {
        const group = groups.nth(i);
        const summary = group.locator('summary').first();
        if (!await summary.isVisible()) continue;
        await summary.scrollIntoViewIfNeeded();
        await summary.focus();
        assert.ok(await summary.evaluate(el => document.activeElement === el), `Filtro ${i} @ ${width}: summary no enfocable`);
        const before = await group.evaluate(el => el.open);
        await page.keyboard.press('Enter');
        await page.waitForFunction(({ i, before }) => document.querySelectorAll('details[data-facet-group]')[i]?.open !== before, { i, before });
        const state = await summary.evaluate(el => {
          const r = el.getBoundingClientRect();
          return { focused: document.activeElement === el, left: r.left, right: r.right, top: r.top, bottom: r.bottom, text: el.textContent.trim() };
        });
        assert.ok(state.text.length > 0, `Filtro ${i} @ ${width}: nombre vacío`);
        assert.ok(state.focused, `Filtro ${i} @ ${width}: perdió el foco al abrirse`);
        assert.ok(state.left >= -1 && state.right <= width + 1 && state.top >= -1 && state.bottom <= 901, `Filtro ${i} @ ${width}: geometría incorrecta ${JSON.stringify(state)}`);
        await page.keyboard.press('Enter');
        await page.waitForFunction(({ i, before }) => document.querySelectorAll('details[data-facet-group]')[i]?.open === before, { i, before });
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
