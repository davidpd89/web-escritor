import assert from 'node:assert/strict';
import { stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { check } from './accesibilidad-fixture.mjs';

await check(async ({ page, origin }) => {
  const failures = [];
  page.on('response', response => { if (response.url().startsWith(origin) && response.status() >= 400) failures.push(`${response.status()} ${response.url()}`); });
  await page.reload({ waitUntil: 'load' });
  const paths = await page.evaluate(() => [...document.querySelectorAll('link[rel="stylesheet"][href], script[src]')].map(el => new URL(el.getAttribute('href') || el.getAttribute('src'), location.href)).filter(url => url.origin === location.origin).map(url => url.pathname));
  const unique = [...new Set(paths)];
  assert.ok(unique.includes('/assets/v1-accessibility-statement.css'));
  assert.ok(unique.includes('/assets/v1-shell.js'));
  assert.ok(unique.includes('/assets/email-reveal.js'));
  assert.equal(failures.length, 0, failures.join(' | '));
  let bytes = 0;
  for (const item of unique) {
    const info = await stat(resolve(process.cwd(), item.slice(1)));
    assert.ok(info.isFile(), item);
    bytes += info.size;
  }
  assert.ok(bytes <= 1100000, `CSS+JS declarados: ${bytes} bytes, presupuesto: 1100000`);
  assert.ok(unique.length <= 24, `Demasiados recursos CSS/JS: ${unique.length}`);
});
console.log('accesibilidad-asset-budget: PASS');
