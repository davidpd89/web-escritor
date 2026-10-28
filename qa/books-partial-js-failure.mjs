import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
const failures = [];
try {
  for (const file of ['samuel-quiz.js','samuel-buy-modal.js']) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
    const page = await context.newPage();
    await page.route(`**/assets/${file}*`,r => r.abort());
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`,{waitUntil:'load'});
    assert.equal(await page.locator('main h1').isVisible(),true);
    assert.equal(await page.locator('main a[href="/fragmento/"]').first().isVisible(),true);
    if (file === 'samuel-quiz.js') {
      const quiz = page.locator('#quiz-noveris');
      const hasOptions = await quiz.locator('.quiz-option:visible').count()>0;
      const hasFallback = await quiz.locator('a[href="/fragmento/"]:visible, a[href="/universo/noveris/"]:visible').count()>0;
      if (!hasOptions && !hasFallback) failures.push('quiz: estado vacío sin alternativa local al fallar su script');
    } else {
      const inert = await page.locator('main button[data-buy-modal]:visible').count();
      if (inert) failures.push(`compra: ${inert} botones visibles sin manejador al fallar el modal`);
    }
    await context.close();
  }
} finally { await browser.close(); }
assert.deepEqual(failures,[]);
console.log('PASS partial script failure recovery');
