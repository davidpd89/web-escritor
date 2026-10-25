import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const base = (process.env.BASE_URL || process.env.SITE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const browser = await chromium.launch({ headless: true });
try {
  for (const width of [320, 360, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 780 } });
    try {
      const response = await page.goto(`${base}/redes-sociales/`, { waitUntil: 'domcontentloaded' });
      assert.equal(response.status(), 200, `redes-sociales: HTTP ${response.status()} a ${width}px`);
      const jsonResponse = await page.request.get(`${base}/redes-sociales/social-metrics.json`);
      assert.equal(jsonResponse.status(), 200, `social-metrics.json: HTTP ${jsonResponse.status()}`);
      const data = await jsonResponse.json();
      for (const network of data.networks) {
        const card = page.locator(`#social-grid .social-card[data-network="${network.id}"]`);
        assert.equal(await card.count(), 1, `redes-sociales ${width}px: tarjeta ${network.id}`);
        const link = card.locator('a[href]');
        assert.equal(await link.count(), 1, `redes-sociales ${width}px: enlace ${network.id}`);
        assert.equal(await link.getAttribute('href'), network.profile_url, `redes-sociales ${width}px: URL de ${network.id}`);
        assert.ok(await link.isVisible(), `redes-sociales ${width}px: enlace oculto ${network.id}`);
      }
    } finally {
      await page.close();
    }
  }
} finally {
  await browser.close();
}
