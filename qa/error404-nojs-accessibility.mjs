import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const html = readFileSync('404.html', 'utf8');
const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [320, 390, 1280]) {
    const context = await browser.newContext({javaScriptEnabled: false, viewport: {width, height: 850}});
    const page = await context.newPage();
    await page.setContent(html);
    const state = await page.evaluate(() => ({
      title: document.title.trim(),
      headings: [...document.querySelectorAll('h1')].map(e => e.textContent.trim()),
      main: document.querySelector('main')?.textContent.trim() || '',
      robots: document.querySelector('meta[name="robots"]')?.content || '',
      skip: document.querySelector('a.skip-link')?.getAttribute('href'),
      skipTarget: !!document.querySelector('#contenido'),
      navigation: [...document.querySelectorAll('nav a[href]')].filter(a => {
        const r = a.getBoundingClientRect();
        const s = getComputedStyle(a);
        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
      }).length,
      overflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > innerWidth + 1
    }));
    assert(state.title, `${width}: title missing`);
    assert.equal(state.headings.length, 1, `${width}: expected one H1`);
    assert(state.main.length > 100, `${width}: main content missing`);
    assert(/noindex/i.test(state.robots), `${width}: 404 is indexable`);
    assert.equal(state.skip, '#contenido');
    assert(state.skipTarget, `${width}: skip target missing`);
    assert(state.navigation > 0, `${width}: navigation unavailable`);
    assert(!state.overflow, `${width}: horizontal overflow`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS 404 no-JS accessibility');
