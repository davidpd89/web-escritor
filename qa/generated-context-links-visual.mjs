import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
let total=0;
try {
  for(const width of [320,360,390,768,1024,1440]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    for(const route of ['/recomendaciones/','/libros/']) {
      const response=await page.goto(BASE+route,{waitUntil:'domcontentloaded'});
      assert.equal(response?.status(),200,`${route} ${width}px: HTTP incorrecto`);
      await page.evaluate(()=>document.fonts.ready);
      const links=page.locator('nav.section-context a');
      const count=await links.count();
      assert.ok(count>0,`${route} ${width}px: falta navegación contextual`);
      for(let i=0;i<count;i++) {
        const link=links.nth(i);
        const data=await link.evaluate(el=>{
          const r=el.getBoundingClientRect();
          const s=getComputedStyle(el);
          const visible=s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
          return {href:el.getAttribute('href'),name:el.getAttribute('aria-label')||el.textContent.trim(),visible,width:r.width,height:r.height,left:r.left,right:r.right,viewport:innerWidth};
        });
        if(!data.visible) continue;
        assert.ok(data.name.trim(),`${route} ${width}px: enlace ${data.href} sin nombre`);
        assert.ok(data.left>=-1&&data.right<=width+1,`${route} ${width}px: enlace ${data.href} sobresale horizontalmente: ${JSON.stringify(data)}`);
        assert.ok(data.width>=1&&data.height>=1,`${route} ${width}px: caja inválida de ${data.href}`);
        total++;
      }
    }
    await page.close();
  }
  assert.ok(total>0,'No se inspeccionaron enlaces contextuales visibles');
  console.log(`generated-context-links-visual: OK (${total} enlaces)`);
} finally {await browser.close();}
