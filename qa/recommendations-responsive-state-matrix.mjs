import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE = process.env.RECOMMENDATIONS_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch();
try {
 const page = await browser.newPage({viewport:{width:1440,height:900}});
 await page.route(/^https?:\/\//, route => new URL(route.request().url()).origin === new URL(BASE).origin ? route.continue() : route.abort());
 await page.goto(BASE+'/recomendaciones/');
 const q=page.locator('[data-filter="q"]');
 assert.equal(await q.count(),1);
 const first=await page.locator('[data-catalogue-book]').first().getAttribute('data-title');
 assert.ok(first);
 await q.fill(first);
 const snapshot=()=>page.evaluate(()=>({q:document.querySelector('[data-filter="q"]').value,ids:[...document.querySelectorAll('[data-catalogue-book]')].filter(x=>!x.hidden).map(x=>x.dataset.bookId),hash:location.hash}));
 const initial=await snapshot();
 assert.ok(initial.ids.length>0);
 for(const [width,height] of [[390,844],[320,568],[768,1024],[1440,900]]){
  await page.setViewportSize({width,height});
  assert.deepEqual(await snapshot(),initial,`Estado alterado en ${width}x${height}`);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 }
 await page.close();
 console.log('PASS responsive state matrix');
}finally{await browser.close();}