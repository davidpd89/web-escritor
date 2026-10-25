import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext();
  const page = await context.newPage();

  const response = await page.goto(`${BASE}/gracias-suscripcion/`, {
    waitUntil: 'domcontentloaded'
  });
  assert.ok(response?.ok(), 'La página de agradecimiento debe responder correctamente');

  const state = await page.evaluate(() => ({
    subscribed: localStorage.getItem('nl-subscribed'),
    popupTimestamp: localStorage.getItem('nl-popup-ts')
  }));

  assert.notEqual(
    state.subscribed,
    '1',
    'DEFECTO: una visita directa sin confirmación ha establecido nl-subscribed=1'
  );

  console.log('newsletter-direct-confirmation-state: PASS');
  await context.close();
} finally {
  await browser.close();
}
