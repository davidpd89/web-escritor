import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const routes = ['/cuaderno/', '/cuaderno/temas/', '/cuaderno/temas/fantasia-de-portales/', '/cuaderno/que-es-el-portal-fantasy/'];
const selector = '.cuaderno-feature h2 a, .cuaderno-entry h3 a, .cuaderno-topics-entry h2 a, .cuaderno-topic-step h2 a, .article-related a';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390]) for (const route of routes) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
    await context.route('**/*', r => new URL(r.request().url()).origin === new URL(BASE).origin ? r.continue() : r.abort());
    await context.addInitScript(() => localStorage.setItem('nl-popup-ts', String(Date.now())));
    const page = await context.newPage();
    try {
      await page.goto(BASE + route);
      await page.evaluate(() => {
        document.documentElement.style.fontSize = '200%';
        const css = document.createElement('link');
        css.rel = 'stylesheet';
        css.href = '/qa/text-spacing.css';
        document.head.appendChild(css);
      });
      await page.waitForFunction(() => [...document.styleSheets].some(s => s.href?.includes('/qa/text-spacing.css')));
      const links = page.locator(selector);
      assert.ok(await links.count() > 0, route);
      for (let i = 0; i < await links.count(); i++) {
        const link = links.nth(i);
        await link.scrollIntoViewIfNeeded();
        const hit = await link.evaluate(el => {
          const r = [...el.getClientRects()].find(x => x.width > 3 && x.height > 3 && x.top >= 0 && x.bottom <= innerHeight);
          if (!r) return { ok: false, reason: 'sin región visible' };
          const x = Math.max(1, Math.min(innerWidth - 2, r.left + r.width / 2));
          const y = r.top + r.height / 2;
          const target = document.elementFromPoint(x, y);
          return { ok: !!target && (el === target || el.contains(target)), target: target?.tagName, x, y };
        });
        assert.ok(hit.ok, `${route} ${width}px enlace ${i}: ${JSON.stringify(hit)}`);
      }
    } finally { await context.close(); }
  }
  console.log('PASS cuaderno text-zoom hit testing');
} finally { await browser.close(); }
