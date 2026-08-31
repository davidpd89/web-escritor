import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/ferias-design';
fs.mkdirSync(OUT,{recursive:true});

const viewports=[
  ['wide-1728',1728,1050],['desktop-1440',1440,1000],['desktop-1280',1280,900],['tablet-1024',1024,900],
  ['archive-901',901,900],['archive-900',900,900],['entry-768',768,1024],['mid-701',701,950],['mid-700',700,950],
  ['media-601',601,950],['media-600',600,950],['hero-411',411,900],['hero-410',410,900],['mobile-390',390,900],['mobile-320',320,900],
];

function columns(value){
  if(!value||value==='none') return 0;
  return value.trim().split(/\s+/).length;
}
async function context(browser,{width,height},js=true){
  const c=await browser.newContext({viewport:{width,height},javaScriptEnabled:js,reducedMotion:'reduce'});
  if(js) await c.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()))}catch{}});
  return c;
}
async function open(page,suffix=''){
  const r=await page.goto(`${ORIGIN}/ferias.html${suffix}`,{waitUntil:'load',timeout:20000});
  assert.ok(r?.ok(),'Ferias no carga');
  await page.evaluate(()=>document.fonts?.ready);
  await page.waitForTimeout(120);
}
async function overflowState(page){
  return page.evaluate(()=>({viewport:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth}));
}
async function noOverflow(page,label){
  const s=await overflowState(page);
  assert.ok(s.overflow<=1,`${label}: overflow horizontal ${s.overflow}px (${s.scroll}/${s.viewport})`);
  return s.overflow;
}
async function typographyState(page){
  return page.evaluate(()=>{
    const snap=el=>{const cs=getComputedStyle(el),r=el.getBoundingClientRect();return{width:r.width,height:r.height,fontFamily:cs.fontFamily,fontSize:cs.fontSize,lineHeight:cs.lineHeight}};
    const title=document.querySelector('.fairs-masthead h1');
    const summary=document.querySelector('.fair-record__summary');
    const ledger=document.querySelector('.fair-ledger dd');
    return {supported:!!document.fonts,loaded:document.fonts?.status==='loaded',title:snap(title),summary:snap(summary),ledger:snap(ledger)};
  });
}
async function stableTypography(page){
  const before=await typographyState(page);
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const after=await typographyState(page);
  return {supported:before.supported,loaded:before.loaded&&after.loaded,before,after};
}
async function loadImages(page){
  for(const selector of ['.fair-media--aranjuez img','.fair-media--madrid img']){
    const imgs=page.locator(selector);
    for(let i=0;i<await imgs.count();i++){
      const img=imgs.nth(i);await img.scrollIntoViewIfNeeded();
      await img.evaluate(async el=>{if(!el.complete)await new Promise((res,rej)=>{el.addEventListener('load',res,{once:true});el.addEventListener('error',rej,{once:true});});if(el.decode){try{await el.decode()}catch{}}});
      const n=await img.evaluate(el=>({w:el.naturalWidth,h:el.naturalHeight}));
      assert.ok(n.w>0&&n.h>0,`${selector}[${i}] no decodifica`);
    }
  }
}
async function addTextSpacing(context,page){
  const cdp=await context.newCDPSession(page);await cdp.send('Page.enable');await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  const {frameTree}=await cdp.send('Page.getFrameTree');const {styleSheetId}=await cdp.send('CSS.createStyleSheet',{frameId:frameTree.frame.id});
  await cdp.send('CSS.setStyleSheetText',{styleSheetId,text:'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'});
}

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[],measurements=[];
try{
  for(const [name,width,height] of viewports){
    const c=await context(browser,{width,height});const page=await c.newPage();
    try{
      await open(page);
      assert.equal(await page.locator('html').getAttribute('data-editorial-context'),'prensa',`${name}: contexto de Prensa/agenda perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'),'identity',`${name}: familia identity alterada`);
      assert.ok((await page.locator('main#contenido').getAttribute('class')||'').split(/\s+/).includes('fairs-page'),`${name}: owner .fairs-page perdido`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),'https://davidportodiaz.com/ferias.html',`${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(),1,`${name}: H1 no único`);
      assert.equal((await page.locator('h1').textContent()).trim(),'Ferias del libro',`${name}: H1 alterado`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'),'/ferias.html',`${name}: navegación contextual no marca Ferias`);

      assert.equal(await page.locator('.fairs-index li').count(),2,`${name}: índice debe conservar dos ferias`);
      assert.deepEqual(await page.locator('.fairs-index a').evaluateAll(a=>a.map(x=>x.getAttribute('href'))),['#feria-libro-aranjuez-2026','#feria-libro-madrid-2026'],`${name}: índice alterado`);
      assert.equal(await page.locator('.fair-record').count(),2,`${name}: archivo debe conservar dos registros`);
      assert.equal(await page.locator('#feria-libro-aranjuez-2026 .fair-ledger>div').count(),5,`${name}: ledger Aranjuez alterado`);
      assert.equal(await page.locator('#feria-libro-madrid-2026 .fair-ledger>div').count(),6,`${name}: ledger Madrid alterado`);
      assert.equal(await page.locator('.fair-media--aranjuez figure').count(),2,`${name}: galería Aranjuez debe conservar dos fotos`);
      assert.equal(await page.locator('.fair-media--madrid figure').count(),6,`${name}: galería Madrid debe conservar seis fotos`);
      assert.equal(await page.locator('#feria-libro-madrid-2026 .fair-record__references a').count(),3,`${name}: referencias Madrid alteradas`);
      const note=(await page.locator('#feria-libro-aranjuez-2026 .fair-source-note').innerText()).toLowerCase();
      assert.ok(note.includes('no publica el turno individual')&&note.includes('no atribuye una hora exacta'),`${name}: cautela documental Aranjuez alterada`);
      assert.ok((await page.locator('#feria-libro-madrid-2026').innerText()).includes('19:00')&&(await page.locator('#feria-libro-madrid-2026').innerText()).includes('20:00'),`${name}: horario Madrid ausente`);

      const schema=await page.evaluate(()=>{
        const docs=[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent));
        return docs.flatMap(d=>d['@graph']||[d]).map(n=>({type:n['@type'],id:n['@id']||null,startDate:n.startDate||null,url:n.url||null}));
      });
      assert.ok(schema.some(n=>n.type==='WebPage'&&n.url==='https://davidportodiaz.com/ferias.html'),`${name}: WebPage schema ausente`);
      const events=schema.filter(n=>n.type==='Event');assert.equal(events.length,2,`${name}: deben existir dos Event JSON-LD`);
      assert.ok(events.some(n=>n.id?.endsWith('#feria-libro-aranjuez-2026')&&n.startDate==='2026-05-23'),`${name}: Event Aranjuez alterado`);
      assert.ok(events.some(n=>n.id?.endsWith('#feria-libro-madrid-2026')&&n.startDate==='2026-06-10T19:00:00+02:00'),`${name}: Event Madrid alterado`);

      const masthead=await page.locator('.fairs-masthead').evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const year=await page.locator('.fairs-year').evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const body=await page.locator('.fair-record__body').first().evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const header=await page.locator('.fair-record__header').first().evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const ledger=await page.locator('.fair-ledger>div').first().evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const aranjuez=await page.locator('.fair-media--aranjuez').evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      const madrid=await page.locator('.fair-media--madrid').evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      assert.equal(columns(masthead),width>900?2:1,`${name}: seam 901/900 masthead cambió (${masthead})`);
      assert.equal(columns(year),width>900?2:1,`${name}: seam 901/900 year cambió (${year})`);
      assert.equal(columns(body),width>900?2:1,`${name}: seam 901/900 body cambió (${body})`);
      assert.equal(columns(header),width>600?2:1,`${name}: seam 601/600 header cambió (${header})`);
      assert.equal(columns(ledger),width>600?2:1,`${name}: seam 601/600 ledger cambió (${ledger})`);
      assert.equal(columns(aranjuez),width>600?2:1,`${name}: seam 601/600 Aranjuez cambió (${aranjuez})`);
      assert.equal(columns(madrid),width>900?3:(width>600?2:1),`${name}: seam Madrid 901/900 o 601/600 cambió (${madrid})`);

      const overflow=await noOverflow(page,name);const typography=await stableTypography(page);
      assert.ok(typography.loaded,`${name}: fuentes no estabilizadas`);assert.deepEqual(typography.before,typography.after,`${name}: geometría tipográfica inestable`);
      measurements.push({name,width,height,overflow,typography,mastheadColumns:masthead,yearColumns:year,bodyColumns:body,headerColumns:header,ledgerColumns:ledger,aranjuezColumns:aranjuez,madridColumns:madrid});
      await loadImages(page);await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(OUT,`ferias-${name}.png`),fullPage:true});
    }catch(error){failures.push({viewport:name,width,height,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:1440,height:1000});const page=await c.newPage();
    try{
      await open(page,'#feria-libro-madrid-2026');
      const target=await page.locator('#feria-libro-madrid-2026').evaluate(el=>({border:getComputedStyle(el).borderBottomColor,before:getComputedStyle(el,'::before').backgroundColor,height:getComputedStyle(el,'::before').height}));
      assert.notEqual(target.before,'rgba(0, 0, 0, 0)','target Madrid sin rail de foco documental');
      await loadImages(page);await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(OUT,'ferias-target-madrid-1440.png'),fullPage:true});
    }catch(error){failures.push({viewport:'target-madrid-1440',width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  for(const route of ['/prensa.html','/eventos.html','/premios.html']){
    const c=await context(browser,{width:1440,height:1000});const page=await c.newPage();
    try{
      const r=await page.goto(ORIGIN+route,{waitUntil:'load'});assert.ok(r?.ok(),`${route}: aislamiento no carga`);await noOverflow(page,`${route} isolation`);
      assert.equal(await page.locator('.fairs-page').count(),0,`${route}: owner Ferias filtrado`);
      await page.screenshot({path:path.join(OUT,`isolation-${route.slice(1,-5)}-1440.png`),fullPage:true});
    }catch(error){failures.push({viewport:`isolation-${route}`,width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900},false);const page=await c.newPage();
    try{
      const r=await page.goto(`${ORIGIN}/ferias.html`,{waitUntil:'load'});assert.ok(r?.ok(),'no-js: Ferias no carga');
      assert.equal(await page.locator('.fair-record').count(),2,'no-js: registros incompletos');assert.equal(await page.locator('.fair-media figure').count(),8,'no-js: galería incompleta');
      await loadImages(page);await page.evaluate(()=>window.scrollTo(0,0));
      await noOverflow(page,'no-js 390');await page.screenshot({path:path.join(OUT,'ferias-no-js-390.png'),fullPage:true});
    }catch(error){failures.push({viewport:'no-js-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const page=await c.newPage();
    try{await open(page);await addTextSpacing(c,page);await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await noOverflow(page,'text spacing');await page.keyboard.press('Tab');assert.notEqual(await page.evaluate(()=>document.activeElement?.tagName),'BODY','keyboard: foco no avanza');}
    catch(error){failures.push({viewport:'text-spacing-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const page=await c.newPage();
    try{await open(page);await page.evaluate(()=>document.documentElement.style.zoom='2');await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await noOverflow(page,'zoom 200%');}
    catch(error){failures.push({viewport:'zoom-200-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'ferias-design-report.json'),JSON.stringify({route:'/ferias.html',phase:'visual-system-contract',viewports:viewports.length,measurements,failures},null,2));
assert.deepEqual(failures,[],`Ferias visual-system contract failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Ferias visual-system contract: PASS (${viewports.length} viewports + target + 3 isolation controls + no-JS + WCAG stress)`);
