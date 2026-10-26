import test from 'node:test';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.BASE_URL||process.env.SITE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const IDS=['bluesky','mastodon','threads','instagram','tiktok','pinterest'];

async function structure(page){
  return page.evaluate(()=>({
    main:document.querySelectorAll('main:not([hidden])').length,
    h1:[...document.querySelectorAll('main h1')].map(x=>x.textContent.trim()),
    h2:[...document.querySelectorAll('main h2')].map(x=>({text:x.textContent.trim(),labelled:!!document.querySelector(`section[aria-labelledby="${x.id}"]`)})),
    cards:[...document.querySelectorAll('#social-grid .social-card')].map(x=>({id:x.dataset.network,heading:x.querySelector('h3')?.textContent.trim(),link:x.querySelector('h3 a')?.getAttribute('href')}))
  }));
}

test('redes-sociales: estructura semántica estable con 16 navegaciones simultáneas',async()=>{
  const browser=await chromium.launch();
  try{
    await Promise.all(Array.from({length:16},async(_,i)=>{
      const context=await browser.newContext();
      try{
        const page=await context.newPage();
        const response=await page.goto(BASE+'/redes-sociales/',{waitUntil:'domcontentloaded'});
        assert.equal(response.status(),200,`/redes-sociales/: sesión ${i}`);
        const initial=await structure(page);
        assert.equal(initial.main,1,`/redes-sociales/: sesión ${i} main`);
        assert.equal(initial.h1.length,1,`/redes-sociales/: sesión ${i} H1`);
        assert.ok(initial.h1[0],`/redes-sociales/: sesión ${i} H1 vacío`);
        assert.ok(initial.h2.some(x=>x.text==='Seguidores por red'&&x.labelled),`/redes-sociales/: sesión ${i} sección sin encabezado asociado`);
        assert.deepEqual(initial.cards.map(x=>x.id),IDS,`/redes-sociales/: sesión ${i} perfiles`);
        for(const card of initial.cards){
          assert.ok(card.heading&&card.link,`/redes-sociales/: ${card.id} sin H3 o enlace`);
        }
        await page.waitForLoadState('load');
        const final=await structure(page);
        assert.deepEqual(final,initial,`/redes-sociales/: sesión ${i} estructura modificada`);
      }finally{await context.close();}
    }));
  }finally{await browser.close();}
});