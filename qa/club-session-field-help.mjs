import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
const page = await context.newPage();

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  for (const id of ['club-title', 'club-author', 'club-kind', 'club-genre', 'club-duration', 'club-tone', 'club-scope', 'club-tokens']) {
    const label = page.locator(`label[for="${id}"]`);
    assert.equal(await label.count(), 1, `${id}: falta etiqueta única`);
    await label.click();
    assert.equal(await page.evaluate(() => document.activeElement?.id), id, `${id}: la etiqueta no enfoca su campo`);
  }
  const description = await page.locator('#club-tokens').evaluate(input => {
    const ids = (input.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
    return ids.map(id => document.getElementById(id)?.textContent || '').join(' ');
  });
  assert.match(description, /cuatro|4/i, 'La ayuda sobre el límite de cuatro temas no está asociada al campo');
} finally {
  await browser.close();
}
console.log('club-session-field-help: OK');