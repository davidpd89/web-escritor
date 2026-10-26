import test from 'node:test';
import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.BASE_URL||process.env.SITE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const IDS=['bluesky','mastodon','threads','instagram','tiktok','pinterest'];

async function withBrowser(fn){
  const browser=await chromium.launch({headless:true});
  try{await fn(browser);}finally{await browser.close();}
}

async function load(browser){
  const context=await browser.newContext();
  const page=await context.newPage();
  const responses=[];
  page.on('response',r=>{if(new URL(r.url()).origin===new URL(BASE).origin)responses.push({url:r.url(),status:r.status()});});
  const response=await page.goto(BASE+'/redes-sociales/',{waitUntil:'domcontentloaded'});
  assert.equal(response.status(),200,'/redes-sociales/: respuesta HTML');
  await page.locator('#social-grid .social-card').first().waitFor();
  return {context,page,responses};
}

test('redes-sociales: navegación Tab con 12 páginas concurrentes',async()=>withBrowser(async browser=>{
  const sessions=await Promise.all(Array.from({length:12},()=>load(browser)));
  try{
    for(const {page,responses} of sessions){
      const links=page.locator('#social-grid .social-card h3 a');
      assert.equal(await links.count(),IDS.length,'/redes-sociales/: seis enlaces');
      assert.deepEqual(await page.locator('#social-grid .social-card').evaluateAll(nodes=>nodes.map(n=>n.dataset.network)),IDS,'/redes-sociales/: orden de perfiles');
      await page.keyboard.press('Tab');
      let found=[];
      for(let i=0;i<35;i++){
        const id=await page.evaluate(()=>document.activeElement?.closest('[data-network]')?.dataset.network||null);
        if(id&&!found.includes(id))found.push(id);
        if(found.length===IDS.length)break;
        await page.keyboard.press('Tab');
      }
      assert.deepEqual(found,IDS,'/redes-sociales/: secuencia de foco');
      assert.ok(responses.every(r=>r.status>=200&&r.status<400),'/redes-sociales/: recursos locales sin error HTTP');
    }
  }finally{await Promise.all(sessions.map(s=>s.context.close()));}
}));