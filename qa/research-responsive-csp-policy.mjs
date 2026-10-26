import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'https://davidportodiaz.com').replace(/\/$/, '');
const ROUTES = ['/', '/herramientas/', '/editoriales/', '/prensa.html'];
const WIDTHS = [320,768,1024,1440];
const browser = await chromium.launch({headless:true});

try {
  for (const width of WIDTHS) {
    for (const route of ROUTES) {
      const page = await browser.newPage({viewport:{width,height:900}});
      try {
        const response = await page.goto(BASE + route,{waitUntil:'domcontentloaded'});
        assert.equal(response?.status(),200,`${route} @ ${width}px: HTTP ${response?.status()}`);
        const policies = [response.headers()['content-security-policy'], ...(await page.locator('meta[http-equiv]').evaluateAll(nodes => nodes.filter(n => n.httpEquiv.toLowerCase() === 'content-security-policy').map(n => n.content)))].filter(Boolean);
        assert.ok(policies.length,`${route} @ ${width}px: falta CSP efectiva`);
        const directives = policies.join('; ').toLowerCase();
        for (const directive of ['script-src','object-src','base-uri']) {
          assert.ok(new RegExp('(?:^|;)\\s*' + directive + '\\s+').test(directives),`${route} @ ${width}px: falta ${directive}`);
        }
        assert.match(directives, /object-src\s+'none'/,`${route} @ ${width}px: object-src no está bloqueado`);
        assert.ok(!directives.includes("'unsafe-eval'"),`${route} @ ${width}px: unsafe-eval permitido`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}