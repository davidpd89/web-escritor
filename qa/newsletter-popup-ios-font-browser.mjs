import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  await context.addInitScript(() => {
    localStorage.removeItem('nl-popup-ts');
    localStorage.removeItem('nl-subscribed');
  });
  const page = await context.newPage();
  const route = '/cuaderno/que-es-el-portal-fantasy/';
  const response = await page.goto(ORIGIN + route, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: HTTP ${response?.status()}`);
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await page.locator('#nl-popup-dialog').waitFor({ state: 'visible' });
  const input = page.locator('#nl-popup-email');
  await input.focus();
  const size = await input.evaluate(el => parseFloat(getComputedStyle(el).fontSize));
  assert.ok(size >= 16, `${route}: #nl-popup-email usa ${size}px; mínimo 16px para evitar zoom de foco en iOS`);
  await context.close();
} finally {
  await browser.close();
}
console.log('newsletter-popup-ios-font-browser: OK');
