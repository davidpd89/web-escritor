import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTE = '/donde-empieza-la-jaula/';
const browser = await chromium.launch({ headless: true });

try {
  for (const width of [320, 360, 390, 768, 1024, 1440]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const imageRequests = [];
    page.on('request', request => {
      if (request.resourceType() === 'image') imageRequests.push(request.url());
    });

    const response = await page.goto(`${ORIGIN}${ROUTE}`, { waitUntil: 'networkidle' });
    assert.equal(response?.status(), 200, `${ROUTE} ${width}px: HTTP incorrecto`);

    const cover = page.locator('.book-cover-fallback');
    await cover.waitFor({ state: 'visible' });
    const result = await cover.evaluate(element => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height, left: rect.left, right: rect.right, viewport: document.documentElement.clientWidth };
    });

    assert.ok(result.width > 0 && result.height > 0, `${ROUTE} ${width}px: portada sin dimensiones ${JSON.stringify(result)}`);
    assert.ok(Math.abs(result.width / result.height - 2 / 3) < 0.08, `${ROUTE} ${width}px: proporción de portada ${result.width / result.height}`);
    assert.ok(result.left >= -1 && result.right <= result.viewport + 1, `${ROUTE} ${width}px: portada desbordada ${JSON.stringify(result)}`);
    assert.equal(await page.locator('.book-cover-zone img').count(), 0, `${ROUTE} ${width}px: la portada provisional incorporó una imagen no prevista`);

    const externalImages = imageRequests.filter(url => !url.startsWith(ORIGIN) && !url.startsWith('data:'));
    assert.deepEqual(externalImages, [], `${ROUTE} ${width}px: imágenes externas solicitadas ${JSON.stringify(externalImages)}`);
    await page.close();
  }
} finally {
  await browser.close();
}

console.log('OK: portada provisional estable y sin imágenes externas');