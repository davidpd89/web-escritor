import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = [
  '/cuaderno/que-es-el-portal-fantasy/',
  '/cuaderno/portal-fantasy-vs-fantasia-epica/',
  '/cuaderno/worldbuilding-noveris-ciudad-magica/',
  '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/'
];
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [390, 768, 1440]) for (const route of routes) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage();
    try {
      await page.goto(BASE + route);
      const links = page.locator('[data-article-toc] a[href^="#"]');
      const total = await links.count();
      assert.ok(total >= 4, route);
      for (const i of [...new Set([0, Math.floor(total / 2), total - 1])]) {
        const link = links.nth(i);
        const hash = await link.getAttribute('href');
        await link.focus();
        await page.keyboard.press('Enter');
        await page.waitForFunction(value => location.hash === value, hash);
        await page.waitForTimeout(200);
        const geometry = await page.evaluate(value => {
          const target = document.getElementById(decodeURIComponent(value.slice(1)));
          if (!target) return null;
          const box = target.getBoundingClientRect();
          const header = document.querySelector('.site-header');
          const hb = header?.getBoundingClientRect();
          const hs = header ? getComputedStyle(header) : null;
          const obstacle = hs && ['fixed', 'sticky'].includes(hs.position) && hb.bottom > 0 ? hb.bottom : 0;
          return { top: box.top, bottom: box.bottom, obstacle, height: innerHeight };
        }, hash);
        assert.ok(geometry, `${route}: ${hash} desaparecido`);
        assert.ok(geometry.top >= geometry.obstacle - 2, `${route}: ${hash} oculto bajo cabecera (${JSON.stringify(geometry)})`);
        assert.ok(geometry.top < geometry.height && geometry.bottom > 0, `${route}: ${hash} fuera del viewport`);
      }
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno TOC landing geometry');
} finally { await browser.close(); }
