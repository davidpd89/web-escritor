import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/eventos-design';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728',1728,1050],['desktop-1440',1440,1000],['desktop-1280',1280,900],['tablet-1024',1024,900],
  ['identity-901',901,900],['identity-900',900,900],['entry-768',768,1024],['entry-767',767,1024],
  ['head-601',601,950],['head-600',600,950],['hero-411',411,900],['hero-410',410,900],['mobile-390',390,900],['mobile-360',360,900],['mobile-320',320,900],
];

const BLUE='rgb(29, 79, 150)';
const BLUE_DEEP='rgb(13, 44, 87)';
const GOLD_TEXT='rgb(149, 105, 0)';

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
      borderLeftWidth:s.borderLeftWidth,borderRadius:s.borderRadius,fontFamily:s.fontFamily,fontSize:s.fontSize,
      lineHeight:s.lineHeight,position:s.position,maxWidth:s.maxWidth,width:r.width,height:r.height,left:r.left,top:r.top,
    };
  });
}
async function pseudoStyle(locator,pseudo='::before'){
  return locator.evaluate((el,pseudoName)=>{
    const s=getComputedStyle(el,pseudoName);
    return {content:s.content,width:s.width,height:s.height,backgroundColor:s.backgroundColor,display:s.display,position:s.position};
  },pseudo);
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
async function overflowState(p){
  return p.evaluate(()=>{
    const viewportWidth=document.documentElement.clientWidth;
    const overflow=document.documentElement.scrollWidth-viewportWidth;
    const offenders=[...document.body.querySelectorAll('*')].map(el=>{
      const r=el.getBoundingClientRect(),s=getComputedStyle(el);
      return {tag:el.tagName.toLowerCase(),id:el.id||'',className:typeof el.className==='string'?el.className:'',text:(el.textContent||'').trim().replace(/\s+/g,' ').slice(0,70),left:+r.left.toFixed(1),right:+r.right.toFixed(1),width:+r.width.toFixed(1),scrollWidth:el.scrollWidth,clientWidth:el.clientWidth,display:s.display,overflowX:s.overflowX};
    }).filter(x=>x.display!=='none'&&(x.right>viewportWidth+1||x.left< -1||x.scrollWidth>x.clientWidth+1)).slice(0,12);
    return {overflow,offenders};
  });
}
async function noOverflow(p,label){
  const state=await overflowState(p);
  assert.ok(state.overflow<=1,`${label}: overflow ${state.overflow}px; offenders=${JSON.stringify(state.offenders)}`);return state.overflow;
}
async function open(page){
  const r=await page.goto(`${ORIGIN}/eventos.html`,{waitUntil:'networkidle',timeout:20000});
  assert.ok(r?.ok(),'Eventos no carga');
  await page.evaluate(()=>document.fonts?.ready);await page.waitForTimeout(100);
}
async function loadDocumentaryPhoto(page){
  const photo=page.locator('#feria-libro-madrid-2026 img');
  await photo.scrollIntoViewIfNeeded();
  await photo.evaluate(async img=>{
    if(!img.complete) await new Promise((resolve,reject)=>{img.addEventListener('load',resolve,{once:true});img.addEventListener('error',reject,{once:true});});
    if(img.decode){try{await img.decode();}catch{}}
  });
  const natural=await photo.evaluate(img=>({width:img.naturalWidth,height:img.naturalHeight}));
  assert.ok(natural.width>0&&natural.height>0,`foto documental no decodifica (${natural.width}x${natural.height})`);
}

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[],measurements=[];
try{
  for(const [name,width,height] of viewports){
    const c=await context(browser,{width,height});const p=await c.newPage();
    try{
      await open(p);
      assert.equal(await p.locator('html').getAttribute('data-editorial-context'),'prensa',`${name}: contexto prensa/agenda perdido`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${name}: familia identity alterada`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-page'),'events',`${name}: scope estático events perdido`);
      assert.equal(await p.locator('link[href^="/assets/v1-events.css"]').count(),1,`${name}: owner CSS de Eventos ausente o duplicado`);
      assert.equal(await p.locator('link[rel="canonical"]').getAttribute('href'),'https://davidportodiaz.com/eventos.html',`${name}: canonical alterado`);
      assert.equal(await p.locator('h1').count(),1,`${name}: H1 no único`);
      assert.equal((await p.locator('h1').textContent()).trim(),'Eventos',`${name}: H1 alterado`);
      assert.equal(await p.locator('.section-context [aria-current="page"]').getAttribute('href'),'/eventos.html',`${name}: navegación contextual no marca Eventos`);

      const upcoming=p.locator('#proximos');
      const archive=p.locator('#pasados');
      const milestone=p.locator('#hitos-editoriales');
      const organize=p.locator('#organizar');
      assert.equal(await upcoming.count(),1,`${name}: falta agenda futura`);
      assert.equal(await archive.count(),1,`${name}: falta archivo`);
      assert.equal(await milestone.count(),1,`${name}: falta hito editorial`);
      assert.equal(await organize.count(),1,`${name}: falta bloque organizar`);
      assert.ok((await upcoming.innerText()).includes('Ahora mismo no hay una próxima fecha publicada.'),`${name}: estado vacío alterado`);
      assert.equal(await archive.locator('.event-entry').count(),4,`${name}: archivo debe conservar 4 entradas`);
      assert.equal(await milestone.locator('.event-entry').count(),1,`${name}: publicaciones debe conservar 1 hito`);
      assert.equal(await organize.locator('.contact-card').count(),3,`${name}: organizar debe conservar 3 vías`);
      assert.equal(await archive.locator('figure img').count(),1,`${name}: foto documental de Madrid ausente o duplicada`);
      assert.equal(await archive.locator('#feria-libro-madrid-2026 img').getAttribute('src'),'/assets/eventos/david-porto-diaz-feria-libro-madrid-2026-caseta-337.webp',`${name}: foto documental sustituida`);

      const schema=await p.evaluate(()=>{
        const docs=[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent));
        const nodes=docs.flatMap(d=>d['@graph']||[d]);
        return nodes.filter(n=>n['@type']==='Event').map(e=>({id:e['@id'],status:e.eventStatus,start:e.startDate,name:e.name}));
      });
      assert.equal(schema.length,2,`${name}: deben existir exactamente 2 Event schema`);
      assert.ok(schema.every(e=>e.status==='https://schema.org/EventCompleted'),`${name}: se perdió EventCompleted`);

      const order=await p.evaluate(()=>{
        const ids=['proximos','pasados','hitos-editoriales','organizar'];
        return ids.map(id=>document.getElementById(id)?.getBoundingClientRect().top ?? null);
      });
      assert.ok(order.every(v=>Number.isFinite(v)),`${name}: falta una sección estructural`);
      assert.ok(order[0]<order[1]&&order[1]<order[2]&&order[2]<order[3],`${name}: orden agenda→archivo→hito→organizar alterado`);

      const overflow=await noOverflow(p,name);
      const masthead=await style(p.locator('.v1-masthead'));
      const title=await style(p.locator('.v1-masthead h1'));
      const futureHead=await style(upcoming.locator('.v1-section__head'));
      const empty=await style(upcoming.locator('.event-empty'));
      const emptyTitle=await style(upcoming.locator('.event-empty__title'));
      const year=await style(archive.locator('.event-year'));
      const yearLabel=await style(archive.locator('.event-year > h3'));
      const firstEntry=await style(archive.locator('.event-entry').first());
      const archiveList=await style(archive.locator('.event-list'));
      const madridBody=await style(p.locator('#feria-libro-madrid-2026 > div'));
      const milestoneList=await style(milestone.locator('.event-list'));
      const milestoneTime=await style(milestone.locator('.event-entry time'));
      const contacts=await style(organize.locator('.contact-grid'));
      const featuredRail=await pseudoStyle(organize.locator('.contact-card--featured'));
      const activeContext=await style(p.locator('.section-context [aria-current="page"]'));
      const footer=await style(p.locator('.site-footer'));

      const expectedEntry=width>767?2:1;
      const expectedHead=width>600?2:1;
      const expectedMadridBody=width>900?2:1;
      assert.equal(columns(firstEntry.gridTemplateColumns),expectedEntry,`${name}: seam 768/767 de entrada cambió`);
      assert.equal(columns(futureHead.gridTemplateColumns),expectedHead,`${name}: seam 601/600 de cabecera cambió`);
      assert.equal(columns(madridBody.gridTemplateColumns),expectedMadridBody,`${name}: seam 901/900 de composición documental de Madrid cambió`);
      if(width>900) assert.equal(yearLabel.position,'sticky',`${name}: año de archivo perdió sticky desktop`);
      if(width<=900) assert.equal(yearLabel.position,'static',`${name}: año de archivo no libera sticky en tablet/móvil`);

      // Contrato visual: proteger jerarquía, no geometría accidental.
      assert.equal(title.color,BLUE,`${name}: H1 perdió el azul editorial`);
      assert.equal(masthead.borderBottomWidth,'2px',`${name}: masthead perdió la regla principal`);
      assert.notEqual(empty.backgroundImage,'none',`${name}: estado futuro perdió su fondo editorial`);
      assert.equal(emptyTitle.color,BLUE_DEEP,`${name}: estado futuro perdió jerarquía azul`);
      assert.equal(archiveList.borderTopWidth,'2px',`${name}: archivo perdió la regla cronológica fuerte`);
      assert.equal(yearLabel.color,BLUE,`${name}: año del archivo perdió la jerarquía azul`);
      assert.equal(milestoneList.borderTopWidth,'1px',`${name}: hito editorial dejó de ser secundario respecto al archivo`);
      assert.equal(milestoneTime.color,GOLD_TEXT,`${name}: hito editorial perdió su código dorado`);
      assert.equal(contacts.borderTopWidth,'2px',`${name}: directorio de contacto perdió su regla de entrada`);
      assert.equal(featuredRail.width,'2px',`${name}: contacto principal perdió su rail editorial`);
      assert.equal(featuredRail.backgroundColor,BLUE,`${name}: contacto principal perdió el acento azul`);

      measurements.push({name,width,height,overflow,masthead,title,futureHead,empty,emptyTitle,year,yearLabel,firstEntry,archiveList,madridBody,milestoneList,milestoneTime,contacts,featuredRail,activeContext,footer});
      await loadDocumentaryPhoto(p);
      await p.evaluate(()=>window.scrollTo(0,0));
      await p.screenshot({path:path.join(OUT,`eventos-${name}.png`),fullPage:true});
    }catch(error){failures.push({viewport:name,width,height,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  for(const route of ['/autor.html','/premios.html','/prensa.html']){
    const c=await context(browser,{width:1440,height:1000});const p=await c.newPage();
    try{
      const r=await p.goto(ORIGIN+route,{waitUntil:'networkidle'});assert.ok(r?.ok(),`${route}: control de aislamiento no carga`);
      assert.equal(await p.locator('main#contenido').getAttribute('data-family'),'identity',`${route}: familia identity perdida`);
      assert.notEqual(await p.locator('main#contenido').getAttribute('data-page'),'events',`${route}: scope events contamina una página hermana`);
      assert.equal(await p.locator('link[href^="/assets/v1-events.css"]').count(),0,`${route}: owner CSS de Eventos cargado fuera de su página`);
      await noOverflow(p,`${route} isolation`);
      await p.screenshot({path:path.join(OUT,`isolation-${route.slice(1,-5)}-1440.png`),fullPage:true});
    }catch(error){failures.push({viewport:`isolation-${route}`,width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900},false);const p=await c.newPage();
    try{
      const r=await p.goto(`${ORIGIN}/eventos.html`,{waitUntil:'load'});assert.ok(r?.ok(),'no-js: Eventos no carga');
      assert.equal(await p.locator('main#contenido').getAttribute('data-page'),'events','no-js: scope events ausente');
      assert.equal(await p.locator('#pasados .event-entry').count(),4,'no-js: archivo incompleto');
      assert.equal(await p.locator('#hitos-editoriales .event-entry').count(),1,'no-js: hito editorial ausente');
      assert.equal(await p.locator('#organizar .contact-card').count(),3,'no-js: vías de contacto ausentes');
      await noOverflow(p,'no-js 390');await p.screenshot({path:path.join(OUT,'eventos-no-js-390.png'),fullPage:true});
    }catch(error){failures.push({viewport:'no-js-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const p=await c.newPage();
    try{
      await open(p);
      await inspectorStyles(c,p,'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');
      await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      await noOverflow(p,'text spacing');
      await p.keyboard.press('Tab');assert.notEqual(await p.evaluate(()=>document.activeElement?.tagName),'BODY','keyboard: foco no avanza');
    }catch(error){failures.push({viewport:'text-spacing-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const p=await c.newPage();
    try{
      await open(p);
      await p.evaluate(()=>document.documentElement.style.zoom='2');
      await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      await noOverflow(p,'zoom 200%');
    }catch(error){failures.push({viewport:'zoom-200-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'eventos-design-report.json'),JSON.stringify({route:'/eventos.html',phase:'visual-system-contract',viewports:viewports.length,measurements,failures},null,2));
assert.deepEqual(failures,[],`Eventos visual-system-contract failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Eventos visual-system contract: PASS (${viewports.length} viewports + 3 isolation controls + no-JS + separated WCAG stress)`);
