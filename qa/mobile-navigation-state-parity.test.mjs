import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const origin = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = ['/', '/libros/', '/cuaderno/', '/las-manecillas-del-recuerdo/'];
const expected = ['/', '/las-manecillas-del-recuerdo/', '/libros/', '/cuaderno/', '/prensa.html#contacto'];

for (const [name, engine] of Object.entries({chromium, firefox, webkit})) {
  const browser = await engine.launch();
  try {
    for (const route of routes) {
      const page = await browser.newPage({viewport: {width: 375, height: 812}});
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, r => r.abort());
      try {
        await page.goto(origin + route, {waitUntil: 'domcontentloaded'});
        const result = await page.evaluate(() => {
          const nav = document.querySelector('.mobile-bottom-nav');
          if (!nav) return {v1: document.documentElement.classList.contains('v1')};
          return {links: [...nav.querySelectorAll('a')].map(a => ({href: new URL(a.href).pathname + new URL(a.href).hash, current: a.getAttribute('aria-current')})), count: document.querySelectorAll('.mobile-bottom-nav').length};
        });
        if (result.v1) continue;
        assert.equal(result.count, 1, `${name} ${route}: navegación duplicada`);
        assert.deepEqual(result.links.map(x => x.href), expected, `${name} ${route}: destinos`);
        const active = result.links.filter(x => x.current === 'page');
        assert.equal(active.length, 1, `${name} ${route}: debe haber un único destino activo`);
        assert.equal(active[0].href, route, `${name} ${route}: destino activo incorrecto`);
      } finally { await page.close(); }
    }
  } finally { await browser.close(); }
}
console.log('PASS mobile navigation state parity');