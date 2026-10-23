import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const facts = JSON.parse(fs.readFileSync('editorial-facts.json','utf8')).books.samuelEntreMundos;
const browser = await chromium.launch({headless:true});
try {
  const context = await browser.newContext();
  await context.route('**/*', r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
  const page = await context.newPage();
  await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`,{waitUntil:'load'});
  for (const selector of ['.samuel-actions [data-buy-modal]','#comprar [data-buy-modal]','#ejemplar-firmado [data-buy-modal]']) {
    const trigger = page.locator(selector).first();
    await trigger.click();
    const dialog = page.locator('#buy-dialog');
    assert.equal(await dialog.evaluate(el => el.open),true,selector);
    const links = await dialog.locator('a.buy-option').evaluateAll(a => a.map(el => ({href:el.href,rel:el.rel})));
    assert.equal(links.length,2);
    assert.equal(links[0].href,facts.purchaseUrls.amazonEs);
    assert.ok(links[1].href.startsWith(facts.purchaseUrls.casaDelLibro));
    assert.ok(['sponsored','nofollow','noopener','noreferrer'].every(x => links[0].rel.split(' ').includes(x)));
    await dialog.locator('#buy-dialog-close').click();
    assert.equal(await trigger.evaluate(el => el === document.activeElement),true);
    assert.equal(await page.locator('#buy-dialog').count(),1,'diálogo duplicado');
  }
  for (let i=0;i<5;i++) await page.locator('.quiz-option').first().click();
  const resultTrigger = page.locator('[data-quiz-result] [data-buy-modal]');
  await resultTrigger.click();
  assert.equal(await page.locator('#buy-dialog').evaluate(el => el.open),true);
  await page.locator('#buy-dialog-close').click();
  assert.equal(await resultTrigger.evaluate(el => el === document.activeElement),true);
  await context.close();
} finally { await browser.close(); }
console.log('PASS modal trigger matrix');
