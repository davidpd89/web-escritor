import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
try{
  const context=await browser.newContext({javaScriptEnabled:false});
  await context.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/,r=>r.abort());
  const page=await context.newPage();
  await page.goto(BASE+'/cuaderno/');
  const surprise=page.locator('a[data-surprise-me]');
  assert.equal(await surprise.count(),1,'falta Sorpréndeme');
  assert.equal(await surprise.getAttribute('href'),'/mapa-del-sitio/','fallback incorrecto');
  const routes=await page.locator('.cuaderno-feature h2 a,.cuaderno-ledger h3 a,.cuaderno-archive a[href^="/cuaderno/temas/"]').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.getAttribute('href')))]);
  assert.ok(routes.length>=3,'recorrido editorial insuficiente');
  for(const route of routes){
    await page.goto(BASE+'/cuaderno/');
    const link=page.locator('main a').filter({has:page.locator('span.__never__')});
    void link;
    const target=page.locator(`main a[href="${route}"]`).first();
    assert.ok(await target.isVisible(),`enlace oculto: ${route}`);
    await Promise.all([page.waitForURL(url=>url.pathname===new URL(route,BASE).pathname),target.click()]);
    assert.equal(new URL(page.url()).pathname,new URL(route,BASE).pathname);
    assert.equal(await page.locator('main h1').count(),1,`destino sin H1: ${route}`);
  }
  await page.goto(BASE+'/cuaderno/');
  await surprise.click();
  assert.equal(new URL(page.url()).pathname,'/mapa-del-sitio/');
  await context.close();
  console.log('PASS cuaderno no-JS journey');
}finally{await browser.close();}
