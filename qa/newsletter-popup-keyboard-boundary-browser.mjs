import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const PATH = '/cuaderno/que-es-el-portal-fantasy/';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  await page.addInitScript(() => {
    try {
      localStorage.removeItem('nl-popup-ts');
      localStorage.removeItem('nl-subscribed');
    } catch {}
  });
  const response = await page.goto(ORIGIN + PATH, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${PATH}: la página debe cargar`);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  const dialog = page.locator('#nl-popup-dialog');
  await dialog.waitFor({ state: 'visible' });
  assert.ok(await dialog.evaluate(el => el.matches(':modal')), `${PATH}: el popup debe ser modal`);
  assert.ok(await dialog.evaluate(el => {
    const id = el.getAttribute('aria-labelledby');
    return Boolean(id && document.getElementById(id)?.textContent.trim());
  }), `${PATH}: falta nombre accesible del diálogo`);
  const first = dialog.locator('#nl-popup-close');
  const last = dialog.locator('#nl-popup-skip');
  await first.focus();
  await page.keyboard.press('Shift+Tab');
  assert.ok(await last.evaluate(el => document.activeElement === el), `${PATH}: Mayús+Tab debe volver al último control del popup`);
  await page.keyboard.press('Tab');
  assert.ok(await first.evaluate(el => document.activeElement === el), `${PATH}: Tab debe volver al primer control del popup`);
  await page.keyboard.press('Escape');
  await dialog.waitFor({ state: 'detached' });
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-popup-keyboard-boundary-browser: PASS');
