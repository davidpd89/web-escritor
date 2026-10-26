import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/libros/', '/las-manecillas-del-recuerdo/', '/recomendaciones/'];
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
let checked = 0;
try {
  for (const width of [360, 390, 768, 1280]) {
    const page = await browser.newPage({viewport:{width,height:900}, reducedMotion:'reduce'});
    for (const route of ROUTES) {
      const response = await page.goto(BASE + route, {waitUntil:'domcontentloaded'});
      assert.equal(response?.status(), 200, `${route} ${width}px: página no disponible`);
      await page.evaluate(() => document.fonts.ready);
      const links = await page.locator('a[href*="#"]').evaluateAll(nodes => nodes.map(a => ({href:a.getAttribute('href'), text:a.textContent?.trim() || a.getAttribute('aria-label') || ''})).filter(x => x.href));
      for (const link of links) {
        const target = new URL(link.href, page.url());
        if (target.origin !== new URL(BASE).origin || !target.hash) continue;
        const fragment = decodeURIComponent(target.hash.slice(1));
        if (!fragment) continue;
        const destination = new URL(target.pathname, BASE);
        if (destination.pathname !== new URL(page.url()).pathname) {
          const result = await page.request.get(destination.href);
          assert.equal(result.status(), 200, `${route} ${width}px: enlace ${link.href} devuelve HTTP ${result.status()}`);
        }
        const probe = await browser.newPage({viewport:{width,height:900}, reducedMotion:'reduce'});
        try {
          const res = await probe.goto(target.href, {waitUntil:'domcontentloaded'});
          assert.equal(res?.status(), 200, `${route} ${width}px: destino ${link.href} no disponible`);
          const state = await probe.evaluate(id => {
            const el = document.getElementById(id) || [...document.getElementsByName(id)].find(x => x instanceof HTMLElement);
            if (!el) return {exists:false};
            el.scrollIntoView({block:'center',behavior:'instant'});
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            return {exists:true,display:cs.display,visibility:cs.visibility,width:r.width,height:r.height,top:r.top,bottom:r.bottom,viewport:innerHeight};
          }, fragment);
          assert.ok(state.exists, `${route} ${width}px: ${link.href} apunta a un fragmento inexistente`);
          assert.notEqual(state.display, 'none', `${route} ${width}px: ${link.href} tiene display:none`);
          assert.notEqual(state.visibility, 'hidden', `${route} ${width}px: ${link.href} está oculto`);
          assert.ok(state.top < state.viewport && state.bottom >= 0, `${route} ${width}px: ${link.href} no puede situarse dentro del viewport: ${JSON.stringify(state)}`);
          checked++;
        } finally { await probe.close(); }
      }
    }
    await page.close();
  }
  assert.ok(checked > 0, 'No se han comprobado enlaces con fragmento');
  console.log(`generated-editorial-fragment-visual: OK (${checked} comprobaciones)`);
} finally { await browser.close(); }
