import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';

const html = readFileSync('offline.html', 'utf8');
const browser = await chromium.launch({headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of [320, 390, 1280]) {
    const context = await browser.newContext({javaScriptEnabled: false, viewport: {width, height: 800}});
    const page = await context.newPage();
    await page.setContent(html);
    const state = await page.evaluate(() => {
      const visible = el => {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
      };
      return {
        h1: visible(document.querySelector('h1')),
        lead: visible(document.querySelector('.lead')),
        status: visible(document.querySelector('[role="status"]')),
        actions: visible(document.querySelector('.actions')),
        overflow: document.documentElement.scrollWidth > innerWidth + 1
      };
    });
    assert(state.h1 && state.lead && state.status, `${width}: offline explanation missing`);
    assert(!state.actions, `${width}: unusable JS-only controls displayed`);
    assert(!state.overflow, `${width}: horizontal overflow`);
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS offline without JavaScript');
