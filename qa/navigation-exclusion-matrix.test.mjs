import assert from 'node:assert/strict';
import {chromium, firefox, webkit} from 'playwright';
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/privacidad.html', '/aviso-legal.html', '/cuaderno/', '/libros/', '/'];
for (const [name, engine] of Object.entries({chromium, firefox, webkit})) {
  const browser = await engine.launch();
  try {
    for (const route of routes) {
      const page = await browser.newPage({viewport: {width: 375, height: 812}});
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
      try {
        await page.goto(origin + route, {waitUntil: 'domcontentloaded'});
        const state = await page.evaluate(() => ({v1: document.documentElement.classList.contains('v1'), count: document.querySelectorAll('.mobile-bottom-nav').length}));
        const excluded = state.v1 || ['/privacidad.html', '/aviso-legal.html'].includes(route);
        if (excluded) assert.equal(state.count, 0, `${name} ${route}: navegación promocional indebida`);
        else assert.equal(state.count, 1, `${name} ${route}: navegación móvil ausente`);
      } finally {await page.close();}
    }
  } finally {await browser.close();}
}
console.log('PASS navigation exclusion matrix');