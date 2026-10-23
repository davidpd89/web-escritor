import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const html = fs.readFileSync('offline.html', 'utf8');
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  await page.route('**/*', route => route.abort());
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setContent(html, { waitUntil: 'domcontentloaded' });
  const heading = page.locator('main h1');
  assert.equal(await heading.count(), 1);
  assert.ok((await heading.innerText()).trim().length > 15);
  const retry = page.getByRole('button', { name: 'Reintentar' });
  const back = page.getByRole('button', { name: 'Volver atrás', hidden: true });
  const status = page.getByRole('status');
  assert.equal(await retry.isVisible(), true);
  assert.equal(await status.count(), 1);
  assert.equal(await status.getAttribute('aria-live'), 'polite');
  assert.equal(await back.isHidden(), true, 'Volver atrás debería ocultarse cuando no hay historial');
  assert.ok((await status.innerText()).trim().length > 0);
  const fonts = await page.evaluate(() => ({
    title: getComputedStyle(document.querySelector('h1')).fontFamily,
    body: getComputedStyle(document.body).fontFamily
  }));
  assert.match(fonts.title, /Instrument Serif/);
  assert.match(fonts.body, /Manrope/);
  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 800 });
    const dimensions = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth
    }));
    assert.ok(dimensions.document <= dimensions.viewport + 1, `Overflow a ${width}px`);
    const rect = await retry.boundingBox();
    assert.ok(rect && rect.width >= 44 && rect.height >= 44, `Objetivo táctil insuficiente a ${width}px`);
  }
  await retry.focus();
  assert.equal(await retry.evaluate(el => document.activeElement === el), true);
  assert.deepEqual(errors, []);
  await context.close();
} finally {
  await browser.close();
}
console.log('PASS: pantalla offline accesible y utilizable entre 320 y 1440px');