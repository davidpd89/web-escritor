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
  for (const duration of ['30', '60', '90']) {
    const title = `Lectura de prueba ${duration}`;
    await page.fill('#club-title', title);
    await page.selectOption('#club-duration', duration);
    await page.locator('[data-club-session-form] button[type=submit]').click();
    const blocks = await page.locator('[data-club-session-output] .club-session-block').evaluateAll(nodes => nodes.map(node => ({
      heading: node.querySelector('h3').textContent.split(' · ')[0],
      items: [...node.querySelectorAll('li')].map(item => item.textContent)
    })));
    await page.locator('[data-club-session-copy]').click();
    const copied = await page.evaluate(() => navigator.clipboard.readText());
    assert.ok(copied.includes(title));
    assert.ok(copied.includes(`${duration} minutos`));
    let previous = -1;
    for (const block of blocks) {
      const pos = copied.indexOf(block.heading);
      assert.ok(pos > previous, `${duration}: bloque ausente o desordenado: ${block.heading}`);
      previous = pos;
      for (const item of block.items) {
        const itemPos = copied.indexOf(item);
        assert.ok(itemPos > previous, `${duration}: pregunta omitida o desordenada: ${item}`);
        previous = itemPos;
      }
    }
    assert.ok(!/undefined|\[object Object\]/.test(copied));
  }
} finally {
  await browser.close();
}
console.log('club-session-copy-fidelity: OK');