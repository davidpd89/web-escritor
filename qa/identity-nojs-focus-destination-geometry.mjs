import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.IDENTITY_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 390, 768, 1440]) {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width, height: 900 } });
    try {
      const page = await context.newPage();
      for (const [source, target] of [['/autor.html', '/prensa.html'], ['/prensa.html', '/autor.html']]) {
        const response = await page.goto(new URL(source, BASE).href, { waitUntil: 'load' });
        assert.equal(response?.status(), 200, `${source} @ ${width}: HTTP incorrecto`);
        const links = page.locator(`a[href='${target}']`);
        let link = null;
        for (let i = 0; i < await links.count(); i++) {
          const candidate = links.nth(i);
          if (await candidate.isVisible() && (await candidate.innerText()).trim()) { link = candidate; break; }
        }
        assert.ok(link, `${source} @ ${width}: falta enlace textual a ${target}`);
        await link.focus();
        const focused = await link.evaluate(el => {
          const r = el.getBoundingClientRect();
          return { focused: document.activeElement === el, left: r.left, right: r.right, top: r.top, bottom: r.bottom };
        });
        assert.ok(focused.focused, `${source} @ ${width}: enlace no enfocable`);
        assert.ok(focused.right > 0 && focused.left < width && focused.bottom > 0 && focused.top < 900, `${source} @ ${width}: enlace fuera del viewport`);
        await page.keyboard.press('Enter');
        await page.waitForURL(url => url.pathname === target);
        const heading = page.locator('main h1').first();
        assert.ok(await heading.isVisible(), `${target} @ ${width}: H1 no visible`);
        const rect = await heading.boundingBox();
        assert.ok(rect && rect.x >= -1 && rect.x + rect.width <= width + 1, `${target} @ ${width}: H1 desbordado ${JSON.stringify(rect)}`);
        assert.ok((await heading.innerText()).trim(), `${target} @ ${width}: H1 vacío`);
      }
    } finally { await context.close(); }
  }
} finally { await browser.close(); }
