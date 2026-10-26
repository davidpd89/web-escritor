import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });

try {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    reducedMotion: 'reduce'
  });
  const page = await context.newPage();

  await page.goto(`${BASE}/las-manecillas-del-recuerdo/kindle/`, {
    waitUntil: 'domcontentloaded'
  });

  const banner = page.locator('[data-analytics-consent-banner]');
  await banner.waitFor({ state: 'visible' });

  const readConsent = () => page.evaluate(() =>
    localStorage.getItem('dp-analytics-consent')
  );

  assert.equal(await readConsent(), null, 'No debe existir consentimiento inicial');

  await page.mouse.wheel(0, 400);
  await page.evaluate(() => new Promise(resolve =>
    requestAnimationFrame(() => requestAnimationFrame(resolve))
  ));

  assert.equal(
    await readConsent(),
    null,
    'DEFECTO: desplazarse por la página se interpreta como consentimiento analítico'
  );

  assert.equal(
    await banner.count(),
    1,
    'El banner debe seguir disponible hasta que exista una decisión explícita'
  );

  await page.getByRole('button', { name: 'Rechazo ayudarte' }).click();
  const stored = JSON.parse(await readConsent());
  assert.equal(stored.value, 'denied');

  await context.close();
  console.log('analytics-explicit-consent-browser: PASS');
} finally {
  await browser.close();
}
