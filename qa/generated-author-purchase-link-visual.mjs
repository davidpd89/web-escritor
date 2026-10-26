import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const routes=['/libros/','/las-manecillas-del-recuerdo/'];
try {
  for(const width of [320,360,390,768,1280]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    for(const route of routes) {
      const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`${route} ${width}px: HTTP incorrecto`);
      await page.evaluate(()=>document.fonts.ready);
      const link=page.locator('a.header-buy[href="https://amzn.to/4zW6Yeu"]');
      assert.equal(await link.count(),1,`${route} ${width}px: falta o se duplica el enlace principal de compra`);
      const data=await link.evaluate(el=>{
        const r=el.getBoundingClientRect();
        const s=getComputedStyle(el);
        return {href:el.href,target:el.target,rel:el.rel,name:el.getAttribute('aria-label')||el.textContent.trim(),display:s.display,visibility:s.visibility,width:r.width,height:r.height,left:r.left,right:r.right};
      });
      assert.equal(data.href,'https://amzn.to/4zW6Yeu',`${route}: destino de compra modificado`);
      assert.equal(data.target,'_blank',`${route}: apertura de compra inesperada`);
      for(const token of ['noopener','noreferrer']) assert.ok(data.rel.split(/\s+/).includes(token),`${route}: falta ${token}`);
      assert.ok(data.name.trim(),`${route}: enlace sin nombre accesible`);
      assert.notEqual(data.display,'none',`${route} ${width}px: enlace oculto`);
      assert.notEqual(data.visibility,'hidden',`${route} ${width}px: enlace invisible`);
      assert.ok(data.width>=24&&data.height>=24,`${route} ${width}px: área de compra insuficiente ${data.width}x${data.height}`);
      assert.ok(data.left>=-1&&data.right<=width+1,`${route} ${width}px: enlace de compra fuera del viewport ${JSON.stringify(data)}`);
    }
    await page.close();
  }
  console.log('generated-author-purchase-link-visual: OK');
} finally {await browser.close();}
