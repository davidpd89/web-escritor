import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext();
  await context.route('**/assets/radar-convocatorias.js*',route => route.abort('failed'));
  const page = await context.newPage();
  const response = await page.goto(origin + '/convocatorias-escritores/',{waitUntil:'load'});
  assert.ok(response?.ok());
  assert.ok(await page.locator('[data-radar-item]').count() > 0,'El contenido desaparece sin script');
  const state = await page.evaluate(() => {
    const search = document.querySelector('[data-radar-search]');
    const finder = document.querySelector('.tool-finder');
    const disabled = Boolean(search?.disabled || search?.readOnly || finder?.getAttribute('aria-disabled') === 'true');
    const notice = [...document.querySelectorAll('main [role="alert"],main [role="status"]')].some(el => {
      const s = getComputedStyle(el);
      return s.display !== 'none' && s.visibility !== 'hidden' && /javascript|filtros|búsqueda/i.test(el.textContent || '');
    });
    return {disabled,notice};
  });
  assert.ok(state.disabled || state.notice,'El usuario encuentra filtros inertes sin explicación');
  await context.close();
  console.log('OK: degradación ante fallo del controlador');
} finally {await browser.close();}
