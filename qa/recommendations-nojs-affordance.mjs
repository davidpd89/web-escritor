import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  await context.route('**/*', route => new URL(route.request().url()).origin === new URL(BASE).origin ? route.continue() : route.abort());
  const page = await context.newPage();
  const response = await page.goto(BASE + '/recomendaciones/', { waitUntil: 'load' });
  assert.equal(response.status(), 200);
  const state = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('[data-catalogue-book]')];
    const visible = e => {
      if (e.hidden || e.closest('[hidden]')) return false;
      const style = getComputedStyle(e);
      return style.display !== 'none' && style.visibility !== 'hidden';
    };
    return {
      total: cards.length,
      visible: cards.filter(visible).length,
      links: cards.filter(card => [...card.querySelectorAll('a[href]')].some(a => visible(a) && a.getAttribute('href'))).length,
      deadControls: [...document.querySelectorAll('[data-reading-catalogue] button')].filter(visible).filter(button => !button.disabled && !button.closest('form[action]')).map(button => button.outerHTML.slice(0, 200)),
      filtersVisible: [...document.querySelectorAll('[data-catalogue-filters] input, [data-catalogue-filters] select')].filter(visible).map(e => e.outerHTML.slice(0, 150))
    };
  });
  assert.ok(state.total > 0, 'No hay libros publicados en el HTML');
  assert.equal(state.visible, state.total, 'Sin JS deben conservarse todos los libros');
  assert.equal(state.links, state.total, 'Cada libro debe tener un enlace navegable');
  assert.deepEqual(state.deadControls, [], 'Botones dinámicos sin funcionamiento');
  assert.deepEqual(state.filtersVisible, [], 'Filtros dinámicos visibles sin funcionamiento');
  await context.close();
} finally {
  await browser.close();
}
console.log('OK: degradación sin JavaScript');