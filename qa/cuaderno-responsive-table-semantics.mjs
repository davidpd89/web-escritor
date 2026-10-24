import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    const page = await context.newPage();
    try {
      await page.goto(BASE + '/cuaderno/portal-fantasy-vs-fantasia-epica/');
      const tables = page.locator('.article-prose table');
      assert.ok(await tables.count() > 0, 'La comparativa perdió su tabla');
      for (const table of await tables.all()) {
        const errors = await table.evaluate(el => {
          const head = el.querySelector('thead tr');
          const headerCount = head?.querySelectorAll('th').length || 0;
          const problems = [];
          for (const [i, row] of [...el.querySelectorAll('tbody tr')].entries()) {
            const cells = [...row.children].filter(c => c.matches('td, th'));
            if (cells.length !== headerCount) problems.push(`fila ${i}: ${cells.length}/${headerCount} columnas`);
            const first = cells[0];
            if (!first || !(first.matches('th[scope=row]') || first.hasAttribute('headers') || first.hasAttribute('aria-label'))) problems.push(`fila ${i}: etiqueta de fila sin asociación`);
          }
          return problems;
        });
        assert.deepEqual(errors, [], `Tabla ${width}px: ${errors.join('; ')}`);
        const wrap = table.locator('xpath=..');
        const dims = await wrap.evaluate(el => ({ available: el.clientWidth, content: el.scrollWidth }));
        if (dims.content > dims.available + 1) {
          const scroll = await wrap.evaluate(el => { el.scrollLeft = el.scrollWidth; return el.scrollLeft; });
          assert.ok(scroll > 0, `${width}px: la última columna queda inaccesible`);
        }
      }
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno responsive table semantics');
} finally { await browser.close(); }
