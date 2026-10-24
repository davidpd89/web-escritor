import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const routes = ['/las-manecillas-del-recuerdo/', '/las-manecillas-del-recuerdo/kindle/', '/las-manecillas-del-recuerdo/fragmentos/'];
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext();
  await context.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.abort());
  const page = await context.newPage();
  for (const route of routes) {
    await page.goto(origin + route);
    const nav = page.locator('nav.section-context[data-editorial-context-nav="manecillas"]');
    assert.equal(await nav.count(), 1, `${route}: navegación contextual duplicada`);
    const active = nav.locator('a[aria-current="page"]');
    assert.equal(await active.count(), 1, `${route}: número incorrecto de enlaces activos`);
    const href = await active.getAttribute('href');
    assert.equal(new URL(href, origin).pathname, route);
    const links = await nav.locator('a[href]').evaluateAll(elements => elements.map(e => e.getAttribute('href')));
    for (const expected of routes) assert(links.includes(expected), `${route}: enlace contextual ausente ${expected}`);
  }
  await context.close();
  console.log('manecillas-context-active-route: OK');
} finally {
  await browser.close();
}
