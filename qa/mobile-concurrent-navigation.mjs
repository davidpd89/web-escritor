import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/asistente/', '/editoriales/', '/convocatorias-escritores/'];
const widths = [320, 360, 390];
const browser = await chromium.launch({ headless: true });

try {
  await Promise.all(routes.flatMap(route => widths.map(async width => {
    const context = await browser.newContext({ viewport: { width, height: 780 } });
    try {
      const page = await context.newPage();
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.ok(response?.ok(), `${route} ${width}px: HTTP ${response?.status()}`);
      assert.ok((await page.title()).trim(), `${route} ${width}px: título vacío`);
      const trigger = page.locator('[data-explore-open]');
      await trigger.waitFor({ state: 'visible' });
      await trigger.click();
      const dialog = page.locator('#explore-dialog');
      await dialog.waitFor({ state: 'visible' });
      assert.ok(await dialog.locator('a[href]').count() > 0, `${route} ${width}px: menú sin enlaces`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 2, `${route} ${width}px: desbordamiento horizontal ${overflow}px`);
    } finally {
      await context.close();
    }
  })));
  console.log('PASS: navegación móvil concurrente');
} finally {
  await browser.close();
}