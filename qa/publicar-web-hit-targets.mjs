import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { chromium } from 'playwright';

const html = await fs.readFile(new URL('../publicar-web/index.html', import.meta.url), 'utf8');
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [320, 390, 768, 1280]) {
    for (const zoom of [1, 2]) {
      const page = await browser.newPage({ viewport: { width, height: 900 } });
      await page.route('**/*', route => route.abort());
      await page.setContent(html);
      await page.evaluate(value => { document.documentElement.style.zoom = String(value); }, zoom);
      const results = await page.locator('main a[href]').evaluateAll(links => links.map(a => {
        const rect = a.getBoundingClientRect();
        const x = rect.x + rect.width / 2;
        const y = rect.y + rect.height / 2;
        return {
          href: a.getAttribute('href'),
          width: rect.width,
          height: rect.height,
          hit: document.elementFromPoint(x, y)?.closest('a') === a,
        };
      }));
      assert.ok(results.length > 0);
      for (const result of results) {
        assert.ok(result.width >= 24 * zoom, `${width}/${zoom}: ancho insuficiente ${result.href}`);
        assert.ok(result.height >= 24 * zoom, `${width}/${zoom}: altura insuficiente ${result.href}`);
        assert.ok(result.hit, `${width}/${zoom}: centro interceptado ${result.href}`);
      }
      await page.close();
    }
  }
  console.log('PASS publicar-web: objetivos geométricos en 8 configuraciones');
} finally {
  await browser.close();
}
