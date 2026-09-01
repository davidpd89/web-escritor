import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const OUT=process.env.QA_OUT||'qa-artifacts/design-evidence-hardening';
fs.mkdirSync(OUT,{recursive:true});

async function context(browser,{width,height,js}){
  const c=await browser.newContext({viewport:{width,height},javaScriptEnabled:js,reducedMotion:'reduce'});
  if(js) await c.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()))}catch{}});
  return c;
}

async function open(page,route,label){
  const r=await page.goto(`${ORIGIN}${route}`,{waitUntil:'load',timeout:20000});
  assert.ok(r?.ok(),`${label}: ${route} no carga`);
  await page.evaluate(()=>document.fonts?.ready);
  await page.waitForTimeout(100);
}

async function decodeImages(page,selectors,label){
  const decoded=[];
  for(const selector of selectors){
    const images=page.locator(selector);
    const count=await images.count();
    assert.ok(count>0,`${label}: selector sin imágenes: ${selector}`);
    for(let i=0;i<count;i++){
      const image=images.nth(i);
      await image.scrollIntoViewIfNeeded();
      await image.evaluate(async img=>{
        if(!img.complete){
          await new Promise((resolve,reject)=>{
            img.addEventListener('load',resolve,{once:true});
            img.addEventListener('error',reject,{once:true});
          });
        }
        if(img.decode){try{await img.decode();}catch{}}
      });
      const state=await image.evaluate(img=>({
        src:img.currentSrc||img.src,
        naturalWidth:img.naturalWidth,
        naturalHeight:img.naturalHeight,
        loading:img.getAttribute('loading')||'',
      }));
      assert.ok(state.naturalWidth>0&&state.naturalHeight>0,`${label}: ${selector}[${i}] no decodifica (${state.naturalWidth}x${state.naturalHeight})`);
      decoded.push({selector,index:i,...state});
    }
  }
  return decoded;
}

async function noOverflow(page,label){
  const state=await page.evaluate(()=>({viewport:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));
  const overflow=state.scroll-state.viewport;
  assert.ok(overflow<=1,`${label}: overflow horizontal ${overflow}px (${state.scroll}/${state.viewport})`);
  return overflow;
}

const cases=[
  {
    id:'autor-js-1440',route:'/autor.html',width:1440,height:1000,js:true,
    selectors:['.author-portrait img','.author-bio__aside img'],
  },
  {
    id:'autor-no-js-390',route:'/autor.html',width:390,height:844,js:false,
    selectors:['.author-portrait img','.author-bio__aside img'],
  },
  {
    id:'eventos-no-js-390',route:'/eventos.html',width:390,height:900,js:false,
    selectors:['#feria-libro-madrid-2026 img'],
  },
  {
    id:'prensa-no-js-390',route:'/prensa.html',width:390,height:900,js:false,
    selectors:['.press-author-photo img','.event-photo-grid img','#ficha-manecillas img','#ficha img'],
  },
];

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[];
const results=[];
try{
  for(const test of cases){
    const c=await context(browser,test);const page=await c.newPage();
    try{
      await open(page,test.route,test.id);
      const decoded=await decodeImages(page,test.selectors,test.id);
      const overflow=await noOverflow(page,test.id);
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(OUT,`${test.id}.png`),fullPage:true});
      results.push({id:test.id,route:test.route,width:test.width,height:test.height,javaScriptEnabled:test.js,overflow,decoded});
    }catch(error){
      failures.push({id:test.id,route:test.route,error:error instanceof Error?error.message:String(error)});
    }finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'design-evidence-hardening-report.json'),JSON.stringify({phase:'inherited-evidence-hardening',cases:cases.length,results,failures},null,2));
assert.deepEqual(failures,[],`Inherited design evidence hardening failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Inherited design evidence hardening: PASS (${cases.length} cases)`);
