import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';
import { readKeyboardFocusState, waitForKeyboardFocusState } from './keyboard-focus-state.mjs';

for (const [name, launcher] of Object.entries({ chromium, firefox, webkit })) {
  const browser = await launcher.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 400 }, reducedMotion: 'reduce' });
    await page.setContent('<button id="visible">Visible</button><div inert><button id="blocked">Blocked</button></div><button id="outside" style="position:absolute;top:2000px">Outside</button>');
    await page.focus('#visible');
    assert.equal((await waitForKeyboardFocusState(page)).ok, true, `${name}: foco visible`);
    await page.evaluate(() => document.querySelector('#outside').focus({ preventScroll: true }));
    assert.equal((await page.evaluate(readKeyboardFocusState, false)).ok, false, `${name}: foco fuera de viewport`);
    await page.evaluate(() => {
      document.querySelector('#blocked').parentElement.removeAttribute('inert');
      document.querySelector('#blocked').focus({ preventScroll: true });
      document.querySelector('#blocked').parentElement.setAttribute('inert', '');
    });
    const blocked = await page.evaluate(readKeyboardFocusState, false);
    assert.equal(blocked.ok, false, `${name}: foco dentro de inert`);
    await page.close();
    console.log(`PASS ${name}: keyboard focus contract`);
  } finally {
    await browser.close();
  }
}
