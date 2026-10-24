import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for (const method of ['escape','button','back']) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/#para-quien`, {waitUntil:'load'});
    const trigger = page.locator('.samuel-actions [data-buy-modal]').first();
    await trigger.focus();
    await trigger.click();
    const dialog = page.locator('#buy-dialog');
    assert.equal(await dialog.evaluate(el => el.open), true);
    assert.equal(new URL(page.url()).hash, '#comprar');
    if (method === 'escape') await page.keyboard.press('Escape');
    if (method === 'button') await dialog.locator('#buy-dialog-close').click();
    if (method === 'back') await page.goBack({waitUntil:'domcontentloaded'});
    await page.waitForFunction(() => !document.querySelector('#buy-dialog')?.open);
    assert.equal(await trigger.evaluate(el => document.activeElement === el), true, `${method}: foco no restaurado`);
    assert.equal(new URL(page.url()).hash, '#para-quien', `${method}: fragmento histórico contaminado`);
    assert.equal(await page.locator('html').evaluate(el => el.classList.contains('modal-open')), false);
    await context.close();
  }
} finally { await browser.close(); }
console.log('PASS books modal history');
