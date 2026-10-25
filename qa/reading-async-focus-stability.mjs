import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.QA_BASE_URL || process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext({reducedMotion:'reduce'});
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const response = await page.goto(base + '/recomendaciones/', {waitUntil:'domcontentloaded'});
  assert.equal(response.status(), 200, '/recomendaciones/: HTTP');
  const search = page.locator('[data-filter="q"]');
  await page.waitForFunction(() => document.querySelector('[data-catalogue-filters] fieldset')?.disabled === false);
  await search.focus();
  await page.keyboard.type('Coraline');
  await page.waitForFunction(() => document.querySelector('[data-filter="q"]')?.value === 'Coraline');
  await page.waitForLoadState('load');
  assert(await search.evaluate(el => el === document.activeElement), '/recomendaciones/: foco perdido durante la carga');
  assert.equal(await search.inputValue(), 'Coraline', '/recomendaciones/: búsqueda modificada');
  const name = await search.evaluate(el => {
    const label = el.closest('label');
    return el.getAttribute('aria-label') || (el.labels && [...el.labels].map(x => x.textContent.trim()).join(' ')) || label?.textContent.trim() || '';
  });
  assert(name.trim(), '/recomendaciones/: buscador sin nombre accesible');
  await context.close();
} finally { await browser.close(); }