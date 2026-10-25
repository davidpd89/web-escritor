import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/editoriales/', '/editoriales/minotauro/', '/editoriales/duermevela-ediciones/'];
const browser = await chromium.launch({ headless: true });
try {
  for (const route of routes) for (const width of [320, 390, 768]) {
    const context = await browser.newContext({ viewport: { width, height: 800 }, bypassCSP: true });
    const page = await context.newPage();
    await page.goto(`${origin}${route}`, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => {
      const title = document.querySelector('[data-editorial-card] h2 a') || document.querySelector('.tool-hero h1');
      if (title) title.textContent = 'EditorialInternacionalDeLiteraturaFantasticaContemporanea'.repeat(3);
      const meta = document.querySelector('[data-editorial-card] .tool-meta') || document.querySelector('.spec-ledger dd');
      if (meta) meta.textContent = 'DepartamentoDeRecepcionDeProyectosOriginales'.repeat(4);
    });
    await page.addStyleTag({ content: 'html{font-size:200%!important} *{letter-spacing:.12em!important;word-spacing:.16em!important}' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 1, `${route} ${width}px: overflow horizontal ${overflow}px`);
    const candidate = page.locator('[data-editorial-card] h2, .tool-hero h1').first();
    const rect = await candidate.boundingBox();
    assert.ok(rect && rect.width > 0, `${route} ${width}px: título perdido`);
    await context.close();
  }
  console.log('PASS editorial long-content reflow');
} finally {
  await browser.close();
}