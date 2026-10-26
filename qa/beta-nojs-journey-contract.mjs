import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.QA_BASE_URL || process.env.BASE_URL;
assert.ok(base, 'Configura QA_BASE_URL con el servidor local');
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
const context = await browser.newContext({javaScriptEnabled:false});
try {
  const page = await context.newPage();
  const routes = ['/lectores-beta/', '/lectores-beta/enviar-manuscrito/'];
  for (const route of routes) {
    const response = await page.goto(new URL(route,base).href,{waitUntil:'load'});
    assert.equal(response.status(),200,`${route}: HTTP ${response.status()}`);
    assert.equal(await page.locator('main h1:visible').count(),1,`${route}: falta H1 visible`);
    const text = await page.locator('main').innerText();
    assert.ok(text.trim().length > 300,`${route}: contenido insuficiente sin JS (${text.length})`);
    const target = routes.find(r=>r!==route);
    const links = page.locator(`main a[href='${target}']:visible`);
    assert.ok(await links.count()>0,`${route}: no hay enlace visible a ${target}`);
    await links.first().click();
    await page.waitForURL(url=>url.pathname===target);
    assert.equal(new URL(page.url()).pathname,target,`${route}: navegación fallida a ${target}`);
  }
  console.log('beta-nojs-journey-contract: OK');
} finally {await context.close();await browser.close();}