import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/', '/cuaderno/que-es-el-portal-fantasy/', '/fragmento/', '/universo/noveris/', '/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/fragmentos/', '/las-manecillas-del-recuerdo/kindle/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768]) {
    for (const route of routes) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      await context.route('**/*', r => new URL(r.request().url()).origin === BASE ? r.continue() : r.abort());
      const page = await context.newPage();
      const response = await page.goto(BASE + route, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${route}: error HTTP`);
      await page.addStyleTag({ content: 'html{font-size:200%!important}' });
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const selectors = 'main h1,main h2,main h3,main a.primary-action,main a.text-action,main button.form-submit,main .fragment-index__title';
        return [...document.querySelectorAll(selectors)].filter(el => {
          const s = getComputedStyle(el);
          if (s.display === 'none' || s.visibility === 'hidden') return false;
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && (el.scrollWidth > el.clientWidth + 3) && ['hidden', 'clip'].includes(s.overflowX);
        }).map(el => ({ text: el.textContent.trim().slice(0, 60), width: el.clientWidth, scroll: el.scrollWidth }));
      });
      assert.deepEqual(result, [], `${route} ${width}px: texto recortado`);
      await context.close();
    }
  }
} finally { await browser.close(); }
console.log('OK: ampliación tipográfica transversal de 7 rutas en 3 anchuras');
