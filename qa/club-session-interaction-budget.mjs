import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
const page = await context.newPage();

try {
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  await page.fill('#club-title', 'Sesión de rendimiento');
  await page.fill('#club-tokens', 'memoria, identidad, familia, confianza');
  await page.selectOption('#club-duration', '90');
  await page.locator('[data-club-session-form] button[type=submit]').click();
  const stats = await page.evaluate(() => {
    const button = document.querySelector('[data-club-session-alt]');
    const output = document.querySelector('[data-club-session-output]');
    const start = performance.now();
    const samples = [];
    for (let i = 0; i < 100; i++) {
      const before = performance.now();
      button.click();
      samples.push(performance.now() - before);
    }
    return {
      elapsed: performance.now() - start,
      maxAction: Math.max(...samples),
      headings: output.querySelectorAll('h2').length,
      blocks: output.querySelectorAll('.club-session-block').length,
      nodes: output.querySelectorAll('*').length,
      visible: !output.hidden
    };
  });
  assert.equal(stats.visible, true);
  assert.equal(stats.headings, 1);
  assert.equal(stats.blocks, 5);
  assert.ok(stats.nodes < 100, `DOM acumulativo: ${stats.nodes} nodos`);
  assert.ok(stats.elapsed < 5000, `100 combinaciones tardaron ${stats.elapsed.toFixed(0)} ms`);
  assert.ok(stats.maxAction < 1000, `Interacción aislada demasiado lenta: ${stats.maxAction.toFixed(0)} ms`);
} finally {
  await browser.close();
}
console.log('club-session-interaction-budget: OK');