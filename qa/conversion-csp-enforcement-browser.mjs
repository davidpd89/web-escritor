import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = (process.env.QA_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const ROUTES = ['/', '/fragmento/', '/cuaderno/', '/las-manecillas-del-recuerdo/', '/privacidad.html'];
const browser = await chromium.launch();
try {
  for (const path of ROUTES) {
    const context = await browser.newContext({ serviceWorkers: 'block' });
    await context.route('**/*', route => new URL(route.request().url()).origin === ORIGIN ? route.continue() : route.abort());
    const page = await context.newPage();
    try {
      const response = await page.goto(ORIGIN + path, { waitUntil: 'domcontentloaded' });
      assert.ok(response?.ok(), `${path}: HTTP ${response?.status()}`);
      const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
      assert.ok(csp, `${path}: missing effective CSP meta element`);
      assert.match(csp, /(?:^|;)\s*object-src\s+'none'/, `${path}: object-src not restricted`);
      assert.match(csp, /(?:^|;)\s*base-uri\s+'self'/, `${path}: base-uri not restricted`);
      assert.match(csp, /(?:^|;)\s*form-action\s+'self'/, `${path}: form-action not restricted`);
      const result = await page.evaluate(async () => {
        window.__qaInlineExecuted = false;
        const violations = [];
        const listener = event => violations.push(event.violatedDirective);
        document.addEventListener('securitypolicyviolation', listener);
        const script = document.createElement('script');
        script.textContent = 'window.__qaInlineExecuted = true';
        document.body.appendChild(script);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        document.removeEventListener('securitypolicyviolation', listener);
        const executed = window.__qaInlineExecuted;
        script.remove();
        delete window.__qaInlineExecuted;
        return { executed, violations };
      });
      assert.equal(result.executed, false, `${path}: unauthorized inline script executed`);
      assert.ok(result.violations.some(value => value === 'script-src' || value === 'script-src-elem'), `${path}: browser did not report inline-script CSP enforcement`);
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('PASS: effective CSP on conversion routes');
