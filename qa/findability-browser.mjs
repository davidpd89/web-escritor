import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const OUT=process.env.QA_OUT||'qa-artifacts';
fs.mkdirSync(OUT,{recursive:true});
const pages=[
  {key:'start',url:'/empieza-aqui/',file:'empieza-aqui/index.html'},
  {key:'map',url:'/mapa-del-sitio/',file:'mapa-del-sitio/index.html'},
  {key:'404',url:'/404.html',file:'404.html'},
];
const viewports=[
  {name:'320',width:320,height:900},{name:'390',width:390,height:900},{name:'768',width:768,height:1000},
  {name:'1024',width:1024,height:900},{name:'1440',width:1440,height:1000},{name:'1728',width:1728,height:1000},
  {name:'landscape',width:844,height:390},
];
const registryRaw=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defaults=registryRaw.defaults||{};
const registry=new Map(registryRaw.entries.map(e=>[e.url,{...defaults,...e}]));

const cleanHref=h=>String(h||'').trim();
function localTarget(href){
  const h=cleanHref(href);
  if(!h||h.startsWith('#')||/^(?:https?:|mailto:|tel:|javascript:|data:)/i.test(h))return null;
  const u=new URL(h,ORIGIN);
  if(u.origin!==ORIGIN)return null;
  return {pathname:decodeURIComponent(u.pathname),hash:decodeURIComponent(u.hash.slice(1))};
}
function fileFor(pathname){
  if(pathname==='/')return 'index.html';
  const p=pathname.replace(/^\//,'');
  if(pathname.endsWith('/'))return path.join(p,'index.html');
  return p;
}
function validateInternalLinks(){
  const findings=[];
  for(const page of pages){
    const html=fs.readFileSync(page.file,'utf8');
    const hrefs=[...html.matchAll(/<a\b[^>]*href=["']([^"']+)["']/gi)].map(m=>m[1]);
    for(const href of hrefs){
      const target=localTarget(href); if(!target)continue;
      const file=fileFor(target.pathname);
      assert(fs.existsSync(file),`${page.file}: destino interno inexistente ${href} -> ${file}`);
      if(target.hash){
        const targetHtml=fs.readFileSync(file,'utf8');
        const escaped=target.hash.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
        assert(new RegExp(`\\bid=["']${escaped}["']`,'i').test(targetHtml),`${page.file}: anchor inexistente ${href}`);
      }
    }
    findings.push({page:page.key,count:hrefs.length});
  }
  return findings;
}
function validateExternalLinks(){
  const report=[];
  for(const page of pages){
    const html=fs.readFileSync(page.file,'utf8');
    for(const m of html.matchAll(/<a\b([^>]*)href=["'](https?:\/\/[^"']+)["']([^>]*)>/gi)){
      const attrs=`${m[1]} ${m[3]}`, href=m[2];
      assert.doesNotThrow(()=>new URL(href),`${page.file}: URL externa inválida ${href}`);
      assert(!/[?&]utm_(?:source|medium|campaign|term|content)=/i.test(href),`${page.file}: tracking nuevo ${href}`);
      if(/target=["']_blank["']/i.test(attrs))assert(/rel=["'][^"']*(?:noopener|noreferrer)/i.test(attrs),`${page.file}: target blank sin rel seguro ${href}`);
      report.push({page:page.key,href});
    }
  }
  return report;
}
async function noOverflow(page,label){
  const m=await page.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,bw:document.body.scrollWidth}));
  assert(m.sw<=m.cw+1,`${label}: overflow document ${JSON.stringify(m)}`);
  assert(m.bw<=m.cw+1,`${label}: overflow body ${JSON.stringify(m)}`);
}
async function assertStructure(page,key){
  assert.equal(await page.locator('h1').count(),1,`${key}: debe existir un único H1`);
  assert.equal(await page.locator('main').count(),1,`${key}: main`);
  assert.equal(await page.locator('header.site-header').count(),1,`${key}: header`);
  assert.equal(await page.locator('footer.site-footer').count(),1,`${key}: footer`);
  const navs=page.locator('nav');
  for(let i=0;i<await navs.count();i++)assert((await navs.nth(i).getAttribute('aria-label'))||await navs.nth(i).locator('h2').count(),`${key}: nav sin nombre accesible`);
  const headings=await page.locator('h1,h2,h3').evaluateAll(nodes=>nodes.map(n=>({level:Number(n.tagName[1]),text:n.textContent.trim()})));
  let prev=1; for(const h of headings){assert(h.text,`${key}: heading vacío`);assert(h.level<=prev+1,`${key}: salto de heading H${prev}->H${h.level}`);prev=h.level;}
  const links=page.locator('a[href]'); for(let i=0;i<await links.count();i++)assert((await links.nth(i).innerText()).trim()||await links.nth(i).getAttribute('aria-label'),`${key}: enlace sin propósito textual`);
}
async function checkTouchTargets(page,key){
  const targets=page.locator('.findability-links a,.directory-list a,.findability-primary,.findability-plain-list a');
  for(let i=0;i<await targets.count();i++){
    if(!await targets.nth(i).isVisible())continue;
    const box=await targets.nth(i).boundingBox();
    assert(box&&box.height>=40,`${key}: target <40px: ${(await targets.nth(i).innerText()).trim()} ${box?.height}`);
  }
}
async function checkFocus(page,key){
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(()=>document.activeElement?.classList.contains('skip-link')),true,`${key}: el primer Tab no llega al skip link`);
  let reached=false,visible=false;
  for(let i=0;i<40;i++){
    await page.keyboard.press('Tab');
    // The focus ring resolves through a transition (shortened, not removed,
    // under prefers-reduced-motion), so a synchronous read right after Tab
    // returns the transition's start value (outline-width 0) even though the
    // ring is painted on the very next frame. Settle a frame before measuring.
    const s=await page.evaluate(()=>new Promise(resolve=>{
      requestAnimationFrame(()=>requestAnimationFrame(()=>{
        const e=document.activeElement; if(!(e instanceof HTMLElement))return resolve(null);
        if(!e.matches('[data-family="findability"] .findability-links a,[data-family="findability"] .directory-list a,[data-family="findability"] .findability-primary,[data-family="findability"] .findability-plain-list a'))return resolve({target:false});
        const c=getComputedStyle(e);resolve({target:true,outline:c.outlineStyle!=='none'&&parseFloat(c.outlineWidth)>0,shadow:c.boxShadow!=='none'});
      }));
    }));
    if(s?.target){reached=true;visible=s.outline||s.shadow;break;}
  }
  assert(reached,`${key}: teclado no alcanza enlaces principales`);assert(visible,`${key}: foco principal no visible`);
}
async function checkAriaCurrent(page,key){
  const currents=page.locator('[aria-current="page"]');
  for(let i=0;i<await currents.count();i++){
    const el=currents.nth(i);const href=await el.getAttribute('href');
    if(!href)continue;
    const resolved=new URL(href,`${ORIGIN}${pages.find(p=>p.key===key).url}`).pathname;
    assert.equal(resolved,new URL(`${ORIGIN}${pages.find(p=>p.key===key).url}`).pathname,`${key}: aria-current ficticio en ${href}`);
  }
}
async function runResponsive(browser,report){
  for(const vp of viewports){report.responsive[vp.name]={};for(const def of pages){
    const context=await browser.newContext({viewport:{width:vp.width,height:vp.height}});const page=await context.newPage();
    const pageErrors=[];const consoleErrors=[];page.on('pageerror',e=>pageErrors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
    await page.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});await page.waitForTimeout(180);
    await noOverflow(page,`${def.key}@${vp.name}`);await assertStructure(page,def.key);await checkAriaCurrent(page,def.key);await checkTouchTargets(page,def.key);
    assert.deepEqual(pageErrors,[],`${def.key}@${vp.name}: pageerror ${pageErrors.join(' | ')}`);
    const relevantConsole=consoleErrors.filter(x=>!/(Failed to load resource|ERR_BLOCKED_BY_CLIENT)/i.test(x));assert.deepEqual(relevantConsole,[],`${def.key}@${vp.name}: console ${relevantConsole.join(' | ')}`);
    report.responsive[vp.name][def.key]={pass:true};await context.close();
  }}
}
async function runContracts(browser,report){
  {
    const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(`${ORIGIN}/empieza-aqui/`);
    const man=registry.get('/las-manecillas-del-recuerdo/'),sam=registry.get('/libros/samuel-entre-mundos/');assert(man&&sam);
    assert.equal(await p.locator(`main a[href="${man.url}"]`).count()>0,true);assert.equal(await p.locator(`main a[href="${sam.url}"]`).count()>0,true);
    assert((await p.locator('.findability-entry').first().innerText()).includes('Las manecillas del recuerdo'),'Empieza: la primera ruta no prioriza Manecillas');
    assert((await p.locator('.findability-entry').nth(1).innerText()).includes('Samuel entre mundos'),'Empieza: Samuel no conserva ruta propia');
    report.contracts.start={manecillas:true,samuel:true,ordered:true};await c.close();
  }
  {
    const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(`${ORIGIN}/mapa-del-sitio/`);
    assert(await p.locator('.directory-group').count()>=6,'Mapa: faltan grupos editoriales');
    const hrefs=await p.locator('main a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
    const nonPublic=[...registry.values()].filter(e=>e.status!=='public').map(e=>e.url);
    for(const blocked of nonPublic)assert(!hrefs.includes(blocked),`Mapa: destino no público filtrado por registry: ${blocked}`);
    assert(hrefs.includes('/herramientas/'),'Mapa: falta hub Herramientas');assert(hrefs.includes('/editoriales/'),'Mapa: falta Editoriales');assert(hrefs.includes('/convocatorias-escritores/'),'Mapa: falta Convocatorias');
    report.contracts.map={groups:await p.locator('.directory-group').count(),nonPublicExcluded:true,publicHubs:true};await c.close();
  }
  {
    const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(`${ORIGIN}/404.html`);
    const robots=(await p.locator('meta[name="robots"]').getAttribute('content')).replace(/\s/g,'').toLowerCase();assert.equal(robots,'noindex,follow');
    assert.equal(await p.locator('link[rel="canonical"]').count(),0,'404: canonical no permitido');assert.equal(await p.locator('script[type="application/ld+json"]').count(),0,'404: schema no permitido');
    assert.equal(await p.locator('html.v1').count(),1);assert.equal(await p.locator('link[href="/styles.css?v=202609-launch-1"]').count(),0);assert.equal(await p.locator('script[src="/script.js?v=202609-launch-1"]').count(),0);
    assert.equal(await p.locator('img[src*="logo-david-porto"]').count(),0);assert.equal(await p.locator('.findability-primary').count(),1,'404: debe haber una sola acción primaria');
    report.contracts['404']={robots:'noindex,follow',noCanonical:true,noSchema:true,v1:true,noLegacy:true,onePrimary:true};await c.close();
  }
}
async function runNoJs(browser,report){for(const def of pages){const c=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900}}),p=await c.newPage();await p.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});assert(await p.locator('h1').isVisible());assert(await p.locator('main a[href]').count()>=5,`${def.key}: orientación insuficiente sin JS`);await noOverflow(p,`${def.key}@nojs`);report.noJs[def.key]=true;await c.close();}}
async function runAccessibility(browser,report){for(const def of pages){const c=await browser.newContext({viewport:{width:390,height:900},reducedMotion:'reduce'}),p=await c.newPage();await p.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});assert.equal(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);await checkFocus(p,def.key);
  await p.evaluate(href=>new Promise((res,rej)=>{const l=document.createElement('link');l.rel='stylesheet';l.href=href;l.onload=res;l.onerror=rej;document.head.append(l)}),`${ORIGIN}/qa/text-spacing-findability.css`);await p.waitForTimeout(80);await noOverflow(p,`${def.key}@text-spacing`);
  const cdp=await c.newCDPSession(p);await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:2});await p.waitForTimeout(80);assert(await p.locator('h1').isVisible());await noOverflow(p,`${def.key}@zoom200`);await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});
  const animated=await p.locator('[data-family="findability"] *').evaluateAll(ns=>ns.filter(n=>getComputedStyle(n).animationName!=='none').length);assert.equal(animated,0,`${def.key}: animación activa con reduced-motion`);
  report.accessibility[def.key]={keyboard:true,focusVisible:true,textSpacing:true,zoom200:true,reducedMotion:true};await c.close();}}
async function runFallback(browser,report){for(const def of pages){const c=await browser.newContext({viewport:{width:320,height:900}}),p=await c.newPage();await p.route('**/assets/fonts/**',r=>r.abort());await p.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});await p.waitForTimeout(120);assert(await p.locator('h1').isVisible());await noOverflow(p,`${def.key}@fallback`);report.fontFallback[def.key]=true;await c.close();}}
async function runCls(browser,report){for(const def of pages){const values=[];for(let run=0;run<3;run++){const c=await browser.newContext({viewport:{width:1440,height:1000}}),p=await c.newPage();await p.addInitScript(()=>{window.__cls=0;new PerformanceObserver(list=>{for(const e of list.getEntries())if(!e.hadRecentInput)window.__cls+=e.value}).observe({type:'layout-shift',buffered:true})});await p.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});await p.waitForTimeout(1200);const value=await p.evaluate(()=>window.__cls||0);values.push(value);assert(value<=0.10,`${def.key}: CLS ${value}`);await c.close();}report.cls[def.key]=values;}}
async function runScreens(browser,report){for(const def of pages){for(const vp of [{name:'1440',width:1440,height:1000},{name:'390',width:390,height:900}]){const c=await browser.newContext({viewport:{width:vp.width,height:vp.height}}),p=await c.newPage();await p.goto(`${ORIGIN}${def.url}`,{waitUntil:'load'});await p.waitForTimeout(250);const file=`${def.key}-${vp.name}.png`;await p.screenshot({path:path.join(OUT,file),fullPage:false});report.screenshots.push(file);await c.close();}}}

const report={internalLinks:validateInternalLinks(),externalLinks:validateExternalLinks(),contracts:{},responsive:{},noJs:{},accessibility:{},fontFallback:{},cls:{},screenshots:[]};
const browser=await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try{await runContracts(browser,report);await runResponsive(browser,report);await runNoJs(browser,report);await runAccessibility(browser,report);await runFallback(browser,report);await runCls(browser,report);await runScreens(browser,report);fs.writeFileSync(path.join(OUT,'findability-browser-qa-report.json'),JSON.stringify(report,null,2));console.log('FINDABILITY BROWSER QA: OK');}finally{await browser.close();}
