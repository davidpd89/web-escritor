import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'https://davidportodiaz.com').replace(/\/$/, '');
const ROUTES = ['/', '/herramientas/', '/editoriales/', '/prensa.html'];
const WIDTHS = [320, 768, 1024, 1440];
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  for (const width of WIDTHS) {
    for (const route of ROUTES) {
      const page = await browser.newPage({viewport:{width,height:900}});
      const violations = [];
      page.on('request', request => {
        const url = request.url();
        if (/^http:\/\//i.test(url) && new URL(BASE).protocol === 'https:') {
          violations.push(`${request.resourceType()}: ${url}`);
        }
      });
      page.on('console', message => {
        if (message.type() === 'error' && /mixed content/i.test(message.text())) {
          violations.push(message.text());
        }
      });
      try {
        const response = await page.goto(BASE + route, {waitUntil:'load',timeout:30000});
        assert.equal(response?.status(), 200, `${route} @ ${width}px: HTTP ${response?.status()}`);
        assert.deepEqual(violations, [], `${route} @ ${width}px: recursos mixtos detectados: ${violations.join('; ')}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}