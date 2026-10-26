import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

try {
  for (const route of ['/editoriales/suma-de-letras/', '/mapa-del-sitio/']) {
    for (const width of [320, 360, 390]) {
      const context = await browser.newContext({ viewport: { width, height: 800 }, isMobile: true, hasTouch: true });
      const page = await context.newPage();
      const response = await page.goto(new URL(route, BASE).href, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${route} ${width}px: página no disponible`);
      const policies = [response.headers()['content-security-policy'], ...await page.locator('meta[http-equiv="Content-Security-Policy" i]').evaluateAll(nodes => nodes.map(n => n.content))].filter(Boolean);
      assert.ok(policies.length, `${route} ${width}px: falta CSP`);
      const directives = Object.fromEntries(policies.join(';').split(';').map(x => x.trim().split(/\s+/)).filter(x => x.length > 1).map(([key, ...values]) => [key.toLowerCase(), values]));
      assert.ok(directives['object-src']?.includes("'none'"), `${route} ${width}px: object-src no prohíbe objetos activos`);
      assert.ok(directives['base-uri']?.includes("'self'") || directives['base-uri']?.includes("'none'"), `${route} ${width}px: base-uri sin restricción`);
      assert.ok(directives['script-src']?.includes("'self'"), `${route} ${width}px: scripts no restringidos al origen`);
      assert.ok(!directives['script-src'].includes("'unsafe-eval'") && !directives['script-src'].includes('*'), `${route} ${width}px: script-src permisiva`);
      const trigger = page.locator('[data-explore-open]');
      await trigger.click();
      await assert.doesNotReject(() => page.locator('[data-explore-dialog]').waitFor({ state: 'visible', timeout: 5000 }), `${route} ${width}px: la CSP o el JS impiden abrir el menú`);
      await page.locator('[data-explore-close]').click();
      await page.locator('[data-explore-dialog]').waitFor({ state: 'hidden' });
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS postmerge mobile generated CSP');
