import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { localPage, readyHome, ORIGIN } from './home-family-local-fixture.mjs';

const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [
    { width: 390, height: 844 },
    { width: 1280, height: 900 }
  ]) {
    const { context, page } = await localPage(browser, { viewport });
    await readyHome(page);

    const opener = page.locator('[data-explore-open]').first();
    await opener.click();
    assert.equal(await page.locator('[data-explore-dialog]').evaluate(el => el.open), true);

    await page.locator('[data-explore-dialog] .explore-row[href="/herramientas/"]').first().click();
    await page.waitForURL('**/herramientas/');
    await page.goBack({ waitUntil: 'load' });
    assert.equal(new URL(page.url()).pathname, '/');

    const state = await page.evaluate(() => ({
      modal: document.querySelector('[data-explore-dialog]')?.open,
      expanded: [...document.querySelectorAll('[data-explore-open]')].map(el => el.getAttribute('aria-expanded')),
      classOpen: document.documentElement.classList.contains('explore-open')
    }));
    assert.equal(state.modal, false, 'Modal abierto tras Atrás');
    assert.equal(state.classOpen, false, 'Clase visual residual');
    assert(state.expanded.every(value => value === 'false'));

    const main = page.locator('main#contenido');
    assert.equal(await main.getAttribute('inert'), null);
    await context.close();
  }
  console.log('PASS home-history-modal-restoration');
} finally {
  await browser.close();
}