import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const EXPECTED = ['El Mensajero', 'El Sabio del Espejo', 'La Silenciadora', 'El Guardián'];
const browser = await chromium.launch({headless:true});
try {
  for (const seed of [0.999, 0]) {
    for (let profile=0; profile<4; profile++) {
      const context = await browser.newContext();
      await context.route('**/*', r => new URL(r.request().url()).origin === ORIGIN ? r.continue() : r.abort());
      await context.addInitScript(v => { Math.random = () => v; }, seed);
      const page = await context.newPage();
      await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/`, {waitUntil:'load'});
      const index = seed === 0.999 ? profile : [3,0,1,2][profile];
      for (let question=0; question<5; question++) {
        assert.equal(await page.locator('.quiz-option').count(), 4);
        const option = page.locator('.quiz-option').nth(index);
        if (question % 2 === 0) await option.click();
        else { await option.focus(); await page.keyboard.press('Enter'); }
      }
      assert.equal((await page.locator('[data-quiz-result-name]').innerText()).trim(), EXPECTED[profile]);
      assert.equal(await page.locator('[data-quiz-result]').isVisible(), true);
      assert.equal(await page.locator('[data-quiz-result]').evaluate(el => el === document.activeElement), true);
      assert.equal(await page.locator('[data-quiz-progress]').evaluate(el => parseFloat(el.style.width)), 100);
      await page.locator('[data-quiz-restart]').click();
      assert.equal(await page.locator('[data-quiz-result]').isHidden(), true);
      assert.match(await page.locator('[data-quiz-step]').innerText(), /Pregunta 1 de 5/);
      assert.equal(await page.locator('[data-quiz-progress]').evaluate(el => parseFloat(el.style.width)), 0);
      assert.equal(await page.locator('[data-quiz-result]').getAttribute('data-result'), null);
      await context.close();
    }
  }
} finally { await browser.close(); }
console.log('PASS books quiz: four outcomes, two permutations, mixed input and restart');
