import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [390, 1440]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      return url.origin === new URL(BASE).origin ? route.continue() : route.abort();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(BASE + '/libros/samuel-entre-mundos/#quiz-noveris', {waitUntil:'load'});
    for (let i=0;i<5;i++) {
      const option = page.locator('[data-quiz-options] .quiz-option').first();
      await option.focus();
      await page.keyboard.press('Enter');
    }
    assert.equal(await page.locator('[data-quiz-result]').isVisible(),true);
    const buy = page.locator('[data-quiz-result] [data-buy-modal]');
    await buy.click();
    const dialogs = page.locator('dialog[open], [role="dialog"]:visible');
    assert.equal(await dialogs.count(),1,'Debe existir un único diálogo de compra visible');
    await buy.evaluate(el => {el.click();el.click();});
    assert.equal(await dialogs.count(),1,'Las activaciones repetidas no deben duplicar el diálogo');
    assert.equal(new URL(page.url()).origin,new URL(BASE).origin,'La acción no debe navegar automáticamente a una tienda');
    assert.deepEqual(errors,[]);
    await context.close();
  }
} finally {await browser.close();}
console.log('libros-buy-modal-idempotence: OK');