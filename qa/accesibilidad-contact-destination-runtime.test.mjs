import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.BASE_URL || process.env.TEST_BASE_URL || 'http://127.0.0.1:8000';

test('accesibilidad: recorrido real de reporte de barreras', async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    await page.goto(new URL('/accesibilidad/', base).href);
    const section = page.locator('section[aria-labelledby=contacto]');
    const link = section.getByRole('link');
    assert.equal(await link.count(), 1, '/accesibilidad/: falta un destino de reporte inequívoco');
    const href = await link.getAttribute('href');
    assert.ok(href, '/accesibilidad/: enlace de contacto sin destino');
    if (href.startsWith('mailto:')) {
      assert.match(href, /^mailto:[^\s@]+@[^\s@]+\.[^\s@]+/i);
      return;
    }
    const destination = new URL(href, page.url());
    assert.equal(destination.origin, new URL(base).origin, '/accesibilidad/: contacto fuera del dominio sin explicación');
    const response = await page.goto(destination.href);
    assert.equal(response?.status(), 200, `/accesibilidad/: destino ${destination.pathname} no disponible`);
    if (destination.hash) {
      const target = page.locator(`[id=${JSON.stringify(decodeURIComponent(destination.hash.slice(1)))}]`);
      await target.waitFor({ state: 'attached' });
    }
    const mechanisms = await page.locator('a[href^="mailto:"], form, [data-email-reveal]').count();
    assert.ok(mechanisms > 0, `/accesibilidad/: ${destination.pathname} no ofrece mecanismo de contacto`);
  } finally {
    await browser.close();
  }
});