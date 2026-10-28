import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/convocatorias-escritores/', '/editoriales/'];
const browser = await chromium.launch({ headless: true });

try {
  await Promise.all(routes.flatMap(route => [320, 360, 390].flatMap(width => [0, 1].map(async repetition => {
    const context = await browser.newContext({ viewport: { width, height: 780 } });
    try {
      const page = await context.newPage();
      const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      assert.ok(response?.ok(), `${route} ${width}px intento ${repetition}: HTTP ${response?.status()}`);
      const heading = page.locator('main h1').first();
      await heading.waitFor({ state: 'visible' });
      assert.ok((await heading.innerText()).trim(), `${route} ${width}px: H1 vacío`);
      const mainText = await page.locator('main').first().innerText();
      assert.ok(mainText.trim().length > 100, `${route} ${width}px: contenido principal incompleto (${mainText.length} caracteres)`);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
      assert.ok(overflow <= 2, `${route} ${width}px: desbordamiento horizontal ${overflow}px`);
      const rect = await heading.evaluate(el => { const r = el.getBoundingClientRect(); return { left: r.left, right: r.right, width: r.width }; });
      assert.ok(rect.width > 0 && rect.right > 0 && rect.left < width, `${route} ${width}px: encabezado fuera de pantalla ${JSON.stringify(rect)}`);
    } finally {
      await context.close();
    }
  }))));
  console.log('PASS: herramientas editoriales móviles concurrentes');
} finally {
  await browser.close();
}