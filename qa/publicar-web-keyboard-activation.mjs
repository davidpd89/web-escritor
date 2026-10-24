import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { chromium } from 'playwright';

const html = await fs.readFile(new URL('../publicar-web/index.html', import.meta.url), 'utf8');
const browser = await chromium.launch({ headless: true });

try {
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  await page.setContent(html);
  const expected = await page.locator('main a[href]').evaluateAll(links => links.map(a => a.getAttribute('href')));
  assert.ok(expected.length > 0);

  await page.evaluate(() => {
    window.__clicks = [];
    document.addEventListener('click', event => {
      const anchor = event.target.closest('a[href]');
      if (!anchor) return;
      event.preventDefault();
      window.__clicks.push(anchor.getAttribute('href'));
    }, true);
  });

  for (const href of expected) {
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.getAttribute('href'));
    assert.equal(focused, href, `Orden de foco incorrecto para ${href}`);
    await page.keyboard.press('Enter');
  }

  const activated = await page.evaluate(() => window.__clicks);
  assert.deepEqual(activated, expected, 'Activaciones de teclado incompletas o duplicadas');
  console.log(`PASS publicar-web: ${expected.length} activaciones por teclado`);
} finally {
  await browser.close();
}
