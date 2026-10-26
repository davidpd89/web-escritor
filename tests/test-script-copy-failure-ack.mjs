import assert from 'node:assert/strict';
import { startSite, launch } from '../qa/errores-progresivo-browser-fixture.mjs';
const html = '<!doctype html><html><body><span data-samuel-quiz hidden></span><main><button class="copy-btn" data-copy-target="bio">Copiar</button><p id="bio">Texto editorial QA</p></main><script src="/script.js"></script></body></html>';
const site = await startSite({ '/__qa/copy.html': html });
const browser = await launch();
try {
  const context = await browser.newContext();
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
    document.execCommand = () => false;
  });
  const page = await context.newPage();
  await page.goto(site.origin + '/__qa/copy.html');
  await page.getByRole('button', { name: 'Copiar' }).click();
  await page.waitForTimeout(100);
  assert.equal((await page.locator('.copy-btn').innerText()).trim(), 'Copiar',
    'execCommand returned false: copy button must not falsely announce success');
  await context.close();
} finally { await browser.close(); await site.close(); }
console.log('PASS clipboard failure acknowledgement');
