import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const paths = ['/editoriales/', '/editoriales/minotauro/'];
const browser = await chromium.launch({headless:true});

async function metadata(page) {
  return page.evaluate(() => ({
    title: document.title.trim(),
    description: document.querySelector('meta[name="description"]')?.content.trim(),
    canonical: document.querySelector('link[rel="canonical"]')?.href,
    robots: document.querySelector('meta[name="robots"]')?.content
  }));
}

try {
  for (const width of [375, 768, 1440]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    for (const path of paths) {
      const page = await context.newPage();
      const response = await page.goto(BASE + path, {waitUntil:'load'});
      assert.equal(response.status(), 200, `${path}: HTTP ${response.status()}`);
      const initial = await metadata(page);
      await page.locator('h1').first().waitFor({state:'visible'});
      await page.evaluate(() => document.fonts.ready);
      const final = await metadata(page);
      assert.deepEqual(final, initial, `${path} ${width}px: metadatos alterados tras renderizar`);
      assert.ok(final.title && final.description && final.canonical, `${path}: metadatos SEO incompletos`);
      const heading = await page.locator('h1').first().evaluate(el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return {x:r.x,right:r.right,width:r.width,height:r.height,font:parseFloat(s.fontSize),visibility:s.visibility};
      });
      assert.ok(heading.width > 0 && heading.height > 0 && heading.font >= 16 && heading.x >= -1 && heading.right <= width + 1 && heading.visibility === 'visible', `${path} ${width}px: H1 fuera de pantalla o ilegible: ${JSON.stringify(heading)}`);
      await page.close();
    }
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('OK: identidad SEO editorial estable en tres resoluciones');