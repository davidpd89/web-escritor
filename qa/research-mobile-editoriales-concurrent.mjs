import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
const widths = [320, 360, 390];
try {
  const results = await Promise.all(Array.from({length:12}, async (_, i) => {
    const width = widths[i % widths.length];
    const context = await browser.newContext({viewport:{width,height:740},reducedMotion:'reduce',serviceWorkers:'block'});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/*', route => {
      const url = new URL(route.request().url());
      return url.origin === new URL(BASE).origin ? route.continue() : route.abort();
    });
    try {
      const response = await page.goto(BASE + '/editoriales/', {waitUntil:'load',timeout:30000});
      assert.equal(response?.status(),200,`/editoriales/ ${width}px petición ${i}: HTTP ${response?.status()}`);
      const state = await page.evaluate(() => {
        const main = document.querySelector('main');
        const box = main?.getBoundingClientRect();
        return {text:main?.innerText.trim().length || 0,visible:!!box && box.width>0 && box.height>0,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
      });
      assert.ok(state.text>100,`/editoriales/ ${width}px petición ${i}: contenido vacío (${state.text} caracteres)`);
      assert.ok(state.visible,`/editoriales/ ${width}px petición ${i}: main invisible`);
      assert.ok(state.overflow<=1,`/editoriales/ ${width}px petición ${i}: desbordamiento ${state.overflow}px`);
      assert.deepEqual(errors,[],`/editoriales/ ${width}px petición ${i}: errores ${errors.join('; ')}`);
      return {width,status:response.status()};
    } finally { await context.close(); }
  }));
  assert.equal(results.length,12);
  console.log('PASS editoriales mobile concurrent',results);
} finally { await browser.close(); }
