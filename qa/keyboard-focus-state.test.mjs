import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readKeyboardFocusState, waitForKeyboardFocusState } from './keyboard-focus-state.mjs';

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 800, height: 300 } });
  await page.setContent('<button id="target" style="margin-top:1200px">Target</button>');
  await page.evaluate(() => document.querySelector('#target').focus({ preventScroll: true }));
  assert.equal((await page.evaluate(readKeyboardFocusState, false)).ok, false);
  const outside = await waitForKeyboardFocusState(page, 100);
  assert.equal(outside.ok, false, 'a persistently off-screen target must still fail');
  assert.equal(await page.evaluate(() => scrollY), 0, 'the probe must never scroll the target');

  await page.evaluate(() => {
    setTimeout(() => document.querySelector('#target').scrollIntoView({ behavior: 'instant' }), 120);
  });
  const settled = await waitForKeyboardFocusState(page, 1000);
  assert.equal(settled.ok, true, 'wait for the browser to finish its focus scroll');
  assert.equal(settled.key, 'target');

  await page.evaluate(() => document.querySelector('#target').setAttribute('aria-hidden', 'true'));
  const hidden = await waitForKeyboardFocusState(page, 100);
  assert.equal(hidden.ok, false, 'an aria-hidden target must still fail');
  assert.equal(hidden.reason, 'inside aria-hidden/inert');

  await page.setContent('<button id="visible">Visible</button>');
  await page.focus('#visible');
  assert.equal((await waitForKeyboardFocusState(page)).ok, true);

  // A link that wraps: its bounding box spans the paragraph, its line boxes do not.
  await page.setContent('<p style="width:300px;font:16px/24px monospace">' + 'x'.repeat(25) + ' <a id="wrap" href="#w">ab cdefgh</a> ' + 'y'.repeat(30) + '</p>');
  await page.focus('#wrap');
  assert.ok(await page.evaluate(() => document.querySelector('#wrap').getClientRects().length > 1), 'fixture must wrap');
  assert.equal((await waitForKeyboardFocusState(page)).ok, true, 'a wrapped inline link is not obstructed');

  await page.setContent('<button id="under">Under</button><div style="position:fixed;inset:0;background:#000"></div>');
  await page.focus('#under');
  const covered = await waitForKeyboardFocusState(page, 100);
  assert.equal(covered.ok, false, 'a target under an overlay must still fail');
  assert.match(covered.reason, /obstructed/);
  await page.close();
} finally {
  await browser.close();
}
console.log('PASS keyboard focus probe: settled scroll, persistent off-screen failure, hidden failure and visible target');
