import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const ROUTE = '/recursos/ficha-historia-objeto-heredado/';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  const context = await browser.newContext({javaScriptEnabled:false});
  const page = await context.newPage();
  const response = await page.goto(BASE + ROUTE, {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(), `${ROUTE}: respuesta HTTP incorrecta`);
  const selectors = ['[data-record-export]','[data-record-open]','[data-record-print]','[data-record-clear]','[data-add-row]'];
  const result = await page.evaluate((selectors) => {
    const explanation = [...document.querySelectorAll('noscript')].some(el => el.textContent.trim().length > 0);
    return selectors.flatMap(selector => [...document.querySelectorAll(selector)].filter(el => {
      const style = getComputedStyle(el);
      const visible = style.display !== 'none' && style.visibility !== 'hidden' && el.getClientRects().length > 0;
      if (!visible || el.disabled || el.getAttribute('aria-disabled') === 'true') return false;
      if (el.matches('a[href]')) return false;
      if (el.matches('button[type=submit]') && el.form?.action) return false;
      return !explanation;
    }).map(el => ({selector,text:el.textContent.trim()})));
  }, selectors);
  assert.deepEqual(result, [], `${ROUTE}: acciones sin JavaScript ni alternativa: ${JSON.stringify(result)}`);
  console.log('OK recursos-nojs-action-affordances');
} finally {
  await browser.close();
}
