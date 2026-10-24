import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assistantContextStarters } from '../assets/assistant-widget-core.mjs';

const O = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const routes = [
  '/', '/las-manecillas-del-recuerdo/', '/libros/samuel-entre-mundos/',
  '/universo/noveris/', '/herramientas/', '/editoriales/',
  '/convocatorias-escritores/', '/prensa.html', '/eventos.html'
];
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.route('**/*', r => new URL(r.request().url()).origin === O ? r.continue() : r.abort());
  for (const route of routes) {
    await page.goto(`${O}/asistente/embed.html?from=${encodeURIComponent(route)}`, { waitUntil: 'load' });
    const actual = await page.locator('[data-assistant-example]').evaluateAll(buttons => buttons.map(b => b.dataset.assistantExample));
    assert.deepEqual(actual, assistantContextStarters(route), `${route}: incorrect contextual starters`);
    assert.equal(new Set(actual).size, 3, `${route}: duplicate starter`);
    for (const button of await page.locator('[data-assistant-example]').all()) {
      assert.ok((await button.innerText()).trim().length >= 6, `${route}: empty starter label`);
      assert.ok(await button.isVisible(), `${route}: hidden starter`);
    }
  }
} finally {
  await browser.close();
}
console.log('PASS assistant contextual starter matrix');
