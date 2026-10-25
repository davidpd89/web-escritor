import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN;
assert.ok(origin, 'QA_ORIGIN debe apuntar al servidor local de la web');
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const width of [320, 390, 768, 899, 900, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 800 }, reducedMotion: 'reduce' });
    await page.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen', 'true'); } catch {} });
    const response = await page.goto(new URL('/', origin).href, { waitUntil: 'load' });
    assert.equal(response.status(), 200, `Portada ${width}px: HTTP inesperado`);
    await page.evaluate(() => document.fonts.ready);
    await page.waitForFunction(() => [...document.styleSheets].every(s => { try { return s.cssRules.length >= 0; } catch { return true; } }));
    const failures = await page.evaluate(() => {
      const root = document.querySelector('.site-header__inner');
      if (!root) return ['Falta .site-header__inner'];
      return [...root.querySelectorAll('a[href],button')].filter(el => {
        const s = getComputedStyle(el);
        const r = el.getBoundingClientRect();
        return s.display !== 'none' && s.visibility === 'visible' && !el.disabled && r.width > 0 && r.height > 0;
      }).flatMap(el => {
        const r = el.getBoundingClientRect();
        const points = [[.5,.5],[.25,.5],[.75,.5],[.5,.25],[.5,.75]];
        const hit = points.some(([fx,fy]) => {
          const x = r.left + r.width * fx, y = r.top + r.height * fy;
          if (x < 0 || x >= innerWidth || y < 0 || y >= innerHeight) return false;
          const target = document.elementFromPoint(x,y);
          return target === el || el.contains(target);
        });
        return hit ? [] : [`${el.outerHTML.slice(0,160)}: rect=${JSON.stringify({x:r.x,y:r.y,width:r.width,height:r.height})}`];
      });
    });
    assert.deepEqual(failures, [], `Portada ${width}px: controles de cabecera ocluidos o inaccesibles`);
    await page.close();
  }
} finally { await browser.close(); }