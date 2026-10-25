import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  for (const width of [390, 1440]) {
    const context = await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
    const page = await context.newPage();
    const response = await page.goto(base + '/editoriales/', {waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200,`/editoriales/ ${width}: HTTP`);
    const ids = ['editoriales-q','editoriales-genero'];
    for (const id of ids) {
      const control = page.locator('#' + id);
      assert.equal(await control.count(),1,`/editoriales/ ${width}: falta ${id}`);
      assert(await control.isVisible(),`/editoriales/ ${width}: ${id} invisible`);
      const label = await control.evaluate(el => el.getAttribute('aria-label') || [...(el.labels || [])].map(x => x.textContent.trim()).join(' '));
      assert(label.trim(),`/editoriales/ ${width}: ${id} sin nombre accesible`);
      await control.focus();
      assert(await control.evaluate(el => document.activeElement === el),`/editoriales/ ${width}: ${id} no recibe foco`);
    }
    const search = page.locator('#editoriales-q');
    await search.focus();
    await search.fill('Planeta');
    await page.waitForLoadState('load');
    assert(await search.evaluate(el => document.activeElement === el),`/editoriales/ ${width}: foco perdido después de cargar`);
    assert.equal(await search.inputValue(),'Planeta',`/editoriales/ ${width}: búsqueda perdida`);
    await context.close();
  }
} finally { await browser.close(); }