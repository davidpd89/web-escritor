import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createServer } from 'node:http';
import { chromium } from 'playwright';

const root=process.cwd();
const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.woff2':'font/woff2'};
const server=createServer((req,res)=>{
  const rel=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname).replace(/^\/+/, '');
  const file=path.resolve(root,rel.endsWith('/')||!rel?`${rel}index.html`:rel);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
  res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'}).end(fs.readFileSync(file));
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const base=`http://127.0.0.1:${server.address().port}`;
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
async function visit(viewport={width:1280,height:800}) {
  const context=await browser.newContext({viewport,serviceWorkers:'block'});
  await context.route('**/*',r=>new URL(r.request().url()).origin===base?r.continue():r.abort());
  const page=await context.newPage();
  await page.goto(base+'/lectores-beta/',{waitUntil:'load'});
  return {context,page};
}
try {
  // 1. Abrir privacidad dentro del label NO equivale a aceptar el consentimiento.
  {
    const {context,page}=await visit();
    const check=page.locator('#lectores-beta-gdpr');
    const privacy=page.locator('label[for="lectores-beta-gdpr"] a[href="/privacidad.html"]');
    assert.equal(await check.isChecked(),false);
    const popupPromise=page.waitForEvent('popup');
    await privacy.click();
    const popup=await popupPromise;
    await popup.waitForLoadState('domcontentloaded');
    assert.equal(new URL(popup.url()).pathname,'/privacidad.html');
    assert.equal(await check.isChecked(),false,'abrir la política marcó consentimiento sin permiso');
    await popup.close();await context.close();
  }
  // 2. Hit-testing en móvil real: enlaces y controles no quedan tapados o solapados.
  for(const width of [320,375,390]) {
    const {context,page}=await visit({width,height:640});
    for(const selector of ['#lectores-beta-email','#lectores-beta-form button[type=submit]','label[for="lectores-beta-gdpr"]','label[for="lectores-beta-gdpr"] a']) {
      const loc=page.locator(selector);
      await loc.scrollIntoViewIfNeeded();
      const g=await loc.evaluate(e=>{
        const r=e.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;
        const hit=document.elementFromPoint(x,y);
        return {width:r.width,height:r.height,hit:hit===e||e.contains(hit),viewport:innerWidth,docWidth:document.documentElement.scrollWidth};
      });
      assert.ok(g.width>=24 && g.height>=16,`${width} ${selector}: objetivo minúsculo`);
      assert.ok(g.hit,`${width} ${selector}: un elemento intercepta su centro`);
      assert.ok(g.docWidth<=g.viewport+1,`${width}: overflow horizontal`);
    }
    await context.close();
  }
  // 3. El formulario global Explorar y el privado beta tienen estado y source aislados.
  {
    const {context,page}=await visit();
    const sources=[];
    await page.route('https://subscribe.davidpd89.workers.dev/**',r=>{
      sources.push(r.request().postDataJSON().source);
      return r.fulfill({status:201,contentType:'application/json',body:'{"ok":true,"state":"pending_confirmation"}'});
    });
    await page.locator('[data-explore-open]').click();
    await page.locator('#nl-email-explore').fill('general@example.test');
    await page.locator('#newsletter-form-explore button[type=submit]').click();
    await page.waitForFunction(()=>!document.querySelector('#nl-email-explore'));
    assert.equal(await page.locator('#lectores-beta-gdpr').isChecked(),false);
    assert.equal(await page.locator('#lectores-beta-email').count(),1);
    await page.locator('[data-explore-close]').click();
    await page.locator('#lectores-beta-email').fill('beta@example.test');
    await page.locator('#lectores-beta-gdpr').check();
    await page.locator('#lectores-beta-form button[type=submit]').click();
    await page.waitForFunction(()=>!document.querySelector('#lectores-beta-email'));
    assert.deepEqual(sources,['explore','lectores-beta']);
    await context.close();
  }
} finally {await browser.close();await new Promise(r=>server.close(r));}
console.log('PASS beta consent: nested link, touch targets, global/private isolation');
