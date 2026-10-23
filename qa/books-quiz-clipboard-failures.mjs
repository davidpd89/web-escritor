import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for (const denied of [false,true]) {
    const context = await browser.newContext();
    await context.route('**/*', r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
    await context.addInitScript(blocked => {
      Object.defineProperty(navigator,'share',{configurable:true,value:undefined});
      Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text => {
        window.__copied = text;
        if (blocked) throw new DOMException('Permission denied','NotAllowedError');
      }}});
    }, denied);
    const page = await context.newPage();
    await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`,{waitUntil:'load'});
    for (let i=0;i<5;i++) await page.locator('.quiz-option').first().click();
    const result = await page.locator('[data-quiz-result-name]').innerText();
    await page.locator('[data-quiz-share]').click();
    const label = await page.locator('[data-quiz-share]').innerText();
    assert.match(label, denied ? /No se pudo copiar/i : /Texto copiado/i);
    assert.equal(await page.locator('[data-quiz-result-name]').innerText(), result);
    const copied = await page.evaluate(() => window.__copied);
    assert.ok(copied.includes('/libros/samuel-entre-mundos/#quiz-noveris'));
    await context.close();
  }
} finally { await browser.close(); }
console.log('PASS clipboard outcome parity');
