import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const expected = [
  ['#club-kind', 'nonfiction'],
  ['#club-genre', 'memoir'],
  ['#club-duration', '90'],
  ['#club-tone', 'deep'],
  ['#club-scope', 'partial']
];

async function run(mode) {
  const context = await browser.newContext();
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  await page.goto(`${origin}/clubes-de-lectura/preparar-sesion/`, { waitUntil: 'load' });
  if (mode === 'keyboard') {
    await page.locator('#club-title').focus();
    await page.keyboard.insertText('Memorias de una ciudad');
    for (const [selector, value] of expected) {
      await page.locator(selector).focus();
      await page.keyboard.press('End');
      assert.equal(await page.locator(selector).inputValue(), value, `${selector}: selección de teclado`);
    }
    await page.locator('[data-club-session-form] button[type=submit]').focus();
    await page.keyboard.press('Enter');
  } else {
    await page.fill('#club-title', 'Memorias de una ciudad');
    for (const [selector, value] of expected) await page.selectOption(selector, value);
    await page.locator('[data-club-session-form] button[type=submit]').click();
  }
  const result = await page.locator('[data-club-session-output]').innerText();
  await context.close();
  return result;
}

try {
  assert.equal(await run('keyboard'), await run('pointer'));
} finally {
  await browser.close();
}
console.log('club-session-input-modality: OK');