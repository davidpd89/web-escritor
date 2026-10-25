import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [320, 390, 768, 1440]) {
    const page = await browser.newPage({viewport: {width, height: 900}, reducedMotion: 'reduce'});
    await page.goto(`${BASE}/recomendaciones/`, {waitUntil: 'domcontentloaded'});
    await page.locator('[data-catalogue-filters]').waitFor({state: 'visible'});
    const unnamed = await page.locator('a[href],button,input,select,textarea').evaluateAll(elements => elements.filter(el => {
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || el.closest('[hidden],[inert]')) return false;
      if (!el.getClientRects().length || el.getAttribute('type') === 'hidden') return false;
      const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
      const labelled = ids.map(id => document.getElementById(id)?.textContent || '').join(' ');
      const label = el.labels ? [...el.labels].map(x => x.textContent).join(' ') : '';
      const name = [el.getAttribute('aria-label'), labelled, label, el.textContent, el.getAttribute('alt'), el.getAttribute('title'), el.getAttribute('value')].filter(Boolean).join(' ').trim();
      return !name;
    }).map(el => el.outerHTML.slice(0, 250)));
    assert.deepEqual(unnamed, [], `Controles sin nombre accesible en ${width}px`);
    const search = page.getByRole('button', {name: 'Buscar libros', exact: true});
    await search.focus();
    assert(await search.evaluate(el => document.activeElement === el));
    await page.close();
  }
} finally {
  await browser.close();
}