import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/prensa-design';
fs.mkdirSync(OUT, { recursive: true });

const viewports = [
  ['wide-1728',1728,1050],['desktop-1440',1440,1000],['desktop-1280',1280,900],['tablet-1024',1024,900],
  ['press-901',901,900],['press-900',900,900],['entry-768',768,1024],['facts-701',701,950],['facts-700',700,950],
  ['head-601',601,950],['head-600',600,950],['hero-411',411,900],['hero-410',410,900],['mobile-390',390,900],['mobile-320',320,900],
];
const typographyRequests=[
  ['400 64px "Instrument Serif"','Kit de prensa Ficha técnica Apariciones recientes'],
  ['400 18px "Newsreader"','Todo lo que necesitas para hablar de David Porto Díaz'],
  ['600 16px "Manrope"','Medios Reseñas Librerías Disponible Contacto prensa'],
];

function columns(value){
  if(!value || value === 'none') return 0;
  return value.trim().split(/\s+/).length;
}
async function context(browser,{width,height},js=true){
  const c=await browser.newContext({viewport:{width,height},javaScriptEnabled:js,reducedMotion:'reduce'});
  if(js) await c.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()))}catch{}});
  return c;
}
async function ensureTypographyLoaded(page,label){
  const state=await page.evaluate(async requested=>{
    if(!document.fonts) return {supported:false,loaded:true};
    await Promise.all(requested.map(([font,text])=>document.fonts.load(font,text)));
    await document.fonts.ready;
    return {supported:true,loaded:requested.every(([font,text])=>document.fonts.check(font,text))};
  },typographyRequests);
  assert.ok(!state.supported||state.loaded,`${label}: tipografías de Prensa no cargadas`);
  return state;
}
async function settleTypography(page,label){
  const fontState=await ensureTypographyLoaded(page,label);
  const state=await page.evaluate(async()=>{
    const waitFrames=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    const geometry=()=>{
      const title=document.querySelector('.v1-masthead h1');
      const reading=document.querySelector('.v1-masthead__lead');
      const fact=document.querySelector('#datos-rapidos .trust-item p');
      const read=el=>{
        if(!(el instanceof HTMLElement)) return null;
        const s=getComputedStyle(el);const r=el.getBoundingClientRect();
        return {width:r.width,height:r.height,fontFamily:s.fontFamily,fontSize:s.fontSize,lineHeight:s.lineHeight,maxWidth:s.maxWidth};
      };
      return {title:read(title),reading:read(reading),fact:read(fact)};
    };
    await waitFrames();
    const before=geometry();
    await new Promise(resolve=>setTimeout(resolve,80));
    await waitFrames();
    const after=geometry();
    return {before,after};
  });
  const result={...fontState,...state};
  if(result.before&&result.after){
    for(const key of ['title','reading','fact']){
      const before=result.before[key],after=result.after[key];
      if(!before||!after) continue;
      assert.ok(Math.abs(after.width-before.width)<=0.1,`${label}: ancho de ${key} inestable antes de medir`);
      assert.ok(Math.abs(after.height-before.height)<=0.1,`${label}: alto de ${key} inestable antes de medir`);
      assert.equal(after.fontFamily,before.fontFamily,`${label}: font-family de ${key} cambia antes de medir`);
      assert.equal(after.fontSize,before.fontSize,`${label}: font-size de ${key} cambia antes de medir`);
      assert.equal(after.lineHeight,before.lineHeight,`${label}: line-height de ${key} cambia antes de medir`);
      assert.equal(after.maxWidth,before.maxWidth,`${label}: max-width de ${key} cambia antes de medir`);
    }
  }
  return result;
}
async function open(page,label='Prensa'){
  const r=await page.goto(`${ORIGIN}/prensa.html`,{waitUntil:'load',timeout:20000});
  assert.ok(r?.ok(),'Prensa no carga');
  await ensureTypographyLoaded(page,`${label} warmup`);
  const reloaded=await page.reload({waitUntil:'load',timeout:20000});
  assert.ok(reloaded?.ok(),`${label}: Prensa no recarga tras calentar tipografías`);
  return settleTypography(page,label);
}
async function overflowState(page){
  return page.evaluate(()=>({
    viewport:document.documentElement.clientWidth,
    scroll:document.documentElement.scrollWidth,
    overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
  }));
}
async function noOverflow(page,label){
  const state=await overflowState(page);
  assert.ok(state.overflow<=1,`${label}: overflow horizontal ${state.overflow}px (${state.scroll}/${state.viewport})`);
  return state.overflow;
}
async function loadDocumentaryImages(page){
  const selectors=[
    '.press-author-photo img',
    '.event-photo-grid img',
    '#ficha-manecillas img',
    '#ficha img',
  ];
  for(const selector of selectors){
    const images=page.locator(selector);
    for(let i=0;i<await images.count();i++){
      const image=images.nth(i);
      await image.scrollIntoViewIfNeeded();
      await image.evaluate(async img=>{
        if(!img.complete) await new Promise((resolve,reject)=>{img.addEventListener('load',resolve,{once:true});img.addEventListener('error',reject,{once:true});});
        if(img.decode){try{await img.decode();}catch{}}
      });
      const natural=await image.evaluate(img=>({w:img.naturalWidth,h:img.naturalHeight}));
      assert.ok(natural.w>0&&natural.h>0,`${selector}[${i}] no decodifica`);
    }
  }
}
async function addTextSpacing(context,page){
  const cdp=await context.newCDPSession(page);
  await cdp.send('Page.enable');await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  const {frameTree}=await cdp.send('Page.getFrameTree');
  const {styleSheetId}=await cdp.send('CSS.createStyleSheet',{frameId:frameTree.frame.id});
  await cdp.send('CSS.setStyleSheetText',{styleSheetId,text:'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'});
}

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const failures=[],measurements=[];
try{
  for(const [name,width,height] of viewports){
    const c=await context(browser,{width,height});
    const page=await c.newPage();
    try{
      const typographyState=await open(page,name);
      assert.equal(await page.locator('html').getAttribute('data-editorial-context'),'prensa',`${name}: contexto prensa perdido`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'),'identity',`${name}: familia identity alterada`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-page'),'press',`${name}: owner local de Prensa no está activado`);
      assert.equal(await page.locator('link[rel="stylesheet"][href="/assets/v1-press.css"]').count(),1,`${name}: stylesheet owner v1-press.css ausente o duplicado`);
      assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'),'https://davidportodiaz.com/prensa.html',`${name}: canonical alterado`);
      assert.equal(await page.locator('h1').count(),1,`${name}: H1 no único`);
      assert.equal((await page.locator('h1').textContent()).trim(),'Kit de prensa',`${name}: H1 alterado`);
      assert.equal(await page.locator('.section-context [aria-current="page"]').getAttribute('href'),'/prensa.html',`${name}: navegación contextual no marca Prensa`);

      const ids=['datos-rapidos','bios','ficha-manecillas','ficha','sinopsis','entrevistas','bookbloggers','charlas','cobertura','contacto'];
      for(const id of ids) assert.equal(await page.locator(`#${id}`).count(),1,`${name}: falta #${id}`);
      const order=await page.evaluate(ids=>ids.map(id=>document.getElementById(id)?.getBoundingClientRect().top ?? null),ids);
      assert.ok(order.every(Number.isFinite),`${name}: estructura editorial incompleta`);
      assert.ok(order.every((v,i)=>i===0||v>order[i-1]),`${name}: orden de secciones alterado`);

      assert.equal(await page.locator('#datos-rapidos .trust-item').count(),6,`${name}: datos rápidos deben conservar 6 registros`);
      assert.equal(await page.locator('#bios .press-card').count(),4,`${name}: bios/materiales deben conservar 4 registros`);
      assert.equal(await page.locator('#sinopsis .press-card').count(),3,`${name}: sinopsis debe conservar 3 registros`);
      assert.equal(await page.locator('#entrevistas details').count(),5,`${name}: entrevistas debe conservar 5 preguntas`);
      assert.equal(await page.locator('#bookbloggers .id-card').count(),3,`${name}: recursos para creadores deben conservar 3 entradas`);
      assert.equal(await page.locator('#charlas .id-card').count(),3,`${name}: charlas deben conservar 3 formatos`);
      assert.ok(await page.locator('.copy-btn').count()>=4,`${name}: faltan controles de copia`);

      assert.equal(await page.locator('.press-author-photo img').getAttribute('src'),'/assets/david-porto-diaz-retrato-editorial-prensa.webp',`${name}: retrato editorial sustituido`);
      assert.equal(await page.locator('.event-photo-grid img').count(),3,`${name}: galería documental debe conservar 3 imágenes`);
      assert.equal(await page.locator('#ficha-manecillas img').getAttribute('src'),'/assets/manecillas-book-mockup.webp',`${name}: mockup de Manecillas alterado`);
      assert.equal(await page.locator('#ficha img').getAttribute('src'),'/assets/samuel_entre_mundos_3d.webp',`${name}: mockup de Samuel alterado`);
      assert.ok((await page.locator('#ficha-manecillas').innerText()).includes('979-8-90514-935-1'),`${name}: ISBN Manecillas ausente`);
      assert.ok((await page.locator('#ficha').innerText()).includes('9791387659776'),`${name}: ISBN Samuel ausente`);
      assert.ok((await page.locator('#contacto').innerText()).includes('davidportodiaz@gmail.com'),`${name}: contacto de prensa ausente`);

      const schema=await page.evaluate(()=>{
        const docs=[...document.querySelectorAll('script[type="application/ld+json"]')].map(s=>JSON.parse(s.textContent));
        const nodes=docs.flatMap(d=>d['@graph']||[d]);
        return nodes.map(n=>({type:n['@type'],id:n['@id']||null,url:n.url||null}));
      });
      assert.ok(schema.some(n=>n.type==='WebPage'&&n.url==='https://davidportodiaz.com/prensa.html'),`${name}: WebPage schema de Prensa ausente`);

      const pressCardColumns=await page.locator('#bios .press-card').first().evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      assert.equal(columns(pressCardColumns),width>900?2:1,`${name}: seam 901/900 de press-card cambió (${pressCardColumns})`);
      const photoColumns=await page.locator('.event-photo-grid').evaluate(el=>getComputedStyle(el).gridTemplateColumns);
      assert.equal(columns(photoColumns),width>900?3:(width>600?2:1),`${name}: seam de galería 901/900 o 601/600 cambió (${photoColumns})`);
      for(const id of ['ficha-manecillas','ficha']){
        const factColumns=await page.locator(`#${id} > div[style*="grid-template-columns"]`).evaluate(el=>getComputedStyle(el).gridTemplateColumns);
        assert.equal(columns(factColumns),width>700?2:1,`${name}: seam 701/700 de ${id} cambió (${factColumns})`);
      }

      const overflow=await noOverflow(page,name);
      const state=await page.evaluate(()=>({
        titleColor:getComputedStyle(document.querySelector('.v1-masthead h1')).color,
        pressCardColumns:getComputedStyle(document.querySelector('#bios .press-card')).gridTemplateColumns,
        factManecillas:getComputedStyle(document.querySelector('#ficha-manecillas > div[style*="grid-template-columns"]')).gridTemplateColumns,
        galleryColumns:getComputedStyle(document.querySelector('.event-photo-grid')).gridTemplateColumns,
        inlineStyles:document.querySelectorAll('main [style]').length,
      }));
      assert.equal(state.titleColor,'rgb(29, 79, 150)',`${name}: owner visual de Prensa no controla el H1 (${state.titleColor})`);
      measurements.push({name,width,height,overflow,typographyState,...state});
      await loadDocumentaryImages(page);
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(OUT,`prensa-${name}.png`),fullPage:true});
    }catch(error){
      failures.push({viewport:name,width,height,error:error instanceof Error?error.message:String(error)});
    }finally{await c.close();}
  }

  for(const route of ['/autor.html','/premios.html','/eventos.html']){
    const c=await context(browser,{width:1440,height:1000});const page=await c.newPage();
    try{
      const r=await page.goto(ORIGIN+route,{waitUntil:'load'});assert.ok(r?.ok(),`${route}: aislamiento no carga`);
      assert.equal(await page.locator('main#contenido').getAttribute('data-family'),'identity',`${route}: familia identity perdida`);
      await noOverflow(page,`${route} isolation`);
      await page.screenshot({path:path.join(OUT,`isolation-${route.slice(1,-5)}-1440.png`),fullPage:true});
    }catch(error){failures.push({viewport:`isolation-${route}`,width:1440,height:1000,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900},false);const page=await c.newPage();
    try{
      const r=await page.goto(`${ORIGIN}/prensa.html`,{waitUntil:'load'});assert.ok(r?.ok(),'no-js: Prensa no carga');
      assert.equal(await page.locator('#bios .press-card').count(),4,'no-js: bios/materiales incompletos');
      assert.equal(await page.locator('#entrevistas details').count(),5,'no-js: entrevistas incompletas');
      assert.ok((await page.locator('#contacto').innerText()).includes('davidportodiaz@gmail.com'),'no-js: contacto ausente');
      await noOverflow(page,'no-js 390');
      await page.screenshot({path:path.join(OUT,'prensa-no-js-390.png'),fullPage:true});
    }catch(error){failures.push({viewport:'no-js-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const page=await c.newPage();
    try{
      await open(page,'text spacing precondition');await addTextSpacing(c,page);
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      await noOverflow(page,'text spacing');
      await page.keyboard.press('Tab');
      assert.notEqual(await page.evaluate(()=>document.activeElement?.tagName),'BODY','keyboard: foco no avanza');
    }catch(error){failures.push({viewport:'text-spacing-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }

  {
    const c=await context(browser,{width:390,height:900});const page=await c.newPage();
    try{
      await open(page,'zoom precondition');
      await page.evaluate(()=>document.documentElement.style.zoom='2');
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      await noOverflow(page,'zoom 200%');
    }catch(error){failures.push({viewport:'zoom-200-390',width:390,height:900,error:error instanceof Error?error.message:String(error)});}finally{await c.close();}
  }
}finally{await browser.close();}

fs.writeFileSync(path.join(OUT,'prensa-design-report.json'),JSON.stringify({route:'/prensa.html',phase:'visual-system-contract',viewports:viewports.length,measurements,failures},null,2));
assert.deepEqual(failures,[],`Prensa visual-system contract failures:\n${JSON.stringify(failures,null,2)}`);
console.log(`Prensa visual-system contract: PASS (${viewports.length} viewports + 3 isolation controls + no-JS + separated WCAG stress)`);
