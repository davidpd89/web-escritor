import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';

const port = 43872;
const origin = `http://127.0.0.1:${port}`;
const server = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { stdio: 'ignore' });
const browser = await chromium.launch({ headless: true });

try {
  let ready = false;
  for (let i = 0; i < 50; i++) {
    try { ready = (await fetch(`${origin}/fragmento/`)).ok; } catch {}
    if (ready) break;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.ok(ready, 'Servidor local no disponible');
  const page = await browser.newPage();
  await page.addInitScript(() => {
    sessionStorage.setItem('dp-intro-seen', '1');
    localStorage.setItem('dp-analytics-consent', JSON.stringify({ value: 'denied', v: 1, ts: Date.now() }));
  });
  await page.goto(`${origin}/fragmento/`);
  const dialog = page.locator('[data-explore-dialog]');
  const opener = page.locator('[data-explore-open]').first();
  assert.equal(await opener.count(), 1, 'Falta el control de apertura');

  for (let i = 0; i < 12; i++) {
    await opener.click();
    assert.equal(await dialog.evaluate(el => el.open), true, `Apertura ${i}`);
    assert.equal(await page.locator('[data-assistant-menu-link]').count(), 1, `Enlace duplicado en ciclo ${i}`);
    assert.equal(await opener.getAttribute('aria-expanded'), 'true');
    if (i % 2 === 0) {
      await page.locator('[data-explore-close]').click();
    } else {
      await page.keyboard.press('Escape');
    }
    await assertClosed(i);
  }
  console.log('assets-explore-repeat-idempotence: OK');

  async function assertClosed(i) {
    await page.waitForFunction(() => !document.querySelector('[data-explore-dialog]')?.open);
    assert.equal(await opener.getAttribute('aria-expanded'), 'false', `Estado incorrecto tras cierre ${i}`);
    assert.equal(await page.locator('html.explore-open').count(), 0, `Bloqueo persistente tras cierre ${i}`);
  }
} finally {
  await browser.close();
  server.kill();
}
