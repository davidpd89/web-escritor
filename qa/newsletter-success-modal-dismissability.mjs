import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';
import { createServer } from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const ROOT = process.cwd();
const MIME = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml'],
  ['.woff2', 'font/woff2']
]);

const server = createServer((req, res) => {
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(req.url, 'http://127.0.0.1').pathname);
  } catch {
    res.writeHead(400).end();
    return;
  }
  const relative = pathname.replace(/^\/+/, '');
  const file = path.resolve(ROOT, relative.endsWith('/') || !relative ? relative + 'index.html' : relative);
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, {
    'Content-Type': MIME.get(path.extname(file)) || 'application/octet-stream'
  });
  res.end(fs.readFileSync(file));
});

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;
const engines = { chromium, firefox, webkit };
const selected = (process.argv.find(x => x.startsWith('--engines='))?.split('=')[1] || 'chromium,firefox,webkit').split(',');

try {
  for (const name of selected) {
    assert.ok(engines[name], `Motor desconocido: ${name}`);
    const options = { headless: true };
    if (name === 'chromium' && process.env.QA_CHROMIUM_EXECUTABLE_PATH) {
      options.executablePath = process.env.QA_CHROMIUM_EXECUTABLE_PATH;
    }
    const browser = await engines[name].launch(options);
    try {
      const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
      const page = await context.newPage();
      await page.route(/^https?:\/\/(?!127\.0\.0\.1)/, route => route.abort());
      await page.addInitScript(() => {
        localStorage.removeItem('nl-popup-ts');
        localStorage.removeItem('nl-subscribed');
        window.DPNewsletterGeneral = {
          postNewsletter: async () => ({ ok: true, state: 'pending_confirmation' })
        };
      });
      const response = await page.goto(`${ORIGIN}/cuaderno/`, { waitUntil: 'domcontentloaded' });
      assert.equal(response.status(), 200);
      await page.waitForFunction(() => typeof window.postNewsletter === 'function' || document.querySelector('script[src*="newsletter-popup.js"]'));
      await page.evaluate(() => document.dispatchEvent(new MouseEvent('mouseleave', {
        bubbles: true,
        clientY: -1
      })));
      const dialog = page.locator('#nl-popup-dialog');
      await page.waitForFunction(() => document.querySelector('#nl-popup-dialog')?.open === true);
      await dialog.locator('#nl-popup-email').fill('lector@example.com');
      await dialog.locator('#nl-popup-submit').click();
      await dialog.locator('.nl-popup-result-title').waitFor({ state: 'visible' });
      assert.equal(await dialog.evaluate(el => el.open), true);
      const close = dialog.getByRole('button', { name: /cerrar|no, gracias|volver|continuar/i });
      assert.ok(await close.count() > 0, `${name}: la confirmación elimina todos los botones de cierre`);
      await close.first().click();
      await page.waitForFunction(() => !document.querySelector('#nl-popup-dialog')?.open);
      assert.equal(await page.locator('dialog[open]').count(), 0);
      await context.close();
      console.log(`PASS ${name}: confirmación cerrable`);
    } finally {
      await browser.close();
    }
  }
} finally {
  await new Promise(resolve => server.close(resolve));
}