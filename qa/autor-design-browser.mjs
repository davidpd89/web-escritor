import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/autor-design';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728',1728,1050],['desktop-1440',1440,1000],['desktop-1280',1280,900],['tablet-1024',1024,900],
  ['bio-901',901,900],['bio-900',900,900],['tablet-768',768,1024],['section-701',701,900],['section-700',700,900],
  ['head-601',601,900],['head-600',600,900],['hero-411',411,860],['hero-410',410,860],['mobile-390',390,844],['mobile-320',320,820],
];

function columns(value){
  if(!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
}
async function style(locator){
  return locator.evaluate(el=>{
    const s=getComputedStyle(el),r=el.getBoundingClientRect();
    return {display:s.display,gridTemplateColumns:s.gridTemplateColumns,color:s.color,backgroundColor:s.backgroundColor,borderTopWidth:s.borderTopWidth,borderBottomWidth:s.borderBottomWidth,borderRadius:s.borderRadius,boxShadow:s.boxShadow,fontFamily:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,maxWidth:s.maxWidth,width:r.width,height:r.height,left:r.left,top:r.top};
  });
}
async function context(browser,{width,height},js=true){
  const c=await browser.newContext({viewport:{width,height},javaScriptEnabled:js,reducedMotion:'reduce'});
  if(js) await c.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()))}catch{}});
  return c;
}
async function inspectorStyles(c,p,css){
  const cdp=await c.newCDPSession(p);await cdp.send('Page.enable');await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  const {frameTree}=await cdp.send('Page.getFrameTree');const {styleSheetId}=await cdp.send('CSS.createStyleSheet',{frameId:frameTree.frame.id});
  await cdp.send('CSS.setStyleSheetText',{styleSheetId,text:css});
}
async function noOverflow(p,label){
  const x=await p.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
  assert.ok(x<=1,`${label}: overflow ${x}px`);return x;
}

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[],measurements=[];
try{
  for(const [name,width,height] of viewports){
    const c=await context(browser,{width,height});const p=await c.newPage();
    try{
      const r=await p.goto(`${ORIGIN}/autor.html`,{waitUntil:'networkidle',timeout:20000});assert.ok(r?.ok(),`${name}: autor no carga`);
      await p.evaluate(()=>document.fonts?.ready);await p.waitForTimeout(100);
      assert.equal(await p.locator('html').getAttribute('data-editorial-context'),'autor',`${name}: contexto Autor perdido`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${name}: familia identity alterada`);
      assert.equal(await p.locator('link[rel="canonical"]').getAttribute('href'),'https://davidportodiaz.com/autor.html',`${name}: canonical alterado`);
      assert.equal(await p.locator('h1').count(),1,`${name}: H1 no único`);
      assert.equal((await p.locator('h1').textContent()).trim(),'David Porto Díaz',`${name}: H1 alterado`);
      assert.equal(await p.locator('.section-context [aria-current="page"]').getAttribute('href'),'/autor.html',`${name}: navegación contextual no marca Autor`);

      assert.equal(await p.locator('.masthead-name-row__avatar').getAttribute('src'),'/assets/david-porto-avatar-masthead.webp',`${name}: avatar de masthead sustituido`);
      const portrait=p.locator('.author-portrait img');assert.equal(await portrait.count(),1,`${name}: retrato principal ausente`);
      assert.equal(await portrait.getAttribute('src'),'/assets/david-porto-diaz-escritor-fantasia-madrid-autor.avif',`${name}: retrato principal sustituido`);
      assert.equal(await portrait.getAttribute('fetchpriority'),'high',`${name}: retrato pierde prioridad LCP`);
      const portraitMetrics=await portrait.evaluate(img=>({naturalWidth:img.naturalWidth,naturalHeight:img.naturalHeight,width:img.getBoundingClientRect().width,height:img.getBoundingClientRect().height}));
      assert.ok(portraitMetrics.naturalWidth>0&&portraitMetrics.width>0&&portraitMetrics.height>0,`${name}: retrato no visible/cargado`);
      assert.equal(await p.locator('.author-bio__aside img').count(),1,`${name}: imagen documental lateral ausente`);
      assert.equal(await p.locator('#libros .id-card').count(),3,`${name}: obra publicada deja de tener tres registros`);
      assert.equal(await p.locator('#premios .awards-ledger li').count(),3,`${name}: trayectoria visible alterada`);
      assert.equal(await p.locator('#reseñas .quote-stream li').count(),3,`${name}: testimonios visibles alterados`);

      const person=await p.evaluate(()=>{
        const docs=[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent));
        const nodes=docs.flatMap(d=>d['@graph']||[d]);return nodes.find(n=>n['@type']==='Person');
      });
      assert.equal(person?.name,'David Porto Díaz',`${name}: Person schema pierde nombre`);
      assert.equal(person?.award?.length,2,`${name}: Person schema altera reconocimientos`);

      const overflow=await noOverflow(p,name);
      const masthead=await style(p.locator('.v1-masthead'));
      const title=await style(p.locator('.masthead-name-row h1'));
      const avatar=await style(p.locator('.masthead-name-row__avatar'));
      const bio=await style(p.locator('.author-bio'));
      const portraitStyle=await style(p.locator('.author-portrait'));
      const copy=await style(p.locator('.author-bio__copy'));
      const aside=await style(p.locator('.author-bio__aside'));
      const sectionHead=await style(p.locator('#libros .v1-section__head'));
      const books=await style(p.locator('#libros .id-cards'));
      const awards=await style(p.locator('#premios .awards-ledger'));
      const quotes=await style(p.locator('#reseñas .quote-stream'));
      const activeContext=await style(p.locator('.section-context [aria-current="page"]'));
      const footer=await style(p.locator('.site-footer'));

      assert.equal(columns(bio.gridTemplateColumns),width>900?3:1,`${name}: seam heredado 901/900 de bio cambió`);
      assert.equal(columns(masthead.gridTemplateColumns),width>900?2:1,`${name}: seam heredado 901/900 de masthead cambió`);
      assert.equal(columns(sectionHead.gridTemplateColumns),width>600?2:1,`${name}: seam heredado 601/600 de cabecera de sección cambió`);

      measurements.push({name,width,height,overflow,portraitMetrics,masthead,title,avatar,bio,portrait:portraitStyle,copy,aside,sectionHead,books,awards,quotes,activeContext,footer});
      await p.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:path.join(OUT,`autor-${name}.png`),fullPage:true});
    }catch(error){failures.push({viewport:name,width,height,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  for(const route of ['/premios.html','/eventos.html','/prensa.html']){
    const c=await context(browser,{width:1440,height:1000});const p=await c.newPage();
    try{
      const r=await p.goto(ORIGIN+route,{waitUntil:'networkidle'});assert.ok(r?.ok(),`${route}: control de aislamiento no carga`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${route}: familia identity perdida`);
      await noOverflow(p,`${route} isolation`);
      await p.screenshot({path:path.join(OUT,`isolation-${route.slice(1,-5)}-1440.png`),fullPage:true});
    }catch(error){failures.push({viewport:`isolation-${route}`,width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:844},false);const p=await c.newPage();
    try{
      const r=await p.goto(`${ORIGIN}/autor.html`,{waitUntil:'load'});assert.ok(r?.ok(),'no-js: Autor no carga');
      assert.ok((await p.locator('main').innerText()).length>1000,'no-js: biografía deja de estar disponible');
      assert.equal(await p.locator('.author-portrait img').count(),1,'no-js: retrato principal ausente');
      assert.equal(await p.locator('#libros .id-card').count(),3,'no-js: obra publicada ausente');
      await noOverflow(p,'no-js 390');await p.screenshot({path:path.join(OUT,'autor-no-js-390.png'),fullPage:true});
    }catch(error){failures.push({viewport:'no-js-390',width:390,height:844,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:844});const p=await c.newPage();
    try{
      await p.goto(`${ORIGIN}/autor.html`,{waitUntil:'networkidle'});
      await inspectorStyles(c,p,'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');
      await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await noOverflow(p,'text spacing');
      await p.evaluate(()=>document.documentElement.style.zoom='2');await noOverflow(p,'zoom 200%');
      await p.keyboard.press('Tab');assert.notEqual(await p.evaluate(()=>document.activeElement?.tagName),'BODY','keyboard: foco no avanza');
    }catch(error){failures.push({viewport:'wcag-stress-390',width:390,height:844,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'autor-design-report.json'),JSON.stringify({route:'/autor.html',phase:'inherited-baseline',viewports:viewports.length,measurements,failures},null,2));
assert.deepEqual(failures,[],`Autor inherited-baseline failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Autor inherited baseline: PASS (${viewports.length} viewports + 3 isolation controls + no-JS + WCAG stress)`);
