import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const tools = [
  ['manuscrito', '[data-chapter-paste]', '[data-chapter-analyzer] button[type="submit"]', '[data-chapter-results]'],
  ['dialogo', '#dialogue-text', '[data-dialogue-tool] button[type="submit"]', '[data-dialogue-results]'],
  ['legibilidad', '[data-readability-input]', '[data-readability-form] button[type="submit"]', '[data-readability-results]'],
  ['repeticiones', '[data-repetition-input]', '[data-repetition-form] button[type="submit"]', '[data-repetition-results]'],
  ['variedad-lexica', '[data-lexical-input]', '[data-lexical-form] button[type="submit"]', '[data-lexical-results]']
];
const sample = Array.from({length: 35}, (_, i) => `La puerta estaba abierta. Ana miró el reloj y recordó la conversación. —No pienso entrar —dijo Ana—. La noche era fría. Escena ${i + 1}.`).join('\n\n');
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320, 360, 390]) {
    for (const [name, input, submit, result] of tools) {
      const context = await browser.newContext({viewport:{width,height:760}});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      const url = `${ORIGIN}/herramientas/${name}/`;
      try {
        const response = await page.goto(url, {waitUntil:'load'});
        assert(response?.ok(), `${url} @${width}: HTTP ${response?.status()}`);
        await page.locator(input).fill(sample);
        await page.locator(submit).click();
        await page.locator(result).waitFor({state:'visible',timeout:10000});
        const metrics = await page.evaluate(() => ({document:document.documentElement.scrollWidth,body:document.body.scrollWidth,viewport:document.documentElement.clientWidth}));
        assert(metrics.document <= metrics.viewport + 1, `${url} @${width}: desbordamiento tras analizar: ${JSON.stringify(metrics)}`);
        assert(metrics.body <= metrics.viewport + 1, `${url} @${width}: body desbordado: ${JSON.stringify(metrics)}`);
        assert((await page.locator(result).innerText()).trim().length > 0, `${url} @${width}: resultados vacíos`);
        assert.deepEqual(errors, [], `${url} @${width}: errores JS ${errors.join('; ')}`);
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}
console.log('tools-mobile-results-smoke: PASS');