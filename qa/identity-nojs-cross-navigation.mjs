import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.IDENTITY_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
try {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    for (const [source, target] of [['/autor.html', '/prensa.html'], ['/prensa.html', '/autor.html']]) {
      const response = await page.goto(new URL(source, BASE).href, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `${source}: HTTP ${response?.status()}`);
      const links = page.locator(`a[href='${target}']`);
      const count = await links.count();
      let link = null;
      for (let i = 0; i < count; i++) {
        const candidate = links.nth(i);
        if (await candidate.isVisible() && (await candidate.innerText()).trim()) {
          link = candidate;
          break;
        }
      }
      assert.ok(link, `${source}: falta enlace visible y nombrado hacia ${target}`);
      await link.click();
      await page.waitForURL(url => url.pathname === target);
      assert.equal(new URL(page.url()).pathname, target, `${source}: navegación incorrecta hacia ${target}`);
      assert.ok(await page.locator('main h1').first().isVisible(), `${target}: destino sin H1 visible`);
    }
  } finally {
    await context.close();
  }
} finally {
  await browser.close();
}
