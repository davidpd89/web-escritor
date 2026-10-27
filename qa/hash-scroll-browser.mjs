import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {pathToFileURL} from 'node:url';
import {waitForKeyboardFocusState} from './keyboard-focus-state.mjs';

export async function assertInitialHashNavigation(browser, origin){
const fixture='<!doctype html><html class="v1"><head><style>body{margin:0;overflow-anchor:none}a,button{display:block}main{min-height:5000px;display:flow-root}#reading{margin-top:3000px}#destination{margin-top:1000px}</style><script defer src="/assets/analytics-consent-banner.js?v=16"></script><script defer src="/script.js"></script></head><body><a href="#contenido" class="skip-link">Ir al contenido</a><main id="contenido" tabindex="-1"><button id="reading">Seguir leyendo</button><div id="destination" tabindex="-1">Destino inicial</div></main></body></html>';
 for(const hash of ['', '#contenido']){
  const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
  await context.route('**/qa-hash-scroll/',r=>r.fulfill({contentType:'text/html',body:fixture}));
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.clock.install({time:new Date('2026-10-21T10:00:00Z')});
  await page.clock.pauseAt(new Date('2026-10-21T10:00:01Z'));
  await page.goto(origin+'/qa-hash-scroll/'+hash,{waitUntil:'networkidle'});
  assert(await page.evaluate(()=>typeof syncHashScroll==='function'),'The real page runtime must load');
  if(!hash){await page.keyboard.press('Tab');await page.keyboard.press('Enter');}
  else await page.locator('#contenido').focus();
  await page.keyboard.press('Tab');
  assert.equal(await page.locator('#reading').evaluate(n=>n===document.activeElement),true);
  assert((await waitForKeyboardFocusState(page)).ok);
  await page.clock.fastForward(700);
  assert((await waitForKeyboardFocusState(page)).ok,`Delayed initial hash scroll displaced keyboard focus for ${hash||'a new skip-link hash'}`);
  assert.deepEqual(errors,[]);await context.close();
 }
 // Without user interaction, the delayed alignment still serves incoming links.
 const context=await browser.newContext({viewport:{width:1440,height:900},reducedMotion:'reduce'});
 await context.route('**/qa-hash-scroll/',r=>r.fulfill({contentType:'text/html',body:fixture}));
 const page=await context.newPage();await page.clock.install({time:new Date('2026-10-21T10:00:00Z')});
 await page.clock.pauseAt(new Date('2026-10-21T10:00:01Z'));
 await page.goto(origin+'/qa-hash-scroll/#destination',{waitUntil:'networkidle'});
 await page.evaluate(()=>scrollTo(0,0));await page.clock.fastForward(700);
 assert(await page.locator('#destination').evaluate(n=>{const r=n.getBoundingClientRect();return r.top>=0&&r.top<innerHeight;}));
 await context.close();console.log('PASS initial hash alignment preserves keyboard navigation and incoming anchors.');
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const browser=await chromium.launch({headless:true});
 try{await assertInitialHashNavigation(browser,process.env.QA_ORIGIN||'http://127.0.0.1:4173');}
 finally{await browser.close();}
}
