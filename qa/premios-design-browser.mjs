import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/premios-design';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728',1728,1050],['desktop-1440',1440,1000],['desktop-1280',1280,900],['tablet-1024',1024,900],
  ['identity-901',901,900],['identity-900',900,900],['tablet-768',768,1024],['attrib-761',761,950],['attrib-760',760,950],
  ['head-601',601,950],['head-600',600,950],['hero-411',411,900],['hero-410',410,900],['mobile-390',390,900],['mobile-320',320,900],
];

function columns(value){
  if(!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
}
async function style(locator){
  return locator.evaluate(el=>{
    const s=getComputedStyle(el),r=el.getBoundingClientRect();
    return {
      display:s.display,gridTemplateColumns:s.gridTemplateColumns,color:s.color,backgroundColor:s.backgroundColor,
      backgroundImage:s.backgroundImage,borderTopWidth:s.borderTopWidth,borderBottomWidth:s.borderBottomWidth,
      borderLeftWidth:s.borderLeftWidth,borderRadius:s.borderRadius,boxShadow:s.boxShadow,fontFamily:s.fontFamily,
      fontSize:s.fontSize,lineHeight:s.lineHeight,maxWidth:s.maxWidth,width:r.width,height:r.height,left:r.left,top:r.top,
    };
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
      const r=await p.goto(`${ORIGIN}/premios.html`,{waitUntil:'networkidle',timeout:20000});assert.ok(r?.ok(),`${name}: Premios no carga`);
      await p.evaluate(()=>document.fonts?.ready);await p.waitForTimeout(100);
      assert.equal(await p.locator('html').getAttribute('data-editorial-context'),'autor',`${name}: contexto de identidad perdido`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${name}: familia identity alterada`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-page'),'awards',`${name}: scope estático awards perdido`);
      assert.equal(await p.locator('link[rel="canonical"]').getAttribute('href'),'https://davidportodiaz.com/premios.html',`${name}: canonical alterado`);
      assert.equal(await p.locator('h1').count(),1,`${name}: H1 no único`);
      assert.equal((await p.locator('h1').textContent()).trim(),'Premios y reconocimientos',`${name}: H1 alterado`);
      assert.equal(await p.locator('.section-context [aria-current="page"]').getAttribute('href'),'/premios.html',`${name}: navegación contextual no marca Premios`);
      assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--awards-blue').trim()),'#1d4f96',`${name}: token azul documental perdido`);

      const records=p.locator('#reconocimientos [data-award-record]');
      assert.equal(await records.count(),2,`${name}: deben existir exactamente dos reconocimientos`);
      assert.equal((await records.nth(0).locator('[data-award-result]').textContent()).trim(),'Primer Premio',`${name}: primer resultado alterado`);
      assert.equal((await records.nth(0).locator('[data-award-organizer]').textContent()).trim(),'Letras Como Espada',`${name}: primer organizador alterado`);
      assert.equal(await records.nth(0).locator('[data-award-source]').count(),2,`${name}: primer reconocimiento pierde su doble evidencia`);
      assert.equal((await records.nth(1).locator('[data-award-result]').textContent()).trim(),'Top 10 — Finalista',`${name}: segundo resultado alterado`);
      assert.equal((await records.nth(1).locator('[data-award-organizer]').textContent()).trim(),'BABIDI-BÚ',`${name}: segundo organizador alterado`);
      assert.equal(await records.nth(1).locator('[data-award-source]').count(),1,`${name}: segundo reconocimiento debe conservar una única fuente pública`);
      assert.equal(await p.locator('#colaboraciones .awards-ledger > li').count(),3,`${name}: trayectoria editorial alterada`);
      assert.equal(await p.locator('#recepcion .awards-ledger > li').count(),1,`${name}: recepción alterada`);
      assert.equal(await p.locator('#conocer .awards-next > a').count(),3,`${name}: salidas de continuación alteradas`);

      const person=await p.evaluate(()=>{
        const docs=[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent));
        const nodes=docs.flatMap(d=>d['@graph']||[d]);return nodes.find(n=>n['@type']==='Person');
      });
      assert.equal(person?.name,'David Porto Díaz',`${name}: Person schema pierde nombre`);
      assert.equal(person?.award?.length,2,`${name}: Person schema debe conservar exactamente dos reconocimientos`);

      const overflow=await noOverflow(p,name);
      const masthead=await style(p.locator('.v1-masthead'));
      const title=await style(p.locator('.v1-masthead h1'));
      const sectionHead=await style(p.locator('#reconocimientos .v1-section__head'));
      const recognitionHeading=await style(p.locator('#reconocimientos .v1-section__head h2'));
      const ledger=await style(p.locator('#reconocimientos .awards-ledger'));
      const firstRecord=await style(records.nth(0));
      const secondRecord=await style(records.nth(1));
      const firstResult=await style(records.nth(0).locator('[data-award-result]'));
      const secondResult=await style(records.nth(1).locator('[data-award-result]'));
      const attribution=await style(records.nth(0).locator('.award-attribution'));
      const sourceRail=await style(records.nth(0).locator('.award-source-rail'));
      const trajectory=await style(p.locator('#colaboraciones .awards-ledger'));
      const reception=await style(p.locator('#recepcion .awards-ledger'));
      const receptionHeading=await style(p.locator('#recepcion .v1-section__head h2'));
      const next=await style(p.locator('#conocer .awards-next'));
      const activeContext=await style(p.locator('.section-context [aria-current="page"]'));
      const footer=await style(p.locator('.site-footer'));

      const expectedAttribution=width>760?4:(width>600?2:1);
      const expectedSource=width>600?2:1;
      const expectedHead=width>600?2:1;
      assert.equal(columns(attribution.gridTemplateColumns),expectedAttribution,`${name}: seam 761/760/601/600 de atribución cambió`);
      assert.equal(columns(sourceRail.gridTemplateColumns),expectedSource,`${name}: seam 601/600 de fuentes cambió`);
      assert.equal(columns(sectionHead.gridTemplateColumns),expectedHead,`${name}: seam 601/600 de cabecera cambió`);
      assert.equal(masthead.display,'block',`${name}: masthead vuelve a plantilla genérica de dos columnas`);
      assert.equal(title.color,'rgb(29, 79, 150)',`${name}: H1 pierde azul canónico`);
      assert.notEqual(firstRecord.backgroundImage,'none',`${name}: Primer Premio pierde tratamiento documental destacado`);
      assert.notEqual(firstRecord.boxShadow,'none',`${name}: Primer Premio pierde filete jerárquico`);
      assert.ok(parseFloat(firstResult.fontSize)>parseFloat(secondResult.fontSize),`${name}: Primer Premio deja de tener jerarquía tipográfica sobre el Top 10`);
      assert.equal(sourceRail.borderTopWidth,'2px',`${name}: procedencia pierde rail de evidencia`);
      assert.notEqual(receptionHeading.color,recognitionHeading.color,`${name}: Recepción vuelve a tener el mismo peso cromático que Reconocimientos`);

      measurements.push({name,width,height,overflow,masthead,title,sectionHead,recognitionHeading,ledger,firstRecord,secondRecord,firstResult,secondResult,attribution,sourceRail,trajectory,reception,receptionHeading,next,activeContext,footer});
      await p.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:path.join(OUT,`premios-${name}.png`),fullPage:true});
    }catch(error){failures.push({viewport:name,width,height,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  for(const route of ['/autor.html','/eventos.html','/prensa.html']){
    const c=await context(browser,{width:1440,height:1000});const p=await c.newPage();
    try{
      const r=await p.goto(ORIGIN+route,{waitUntil:'networkidle'});assert.ok(r?.ok(),`${route}: control de aislamiento no carga`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${route}: familia identity perdida`);
      assert.notEqual(await p.locator('main#contenido').getAttribute('data-page'),'awards',`${route}: scope awards contamina una página hermana`);
      assert.equal(await p.locator('link[href="/assets/v1-awards.css"]').count(),0,`${route}: hoja local de Premios cargada fuera de su página`);
      assert.equal(await p.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--awards-blue').trim()),'',`${route}: tokens visuales de Premios contaminan una página hermana`);
      await noOverflow(p,`${route} isolation`);
      await p.screenshot({path:path.join(OUT,`isolation-${route.slice(1,-5)}-1440.png`),fullPage:true});
    }catch(error){failures.push({viewport:`isolation-${route}`,width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900},false);const p=await c.newPage();
    try{
      const r=await p.goto(`${ORIGIN}/premios.html`,{waitUntil:'load'});assert.ok(r?.ok(),'no-js: Premios no carga');
      assert.equal(await p.locator('#reconocimientos [data-award-record]').count(),2,'no-js: reconocimientos ausentes');
      assert.equal(await p.locator('#colaboraciones .awards-ledger > li').count(),3,'no-js: trayectoria ausente');
      assert.equal(await p.locator('#recepcion .awards-ledger > li').count(),1,'no-js: recepción ausente');
      await noOverflow(p,'no-js 390');await p.screenshot({path:path.join(OUT,'premios-no-js-390.png'),fullPage:true});
    }catch(error){failures.push({viewport:'no-js-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const p=await c.newPage();
    try{
      await p.goto(`${ORIGIN}/premios.html`,{waitUntil:'networkidle'});
      await inspectorStyles(c,p,'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');
      await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await noOverflow(p,'text spacing');
      await p.evaluate(()=>document.documentElement.style.zoom='2');await noOverflow(p,'zoom 200%');
      await p.keyboard.press('Tab');assert.notEqual(await p.evaluate(()=>document.activeElement?.tagName),'BODY','keyboard: foco no avanza');
    }catch(error){failures.push({viewport:'wcag-stress-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'premios-design-report.json'),JSON.stringify({route:'/premios.html',phase:'visual-system-contract',viewports:viewports.length,measurements,failures},null,2));
assert.deepEqual(failures,[],`Premios visual-system failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Premios visual system: PASS (${viewports.length} viewports + 3 isolation controls + no-JS + WCAG stress)`);
