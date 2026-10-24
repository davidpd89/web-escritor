import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin });
const page = await context.newPage();

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  await page.fill('#club-title', 'TITULO_PRIVADO_47391');
  await page.fill('#club-author', 'AUTOR_PRIVADO_47391');
  await page.fill('#club-tokens', 'TEMA_PRIVADO_47391');
  await page.locator('[data-club-session-form] button[type=submit]').click();
  await page.fill('#club-title', 'Libro nuevo');
  await page.fill('#club-author', 'Autor nuevo');
  await page.fill('#club-tokens', 'amistad, justicia');
  await page.selectOption('#club-kind', 'nonfiction');
  await page.locator('[data-club-session-form] button[type=submit]').click();
  await page.locator('[data-club-session-copy]').click();
  const output = await page.locator('[data-club-session-output]').innerText();
  const copied = await page.evaluate(() => navigator.clipboard.readText());
  for (const stale of ['TITULO_PRIVADO_47391', 'AUTOR_PRIVADO_47391', 'TEMA_PRIVADO_47391']) {
    assert.ok(!output.includes(stale), `Resultado contaminado: ${stale}`);
    assert.ok(!copied.includes(stale), `Portapapeles contaminado: ${stale}`);
  }
  assert.match(output, /Libro nuevo/);
  assert.match(copied, /Autor nuevo/);
  assert.equal(await page.locator('[data-club-session-output] h2').count(), 1);
} finally {
  await browser.close();
}
console.log('club-session-multirun-isolation: OK');