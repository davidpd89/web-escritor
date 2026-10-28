import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const route of ['/eventos.html','/ferias.html']) {
    for(const width of [390,1440]) {
      const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
      const page=await context.newPage();
      const response=await page.goto(BASE+route,{waitUntil:'load'});
      assert.ok(response?.ok(),`${route} ${width}: HTTP ${response?.status()}`);
      const images=page.locator('main img');
      assert.ok(await images.count()>0,`${route} ${width}: no se encontraron imágenes documentales`);
      for(const img of await images.all()) {
        const before=await img.evaluate(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,declaredWidth:Number(el.getAttribute('width')),declaredHeight:Number(el.getAttribute('height'))}));
        assert.ok(before.declaredWidth>0&&before.declaredHeight>0,`${route} ${width}: imagen sin dimensiones declaradas: ${await img.getAttribute('src')}`);
        await img.scrollIntoViewIfNeeded();
        await img.evaluate(async el=>{if(!el.complete) await new Promise((resolve,reject)=>{el.addEventListener('load',resolve,{once:true});el.addEventListener('error',reject,{once:true});});if(el.decode) await el.decode();});
        const after=await img.evaluate(el=>({width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight}));
        assert.ok(after.naturalWidth>0&&after.naturalHeight>0,`${route} ${width}: imagen sin decodificar: ${await img.getAttribute('src')}`);
        const ratio=before.declaredWidth/before.declaredHeight;
        const natural=after.naturalWidth/after.naturalHeight;
        assert.ok(Math.abs(ratio-natural)/natural<0.03,`${route} ${width}: proporción declarada ${ratio} frente a proporción natural ${natural}`);
        assert.ok(Math.abs(before.height-after.height)<2,`${route} ${width}: imagen ${await img.getAttribute('src')} cambió su altura ${before.height} -> ${after.height}`);
      }
      await context.close();
    }
  }
} finally {await browser.close();}
