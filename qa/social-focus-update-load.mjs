import test from 'node:test';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.BASE_URL||process.env.SITE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const IDS=['bluesky','mastodon','threads','instagram','tiktok','pinterest'];

test('redes-sociales: el foco sobre perfiles sobrevive a la actualización de métricas',async()=>{
  const browser=await chromium.launch();
  try{
    const jobs=IDS.map(async id=>{
      const context=await browser.newContext();
      try{
        const page=await context.newPage();
        let release;
        const gate=new Promise(resolve=>release=resolve);
        let requested;
        const started=new Promise(resolve=>requested=resolve);
        await page.route('**/redes-sociales/social-metrics.json',async route=>{
          requested();
          await gate;
          await route.continue();
        });
        const response=await page.goto(BASE+'/redes-sociales/',{waitUntil:'domcontentloaded'});
        assert.equal(response.status(),200,`/redes-sociales/: ${id} HTML`);
        const link=page.locator(`[data-network="${id}"] h3 a`);
        await link.focus();
        const before=await link.getAttribute('href');
        try{
          await started;
        }finally{release();}
        await page.waitForResponse(r=>r.url().includes('/redes-sociales/social-metrics.json'));
        await page.waitForFunction(id=>{
          const card=document.querySelector(`[data-network="${id}"]`);
          return card&&card.querySelector('[data-role="count"]').textContent.trim()!=='Dato no disponible';
        },id).catch(async()=>{
          await page.waitForFunction(id=>document.querySelector(`[data-network="${id}"] [data-role="meta"]`)?.textContent.trim()==='Sin medición vigente.',id);
        });
        assert.equal(await page.evaluate(()=>document.activeElement?.closest('[data-network]')?.dataset.network),id,`/redes-sociales/: ${id} pierde foco`);
        assert.equal(await link.getAttribute('href'),before,`/redes-sociales/: ${id} cambia destino`);
        assert.match((await link.innerText()).trim(),/\S/,`/redes-sociales/: ${id} sin nombre`);
      }finally{await context.close();}
    });
    await Promise.all(jobs);
  }finally{await browser.close();}
});