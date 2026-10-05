import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const SHA=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const CANONICAL=(process.env.CANONICAL_ORIGIN||ORIGIN).replace(/\/$/,'');
const ROUTES=['/','/editoriales/','/convocatorias-escritores/','/metodologia-editorial/','/herramientas/','/autor.html','/prensa.html'];

async function fetchRetry(path){
  let last;
  for(let i=0;i<3;i++){
    try{
      const url=new URL(path,ORIGIN);
      url.searchParams.set('__edge',SHA||'live');
      return await fetch(url,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-edge-audit/1.0'},
        signal:AbortSignal.timeout(15000)
      });
    }catch(e){
      last=e;
      await new Promise(r=>setTimeout(r,750*(i+1)));
    }
  }
  throw last;
}

if(SHA){
  const r=await fetchRetry('/_release/'+SHA+'.json');
  assert.equal(r.status,200,'release marker');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:SHA});
}

const machine=[
  ['/editoriales/editoriales-data.json',['application/json']],
  ['/convocatorias-escritores/opportunities.json',['application/json']],
  ['/convocatorias-escritores/deadlines.ics',['text/calendar','application/octet-stream','text/plain']],
  ['/sitemap.xml',['application/xml','text/xml','application/octet-stream','text/plain']],
  ['/assets/v1-shell.js?v=14',['javascript','text/plain']],
  ['/assets/v1-shell.css?v=4',['text/css','text/plain']]
];
for(const [route,types] of machine){
  const r=await fetchRetry(route);
  assert.equal(r.status,200,route);
  const ct=(r.headers.get('content-type')||'').toLowerCase();
  assert.ok(types.some(x=>ct.includes(x)),`${route}: unexpected content-type ${ct}`);
  if(!route.endsWith('.css')&&!route.includes('.js')) {
    assert.ok(!ct.includes('text/html'),`${route}: machine resource served as HTML`);
  }
  assert.ok((await r.arrayBuffer()).byteLength>20,`${route}: empty body`);
}

const missing=await fetchRetry('/editoriales/__qa_edge_missing__/');
assert.equal(missing.status,404,'missing route must return a real 404, not a soft 200');

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  const context=await browser.newContext({viewport:{width:1280,height:900}});
  for(const route of ROUTES){
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    try{
      const url=new URL(route,ORIGIN);
      url.searchParams.set('qa_edge','1');
      url.hash='contenido';
      const r=await page.goto(url.href,{waitUntil:'domcontentloaded',timeout:20000});
      assert.equal(r?.status(),200,route);
      assert.deepEqual(pageErrors,[],`${route}: pageerror(s): ${pageErrors.join(' | ')}`);
      const dom=await page.evaluate(()=>{
        const ids=[...document.querySelectorAll('[id]')].map(e=>e.id).filter(Boolean);
        const duplicateIds=[...new Set(ids.filter((id,i)=>ids.indexOf(id)!==i))];
        const missingRefs=[];
        for(const el of document.querySelectorAll('[aria-labelledby],[aria-describedby],[aria-controls],[aria-owns]')){
          for(const attr of ['aria-labelledby','aria-describedby','aria-controls','aria-owns']){
            for(const id of (el.getAttribute(attr)||'').trim().split(/\s+/).filter(Boolean)){
              if(!document.getElementById(id)) missingRefs.push(attr+'='+id);
            }
          }
        }
        const unnamed=[];
        for(const el of document.querySelectorAll('input,select,textarea,button')){
          if(el.type==='hidden'||el.getAttribute('aria-hidden')==='true') continue;
          const s=getComputedStyle(el),r=el.getBoundingClientRect();
          if(s.display==='none'||s.visibility==='hidden'||r.width===0||r.height===0) continue;
          const by=(el.getAttribute('aria-labelledby')||'').split(/\s+/).filter(Boolean)
            .map(id=>document.getElementById(id)?.textContent||'').join(' ').trim();
          const name=(el.getAttribute('aria-label')||by||[...(el.labels||[])]
            .map(x=>x.textContent||'').join(' ')||el.getAttribute('title')||
            (el.tagName==='BUTTON'?el.textContent:'')||(el.type==='submit'?el.value:'')).trim();
          if(!name) unnamed.push(el.outerHTML.slice(0,180));
        }
        const unsafe=[...document.querySelectorAll('a[target="_blank"]')]
          .filter(a=>{
            const rel=(a.getAttribute('rel')||'').toLowerCase().split(/\s+/);
            return !rel.includes('noopener')||!rel.includes('noreferrer');
          }).map(a=>a.getAttribute('href'));
        return {
          duplicateIds,missingRefs,unnamed,unsafe,
          canonical:document.querySelector('link[rel~="canonical"]')?.href||'',
          h1:(document.querySelector('h1')?.textContent||'').trim(),
          main:(document.querySelector('main')?.innerText||'').trim().length
        };
      });
      assert.deepEqual(dom.duplicateIds,[],`${route}: duplicate ids ${dom.duplicateIds.join(',')}`);
      assert.deepEqual(dom.missingRefs,[],`${route}: broken ARIA refs ${dom.missingRefs.join(',')}`);
      assert.deepEqual(dom.unnamed,[],`${route}: unnamed controls ${dom.unnamed.join(' | ')}`);
      assert.deepEqual(dom.unsafe,[],`${route}: target=_blank without noopener+noreferrer ${dom.unsafe.join(',')}`);
      assert.ok(dom.h1&&dom.main>120,`${route}: missing substantive content`);
      assert.equal(dom.canonical,new URL(route,CANONICAL).href,`${route}: query/hash leaked into canonical`);
    }catch(e){
      failures.push(e.message);
    }finally{
      await page.close();
    }
  }

  const page=await context.newPage();
  try{
    await page.goto(ORIGIN+'/editoriales/?qa_edge_dialog=1',{waitUntil:'domcontentloaded',timeout:20000});
    const trigger=page.locator('[data-explore-open]').first();
    assert.equal(await trigger.count(),1,'Explore trigger missing');
    await trigger.focus();
    await trigger.click();
    const dialog=page.locator('#explore-dialog');
    assert.ok(await dialog.evaluate(el=>el.open),'Explore dialog did not open');
    for(let i=0;i<12;i++){
      await page.keyboard.press('Tab');
      assert.equal(
        await page.evaluate(()=>document.querySelector('#explore-dialog')?.contains(document.activeElement)),
        true,
        'focus escaped open dialog'
      );
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(50);
    assert.equal(await dialog.evaluate(el=>el.open),false,'Escape did not close Explore dialog');
    assert.equal(await trigger.evaluate(el=>el===document.activeElement),true,'focus was not restored to Explore trigger');
  }catch(e){
    failures.push(e.message);
  }finally{
    await page.close();
  }

  const filter=await context.newPage();
  try{
    await filter.goto(ORIGIN+'/editoriales/?qa_edge_filter=1',{waitUntil:'domcontentloaded',timeout:20000});
    const firstName=(await filter.locator('[data-editorial-card] h2').first().textContent())?.trim();
    assert.ok(firstName,'editorial card missing');
    const search=filter.locator('[data-editoriales-search]').first();
    assert.equal(await search.count(),1,'editorial search missing');
    await search.fill(firstName);
    await filter.waitForTimeout(120);
    assert.ok((await filter.locator('[data-editorial-card]:visible').count())>=1,'editorial filter hid every card');
    assert.ok(new URL(filter.url()).hash.length>1,'editorial filter state was not serialized into hash');
    await filter.reload({waitUntil:'domcontentloaded'});
    assert.equal(
      await filter.locator('[data-editoriales-search]').first().inputValue(),
      firstName,
      'editorial filter state did not survive reload'
    );
  }catch(e){
    failures.push(e.message);
  }finally{
    await filter.close();
  }
  await context.close();

  const nojs=await browser.newContext({
    javaScriptEnabled:false,
    viewport:{width:390,height:844},
    isMobile:true,
    hasTouch:true
  });
  for(const route of ['/editoriales/','/convocatorias-escritores/','/metodologia-editorial/']){
    const page=await nojs.newPage();
    try{
      const r=await page.goto(ORIGIN+route+'?qa_nojs=1',{waitUntil:'domcontentloaded',timeout:20000});
      assert.equal(r?.status(),200,'no-JS '+route);
      const state=await page.evaluate(()=>({
        h:(document.querySelector('h1')?.textContent||'').trim(),
        m:(document.querySelector('main')?.innerText||'').trim().length,
        links:document.querySelectorAll('main a[href]').length
      }));
      assert.ok(state.h&&state.m>200&&state.links>0,`no-JS ${route}: core content unavailable`);
    }catch(e){
      failures.push(e.message);
    }finally{
      await page.close();
    }
  }
  await nojs.close();
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production edge contracts: keyboard, ARIA, no-JS, URL, 404 and MIME');
