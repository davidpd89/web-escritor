import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext();
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  for (const route of ['', 'kindle/', 'fragmentos/']) {
    await page.goto(`${origin}/las-manecillas-del-recuerdo/${route}`);
    const regions = await page.evaluate(() => [...document.querySelectorAll('main section[aria-labelledby]')].map(section => {
      const ids = section.getAttribute('aria-labelledby').trim().split(/\s+/);
      return { id: section.id, targets: ids.map(id => {
        const title = document.getElementById(id);
        const style = title ? getComputedStyle(title) : null;
        return {
          exists: !!title,
          heading: !!title && /^H[1-6]$/.test(title.tagName),
          owned: !!title && section.contains(title),
          named: !!title && !!title.textContent.trim(),
          visible: !!style && style.display !== 'none' && style.visibility !== 'hidden',
          hidden: title?.getAttribute('aria-hidden') === 'true'
        };
      }) };
    }));
    assert(regions.length >= 3, `${route}: regiones insuficientes`);
    for (const region of regions) {
      for (const target of region.targets) {
        assert(target.exists && target.heading && target.owned && target.named && target.visible && !target.hidden, `${route}: región ${region.id} sin encabezado semántico válido`);
      }
    }
  }
  await context.close();
  console.log('manecillas-region-heading-association: OK');
} finally {
  await browser.close();
}
