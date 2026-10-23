import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const O=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try{
  for(const width of [320,390,768,1280]){
    const context=await browser.newContext({javaScriptEnabled:false,viewport:{width,height:844}});
    await context.route('**/*',r=>r.request().url().startsWith(O+'/')?r.continue():r.abort());
    const page=await context.newPage();
    const response=await page.goto(O+'/offline.html',{waitUntil:'load'});
    assert.equal(response?.status(),200);
    const state=await page.evaluate(()=>({h1:document.querySelector('h1')?.innerText,status:document.querySelector('[role=status]')?.innerText,buttons:[...document.querySelectorAll('.actions button')].filter(b=>b.getClientRects().length&&getComputedStyle(b).visibility!=='hidden').length,overflow:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth,robots:document.querySelector('meta[name=robots]')?.content}));
    assert.ok(state.h1?.length>15,width+': título inaccesible');
    assert.ok(state.status?.length>15,width+': sin explicación de estado');
    assert.equal(state.buttons,0,width+': botones JS inertes visibles');
    assert.ok(state.overflow<=1,width+': overflow horizontal '+state.overflow);
    assert.match(state.robots||'',/noindex/);
    await context.close();
  }
}finally{await browser.close();}
console.log('PASS nojs offline shell accessibility');