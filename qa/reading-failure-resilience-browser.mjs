// Optional market transport must never reset a reader's work or hide books.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';

const origin=(process.env.QA_BASE_URL||'http://127.0.0.1:4175').replace(/\/$/,'');
const out=process.env.QA_ARTIFACT_DIR||'.ci/reading-resilience';
const catalogue=JSON.parse(await fs.readFile('data/reading-catalogue.json','utf8'));
const books=catalogue.libros.filter(b=>b.estado==='publicado');
const selected=books.find(b=>b.isbn13);
assert(selected,'The real catalogue must contain an ISBN to exercise search.');
const sha=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
const results=[];
const visible=page=>page.locator('[data-catalogue-book]:visible').evaluateAll(es=>es.map(e=>e.dataset.bookId));

async function runCase(width,mode){
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
  // Exercise first-party code only: no dependence on analytics availability.
  await context.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
  await context.addInitScript(()=>{
    sessionStorage.setItem('dp-intro-seen','1');
    localStorage.setItem('nl-popup-ts',String(Date.now()));
  });
  const page=await context.newPage(),errors=[];
  page.setDefaultTimeout(8000);
  page.setDefaultNavigationTimeout(20000);
  page.on('pageerror',e=>errors.push(e.message));
  let intercepted=0,release;
  const gate=new Promise(resolve=>release=resolve);
  let handled;
  const done=new Promise(resolve=>handled=resolve);
  const result={width,mode,status:'pass',release:sha};
  try{
    if(mode==='script-unavailable'){
      await context.route('**/assets/reading-catalogue.js*',async route=>{intercepted++;await route.abort();});
    }else{
      await context.route('**/assets/reading-market.json',async route=>{
        intercepted++;
        await gate;
        try{
          if(mode==='connection-failure')await route.abort('connectionfailed');
          else if(mode==='http-503')await route.fulfill({status:503,contentType:'text/plain',body:'Controlled service failure'});
          else if(mode==='malformed-json')await route.fulfill({contentType:'application/json',body:'{"schema_version":'});
          else if(mode==='wrong-shape')await route.fulfill({json:{schema_version:1,offers:null,ratings:{}}});
          else await route.fulfill({json:{schema_version:1,offers:[],ratings:[]}});
        }finally{handled();}
      });
    }
    const response=await page.goto(origin+'/recomendaciones/?utm_source=resilience-test',{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200,'Local catalogue response');
    assert.equal(await page.locator('[data-catalogue-book]').count(),books.length,'Use the complete real catalogue');
    if(mode==='script-unavailable'){
      await page.waitForLoadState('networkidle');
      assert(intercepted>0,'The intended script failure must actually be injected');
      assert.equal((await visible(page)).length,books.length,'Every static card remains available when JS delivery fails');
      assert(await page.locator('[data-catalogue-filters] fieldset').evaluate(n=>n.disabled),'Fallback fieldset must declare disabled');
      assert(await page.locator('[data-filter="q"]').isDisabled(),'Unavailable search must not pretend to work');
    }else{
      await page.waitForFunction(()=>document.querySelector('[data-catalogue-filters] fieldset')?.disabled===false);
      await page.waitForFunction(()=>document.querySelector('[data-filter="q"]'));
      // The request remains pending until the user has changed both controls.
      await page.locator('[data-filter="q"]').fill(selected.isbn13);
      await page.locator('[data-filter="orden"]').selectOption('titulo_desc');
      assert.deepEqual(await visible(page),[selected.id],'Search works before market response arrives');
      const before=page.url();
      release();
      let timer;
      try{await Promise.race([done,new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('The injected market response did not finish')),10000);})]);}
      finally{clearTimeout(timer);}
      await page.waitForLoadState('networkidle');
      assert.equal(intercepted,1,'The intended market request must actually be intercepted');
      assert.equal(await page.locator('[data-filter="q"]').inputValue(),selected.isbn13,'Market result must preserve user input');
      assert.equal(await page.locator('[data-filter="orden"]').inputValue(),'titulo_desc','Market result must preserve chosen order');
      assert.equal(page.url(),before,'Market result must preserve the shareable URL');
      assert.deepEqual(await visible(page),[selected.id],'Market failure must not reset or hide the result');
      assert.equal(await page.locator('[data-price-book]:visible').count(),0,'No fabricated price after failed or empty market response');
      const ratings = await page.locator('[data-rating-book]').evaluateAll(boxes => boxes.map(box => ({
        text: box.textContent.trim(),
        label: box.querySelector('a')?.getAttribute('aria-label'),
        fill: box.querySelector('.catalogue-stars')?.style.getPropertyValue('--rating')
      })));
      assert(ratings.every(r => !r.text || (r.text === 'Goodreads ★★★★★ 0,0 (0)' && r.fill === '0%' && r.label === 'Goodreads: aún sin valoraciones públicas')),'Only an explicitly empty Goodreads state may appear without verified ratings');
      assert(await page.locator('[data-filter="valoracion"]').isDisabled(),'No active rating filter without verified ratings');
      assert(await page.locator('[data-filter="precio_max"]').isEnabled(),'Editorial PVP filtering stays available without market prices');
      const maximum = Math.ceil(selected.pvp_centimos / 100);
      if (maximum) {
        await page.locator('[data-filter="precio_max"]').fill(String(maximum));
        assert.deepEqual(await visible(page),[selected.id],'Editorial PVP works after market failure');
        await page.locator('[data-filter="precio_max"]').fill('0.01');
        assert.deepEqual(await visible(page),[],'PVP filtering excludes editions above the limit');
        await page.locator('[data-filter="precio_max"]').fill('');
      }
      // Reload with the generated hash: the failure must not break shared links.
      await page.reload({waitUntil:'networkidle'});
      await page.waitForFunction(isbn=>document.querySelector('[data-filter="q"]')?.value===isbn,selected.isbn13);
      assert.deepEqual(await visible(page),[selected.id],'Shared search survives reload with failed market');
      assert.equal(await page.locator('[data-filter="orden"]').inputValue(),'titulo_desc','Shared ordering survives reload');
    }
    const card=page.locator('[data-catalogue-book]').filter({has:page.locator(`a[href="/recomendaciones/libros/${selected.slug}/"]`)}).first();
    const amazon=card.locator('.catalogue-card__buy');
    assert.equal(await amazon.getAttribute('target'),'_blank','Purchase still opens another tab');
    assert.equal(new URL(await amazon.getAttribute('href')).searchParams.get('tag'),'davidporto-21','Purchase retains the affiliate tag');
    if(selected.pvp_centimos){
      const expected=(selected.pvp_centimos/100).toLocaleString('es-ES',{style:'currency',currency:'EUR'}).replace(/\s/g,' ');
      assert((await card.locator('.catalogue-pvp').innerText()).replace(/\s/g,' ').includes(expected),'Editorial PVP remains available independently of market data');
    }
    assert.equal(new URL(page.url()).searchParams.get('utm_source'),'resilience-test','Source parameter survives interactions and reload');
    if(mode==='connection-failure'){
      await page.getByRole('button',{name:'Restablecer',exact:true}).click();
      await page.waitForFunction(n=>document.querySelectorAll('[data-catalogue-book]:not([hidden])').length===Math.min(24,n),books.length);
      assert.equal(new URL(page.url()).hash,'','Reset remains available after transport failure');
      if(books.length>24){
        await page.locator('.catalogue-pagination button').last().click();
        assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('pagina'),'2','Pagination remains available after transport failure');
      }
    }
    assert.deepEqual(errors,[],'No uncaught first-party errors');
    result.visible=await visible(page);
  }catch(error){
    result.status='fail';result.error=error.stack||String(error);result.pageErrors=errors;
    result.url=page.url();result.visible=await visible(page).catch(()=>[]);
    await page.screenshot({path:`${out}/${width}-${mode}.png`,fullPage:true}).catch(()=>{});
  }finally{
    release();
    await context.close();
  }
  results.push(result);
  console.log(`${result.status.toUpperCase()} ${width} ${mode}${result.error?' '+result.error.split('\n')[0]:''}`);
}

try{
  for(const width of [390,1280]){
    for(const mode of ['connection-failure','http-503','malformed-json','wrong-shape','delayed-empty','script-unavailable']){
      await runCase(width,mode);
    }
  }
}finally{
  await browser.close();
  await fs.writeFile(`${out}/results.json`,JSON.stringify({release:sha,results},null,2)+'\n');
  await fs.writeFile(`${out}/report.md`,['# Catalogue failure resilience','',`Source commit: ${sha}`,'',...results.map(r=>`- **${r.status.toUpperCase()}** ${r.width}px / ${r.mode}${r.error?': '+r.error.split('\n')[0]:''}`),''].join('\n'));
}
assert.equal(results.filter(r=>r.status==='fail').length,0,`See ${out}/results.json and failure screenshots.`);
