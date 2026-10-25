import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.RECOMMENDATIONS_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch();
try{
 const page=await browser.newPage({viewport:{width:320,height:700}});
 await page.route(/^https?:\/\//,r=>new URL(r.request().url()).origin===new URL(BASE).origin?r.continue():r.abort());
 await page.goto(BASE+'/recomendaciones/');
 await page.addStyleTag({content:'html{font-size:200%!important}'});
 const controls=page.locator('[data-catalogue-filters] input:visible, [data-catalogue-filters] select:visible, [data-catalogue-filters] button:visible');
 assert.ok(await controls.count()>0);
 for(let i=0;i<await controls.count();i++){
  const el=controls.nth(i);
  if(await el.isDisabled())continue;
  await el.scrollIntoViewIfNeeded();
  const state=await el.evaluate(node=>{const r=node.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;const top=document.elementFromPoint(x,y);return {left:r.left,right:r.right,hit:!!top&&(node===top||node.contains(top)||top.contains(node))};});
  assert.ok(state.left>=-1&&state.right<=321,`Control fuera de ancho: ${i}`);
  assert.ok(state.hit,`Control interceptado: ${i}`);
 }
 console.log('PASS text zoom hit testing');
}finally{await browser.close();}