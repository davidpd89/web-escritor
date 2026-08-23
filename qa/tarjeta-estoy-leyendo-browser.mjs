import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const URL = `${ORIGIN}/herramientas/tarjeta-estoy-leyendo/`;

async function generate(page, { reference = false, hostile = false } = {}) {
  await page.locator('#reading-card-label').selectOption('leyendo');
  await page.locator('#reading-card-title').fill(hostile ? '<script>window.__xss=1</script>' : 'La casa del reloj');
  await page.locator('#reading-card-author').fill(hostile ? '<img src=x onerror=window.__xss=2>' : 'Ana Ejemplo');
  if (reference) await page.locator('#reading-card-reference').check();
  await page.locator('[data-reading-card-form] button[type="submit"]').click();
  await page.locator('[data-reading-card-results]').waitFor({ state: 'visible' });
}

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const viewport of [{ width: 320, height: 700 }, { width: 1280, height: 900 }]) {
    const context = await browser.newContext({ viewport });
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: async (value) => { window.__copied = value; } },
      });
    });
    const page = await context.newPage();
    const external = [];
    page.on('request', (req) => {
      if (!req.url().startsWith(ORIGIN) && !req.url().startsWith('data:') && !req.url().startsWith('blob:')) external.push(req.url());
    });
    await page.goto(URL, { waitUntil: 'networkidle' });

    const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
    assert(csp?.includes("connect-src 'none'"));
    assert.equal(await page.locator('#reading-card-reference').isChecked(), false, 'reference must be opt-in');
    await generate(page, { hostile: true });

    const html = await page.locator('[data-reading-card-html]').inputValue();
    assert(html.includes('&lt;script&gt;'));
    assert(!html.includes('<script'));
    assert(!html.includes('onerror='));
    assert(!html.includes('davidportodiaz.com/herramientas/tarjeta-estoy-leyendo/'));
    assert.equal(await page.evaluate(() => window.__xss), undefined);
    assert((await page.locator('[data-reading-card-preview]').textContent()).includes('<script>window.__xss=1</script>'));

    await page.locator('[data-copy-target="#reading-card-html"]').click();
    assert.equal(await page.evaluate(() => window.__copied), html, 'Clipboard API must receive the generated HTML');
    assert((await page.locator('[data-reading-card-status]').textContent()).includes('copiado'));

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert(overflow <= 1, `horizontal overflow at ${viewport.width}px: ${overflow}`);
    assert.deepEqual(external, [], `unexpected external requests: ${external.join(', ')}`);
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    await page.goto(URL, { waitUntil: 'load' });
    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
      document.execCommand = () => false;
    });
    await generate(page);
    const output = page.locator('[data-reading-card-html]');
    await page.locator('[data-copy-target="#reading-card-html"]').click();
    assert.equal(await output.evaluate((el) => document.activeElement === el), true, 'fallback must focus output');
    assert((await page.locator('[data-reading-card-status]').textContent()).includes('seleccionado'));

    await page.locator('#reading-card-reference').check();
    await page.locator('[data-reading-card-form] button[type="submit"]').click();
    const withReference = await output.inputValue();
    assert(withReference.includes('https://davidportodiaz.com/herramientas/tarjeta-estoy-leyendo/'));
  }

  console.log('tarjeta-estoy-leyendo-browser: PASS');
} finally {
  await browser.close();
}
