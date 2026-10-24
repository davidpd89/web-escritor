import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { chromium } from 'playwright';

const html = await fs.readFile(new URL('../publicar-web/index.html', import.meta.url), 'utf8');
const browser = await chromium.launch({ headless: true });
const widths = [1440, 768, 390, 320, 375, 1024, 320, 1440];

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.route('**/*', route => route.abort());
  await page.setContent(html);
  const initial = await page.locator('main a[href]').evaluateAll(links => links.map(a => a.getAttribute('href')));
  assert.ok(initial.length > 0, 'No hay enlaces interactivos');

  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    const result = await page.evaluate(() => ({
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      links: [...document.querySelectorAll('main a[href]')].map(a => ({
        href: a.getAttribute('href'),
        visible: a.getClientRects().length > 0 && getComputedStyle(a).visibility !== 'hidden',
      })),
    }));
    assert.ok(result.overflow <= 1, `${width}px: overflow horizontal ${result.overflow}px`);
    assert.deepEqual(result.links.map(x => x.href), initial, `${width}px: acciones alteradas`);
    assert.ok(result.links.every(x => x.visible), `${width}px: enlace oculto`);
  }
  console.log(`PASS publicar-web: ${widths.length} transiciones responsive`);
} finally {
  await browser.close();
}
