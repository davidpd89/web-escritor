import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const cases = [
  ['2026-10-22', 'Cierra mañana', false],
  ['2026-10-23', 'Cierra hoy', false],
  ['2026-10-24', 'Plazo finalizado', true]
];
try {
  for (const [today, label, hidden] of cases) {
    const page = await browser.newPage();
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.origin !== new URL(O).origin) return route.abort();
      if (url.pathname !== '/convocatorias-escritores/' && url.pathname !== '/convocatorias-escritores/index.html') return route.continue();
      const response = await route.fetch();
      const html = await response.text();
      const pattern = /<article\b[^>]*data-radar-kind="expired"[^>]*data-title="xxxviii certamen literario alberto magno de ciencia ficción 2026"[^>]*data-deadline="2026-10-23"[^>]*>/g;
      const matches = [...html.matchAll(pattern)];
      assert.equal(matches.length, 1, 'La convocatoria base debe existir exactamente una vez');
      const updated = html.replace(pattern, article => article.replace('data-radar-kind="expired"', 'data-radar-kind="active"'));
      await route.fulfill({ response, body: updated });
    });
    await page.addInitScript(date => { window.__DP_RADAR_TODAY__ = date; }, today);
    await page.goto(O + '/convocatorias-escritores/', { waitUntil: 'domcontentloaded' });
    const card = page.locator('[data-radar-item][data-radar-kind="active"][data-deadline="2026-10-23"][data-title="xxxviii certamen literario alberto magno de ciencia ficción 2026"]');
    assert.ok(await card.count(), 'Falta fixture de convocatoria real');
    assert.equal((await card.locator('[data-radar-status]').textContent()).trim(), label, today);
    assert.equal(await card.evaluate(node => node.hidden), hidden, today);
    const dates = await page.evaluate(() => window.DPRadarDates?.SITE_TIME_ZONE);
    assert.equal(dates, 'Europe/Madrid');
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('PASS: transición de plazo en Madrid');
