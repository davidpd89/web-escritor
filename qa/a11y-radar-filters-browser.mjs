import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const server = createServer(async (req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const filename = path.resolve(ROOT, '.' + pathname, pathname.endsWith('/') ? 'index.html' : '');
  if (!filename.startsWith(ROOT + path.sep)) return res.writeHead(403).end();
  const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };
  try {
    res.setHeader('Content-Type', mime[path.extname(filename)] || 'application/octet-stream');
    res.end(await readFile(filename));
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 768, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 900 } });
    await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
    const page = await context.newPage();
    await page.goto(origin + '/convocatorias-escritores/', { waitUntil: 'domcontentloaded' });
    for (const selector of ['[data-radar-search]', '[data-radar-type]', '[data-radar-genre]', 'select[data-radar-kind]', '[data-radar-soon]', '[data-radar-expired]']) {
      const element = page.locator(selector);
      assert.equal(await element.count(), 1, `${width}: ${selector} ausente`);
      const named = await element.evaluate(el => Boolean(
        el.labels?.length || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')
      ));
      assert.ok(named, `${width}: ${selector} sin nombre accesible`);
    }
    const count = page.locator('[data-radar-count]');
    assert.equal(await count.getAttribute('aria-live'), 'polite', `${width}: contador sin aria-live`);
    assert.equal(await count.getAttribute('role'), 'status', `${width}: contador sin status`);
    const search = page.locator('[data-radar-search]');
    const before = (await count.textContent()).trim();
    await search.fill('zzzxqsinconvocatorias987654');
    await page.waitForFunction(() => /0|ningun|sin resultados/i.test(document.querySelector('[data-radar-count]')?.textContent || ''));
    assert.notEqual((await count.textContent()).trim(), before, `${width}: contador sin actualizacion`);
    assert.ok(await search.evaluate(el => el === document.activeElement), `${width}: busqueda pierde el foco`);
    await context.close();
  }
  console.log('a11y-radar-filters: OK');
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
