import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, ORIGIN } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const route of [
    '/pagina-inexistente-2026/',
    '/cuaderno/entrada-que-no-existe/',
    '/libros/obra-desconocida/'
  ]) {
    const { context, page } = await localPage(browser);
    await page.addInitScript(() => sessionStorage.setItem('dp-intro-seen', '1'));
    const response = await page.goto(ORIGIN + route);

    assert.equal(response.status(), 404, route);
    assert.match(await page.locator('meta[name="robots"]').getAttribute('content'), /noindex/i);
    assert.equal(await page.locator('main[data-findability-page="404"]').count(), 1);
    assert.equal(await page.locator('main h1').count(), 1);

    const links = await page.locator('.findability-recovery a[href]').evaluateAll(nodes =>
      nodes.map(a => a.getAttribute('href'))
    );
    assert(links.includes('/'));
    assert(links.includes('/libros/'));
    assert(links.includes('/mapa-del-sitio/'));

    await page.locator('.findability-primary[href="/"]').click();
    await page.waitForURL(ORIGIN + '/');
    assert.equal(await page.locator('main#contenido').count(), 1);
    await context.close();
  }
  console.log('PASS root-404-recovery-journey');
} finally {
  await browser.close();
}