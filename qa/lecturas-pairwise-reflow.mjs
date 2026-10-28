import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const server = createServer((req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    let file = path.resolve(root, '.' + pathname);
    if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403); res.end(); return; }
    if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    res.setHeader('Content-Type', file.endsWith('.css') ? 'text/css' : file.endsWith('.woff2') ? 'font/woff2' : 'text/html');
    res.end(fs.readFileSync(file));
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
const widths = [320, 390, 768, 1280];
try {
  for (const width of widths) for (const fontSize of [16, 32]) {
    const context = await browser.newContext({ viewport: { width, height: 850 }, serviceWorkers: 'block' });
    await context.route('**/*', route => route.request().url().startsWith(origin + '/') ? route.continue() : route.abort());
    const page = await context.newPage();
    try {
      await page.goto(origin + '/lecturas/');
      await page.evaluate(size => { document.documentElement.style.fontSize = size + 'px'; }, fontSize);
      const errors = await page.evaluate(() => {
        const selectors = ['main', '.reading-hero', '.reading-grid', '.reading-card', '.reading-card h3', '.reading-card p'];
        return selectors.flatMap(selector => [...document.querySelectorAll(selector)].flatMap(el => {
          const rect = el.getBoundingClientRect();
          const outside = rect.left < -1 || rect.right > innerWidth + 1;
          const clipped = el.scrollWidth > el.clientWidth + 1;
          return outside || clipped ? [`${selector}: outside=${outside}, clipped=${clipped}`] : [];
        }));
      });
      assert.deepEqual(errors, [], `Reflow ${width}px, fuente ${fontSize}px`);
      assert.equal(await page.locator('article.reading-card').count(), 1);
      console.log(`PASS ${width}px font=${fontSize}px`);
    } finally { await context.close(); }
  }
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
