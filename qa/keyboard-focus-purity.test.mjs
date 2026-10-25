import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';
import { readKeyboardFocusState } from './keyboard-focus-state.mjs';

for (const [name, launcher] of Object.entries({ chromium, firefox, webkit })) {
  const browser = await launcher.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 600, height: 350 } });
    await page.setContent('<button id="first">First</button><div style="height:3000px"></div><button id="last">Last</button>');
    await page.evaluate(() => document.querySelector('#last').focus({ preventScroll: true }));
    const before = await page.evaluate(() => ({ x: scrollX, y: scrollY, id: document.activeElement.id }));
    for (let i = 0; i < 25; i++) {
      const result = await page.evaluate(readKeyboardFocusState, false);
      assert.equal(result.ok, false, `${name}: elemento fuera de pantalla`);
    }
    const after = await page.evaluate(() => ({ x: scrollX, y: scrollY, id: document.activeElement.id }));
    assert.deepEqual(after, before, `${name}: la inspección modificó el estado del navegador`);
    await page.close();
  } finally {
    await browser.close();
  }
}
console.log('PASS focus probe purity');
