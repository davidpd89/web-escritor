import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch();

try {
  const context = await browser.newContext({ serviceWorkers: 'block', reducedMotion: 'reduce' });
  await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
  await context.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
  await Promise.all(Array.from({ length: 6 }, async (_, index) => {
    const page = await context.newPage();
    try {
      const response = await page.goto(ORIGIN + '/', { waitUntil: 'domcontentloaded', timeout: 20000 });
      assert.ok(response?.ok(), `Portada sesión ${index}: HTTP ${response?.status()}`);
      await page.waitForFunction(() => document.documentElement.dataset.homeEditorialV3 === 'true', { timeout: 15000 });
      const result = await page.evaluate(() => {
        const main = document.querySelector('main');
        const headings = [...document.querySelectorAll('main h1')].filter(el => el.getClientRects().length && el.textContent.trim());
        return { main: !!main, headings: headings.length, text: main?.innerText.trim().length || 0 };
      });
      assert.ok(result.main, `Portada sesión ${index}: falta main`);
      assert.ok(result.headings > 0, `Portada sesión ${index}: falta H1 visible tras hidratación`);
      assert.ok(result.text > 100, `Portada sesión ${index}: contenido principal vacío (${result.text})`);
    } finally {
      await page.close();
    }
  }));
  await context.close();
} finally {
  await browser.close();
}
console.log('root-concurrent-home-hydration: OK');