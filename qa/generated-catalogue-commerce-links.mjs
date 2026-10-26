import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
let inspected=0;
try {
  const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const response=await page.goto(BASE+'/recomendaciones/',{waitUntil:'domcontentloaded'});
  assert.equal(response?.status(),200,'/recomendaciones/: HTTP incorrecto');
  await page.evaluate(()=>document.fonts.ready);
  const links=await page.locator('main a[href]').evaluateAll(nodes=>nodes.map(a=>{
    const r=a.getBoundingClientRect();
    const s=getComputedStyle(a);
    return {href:a.href,raw:a.getAttribute('href'),target:a.target,rel:a.rel,name:a.getAttribute('aria-label')||a.textContent.trim()||a.querySelector('img')?.getAttribute('alt')||'',visible:s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
  }));
  const commercial=links.filter(x=>x.visible&&/^https:\/\//i.test(x.href)&&/(?:amazon\.[a-z.]+|amzn\.to)/i.test(new URL(x.href).hostname));
  for(const link of commercial) {
    const url=new URL(link.href);
    assert.equal(url.protocol,'https:',`/recomendaciones/: enlace comercial inseguro ${link.href}`);
    assert.ok(link.name.trim(),`/recomendaciones/: enlace comercial sin nombre ${link.href}`);
    if(link.target==='_blank') {
      const tokens=link.rel.toLowerCase().split(/\s+/);
      for(const required of ['noopener','noreferrer']) assert.ok(tokens.includes(required),`/recomendaciones/: falta ${required} en ${link.href}`);
    }
    if(url.searchParams.has('tag')) assert.ok(url.searchParams.get('tag')?.trim(),`/recomendaciones/: tag Amazon vacío en ${link.href}`);
    inspected++;
  }
  assert.ok(inspected>0,'/recomendaciones/: no se encontraron enlaces comerciales visibles; revisar selector o generación');
  console.log(`generated-catalogue-commerce-links: OK (${inspected} enlaces)`);
} finally {await browser.close();}
