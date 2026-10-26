import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  const seed = await browser.newPage();
  const response = await seed.goto(`${ORIGIN}/recomendaciones/`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), '/recomendaciones/: catálogo no disponible');
  const paths = await seed.locator('script[type="application/ld+json"]').evaluateAll(nodes => {
    const urls = [];
    for (const node of nodes) {
      try {
        const data = JSON.parse(node.textContent);
        if (data['@type'] === 'ItemList') {
          for (const entry of data.itemListElement || []) {
            const url = entry.item?.url;
            if (typeof url === 'string') {
              const parsed = new URL(url);
              if (parsed.pathname.startsWith('/recomendaciones/libros/')) urls.push(parsed.pathname);
            }
          }
        }
      } catch {}
    }
    return [...new Set(urls)].slice(0, 9);
  });
  assert.ok(paths.length >= 3, '/recomendaciones/: faltan fichas bibliográficas en el catálogo publicado');
  await seed.close();
  await Promise.all(paths.map(async (route, i) => {
    const width = [320, 360, 390][i % 3];
    const context = await browser.newContext({ viewport: { width, height: 780 } });
    try {
      const page = await context.newPage();
      const result = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.ok(result?.ok(), `${route} ${width}px: HTTP ${result?.status()}`);
      const main = page.locator('main').first();
      assert.ok((await main.innerText()).trim().length > 40, `${route} ${width}px: ficha vacía`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 2, `${route} ${width}px: overflow ${overflow}px`);
    } finally {
      await context.close();
    }
  }));
  console.log('PASS: fichas bibliográficas móviles concurrentes');
} finally {
  await browser.close();
}