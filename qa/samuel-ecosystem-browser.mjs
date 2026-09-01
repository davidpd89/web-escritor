import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve('qa-artifacts/samuel-ecosystem');
await fs.mkdir(OUT, { recursive: true });

function commandExists(cmd) {
  const probe = process.platform === 'win32' ? 'where' : 'which';
  const result = spawnSync(probe, [cmd], { stdio: 'ignore' });
  return result.status === 0;
}

// Poppler solo se puede omitir en una maquina de desarrollo. En CI el workflow
// instala poppler-utils a proposito, asi que si aqui no esta es que la
// instalacion se rompio: fallar es lo correcto. Sin esta linea la ausencia de
// poppler se veria exactamente igual que un PDF correcto, que es el modo de
// fallo que ya nos ha mordido varias veces en este repo.
function requirePdfTools() {
  const available = commandExists('pdfinfo') && commandExists('pdftotext');
  if (!available && process.env.CI) {
    throw new Error('print: pdfinfo/pdftotext ausentes en CI; el workflow debe instalar poppler-utils');
  }
  return available;
}

// 'samuel' (the book's own hub page, with the testimonial/proof strip) was
// missing from this map entirely until #133's audit: none of the generic
// loops below (overflow per viewport, long-content stress, keyboard, and
// critically the qa-text-200/qa-text-spacing 390px loop) ever ran against
// it, so a real ~19px overflow in .samuel-proof__stream under font-size:200%
// (assets/v1-samuel.css's <=620px breakpoint missing minmax(0,1fr), same
// class of bug as .samuel-route-list) went undetected until a manual repro
// found it. Added here instead of a new dedicated QA file so it inherits
// every existing generic check for free.
const URLS = {
  samuel: '/libros/samuel-entre-mundos/',
  noveris: '/universo/noveris/',
  club: '/clubes-de-lectura/samuel-entre-mundos/',
  guide: '/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/',
};
const CANONICAL = {
  samuel: 'https://davidportodiaz.com/libros/samuel-entre-mundos/',
  noveris: 'https://davidportodiaz.com/universo/noveris/',
  club: 'https://davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/',
  guide: 'https://davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/',
};
const VIEWPORTS = [
  [320,900],[390,900],[768,1000],[1024,900],[1440,1000],[1728,1000],[844,390],
];
const TERMS_BEFORE = ['Canalizador','Sael','Zakra','Gorx','Velukis','Glissaro','Vara Glytch','Glíder','Veltris','Sernía','Melastra','Velo / Barrera','Espejo Ancestral','Silenciadoras'];
const QUESTIONS = [
  '¿Por qué crees que Samuel decide cruzar la barrera aun sabiendo los riesgos? ¿Tú habrías cruzado?',
  'En Noveris, la magia siempre exige un precio. ¿Qué dice ese principio sobre cómo el autor entiende el poder?',
  'Los canalizadores tienen personalidad y preferencias propias. ¿Los considerarías personajes o herramientas?',
  'Zunthar y Marelian llevan décadas enfrentados por cómo debe distribuirse la magia. ¿Cuál de los dos bandos tiene razón?',
  'Samuel lleva toda su vida con el medallón sin saber lo que es. ¿Cómo te habrías sentido tú al descubrir su verdadero origen?',
  'Samuel es el "no-elegido": nadie lo eligió, simplemente llegó. ¿Prefieres ese tipo de protagonista frente al héroe destinado?',
  '¿Qué personaje secundario de Noveris os resultó más interesante? ¿Por qué?',
  'El libro mezcla aventura, secretos de familia y worldbuilding. ¿Cuál de los tres elementos fue el que más os enganchó?',
  'La narrativa transcurre casi íntegra en Noveris. ¿Echasteis de menos el mundo real? ¿O se os olvidó que existía?',
  'El final abre una segunda historia. ¿Qué creéis que pasará con Samuel y Noveris en el siguiente libro?',
];

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

function norm(value='') { return value.replace(/\s+/g,' ').trim(); }
async function context(options={}) {
  return browser.newContext({ locale:'es-ES', viewport:{width:1440,height:1000}, ...options });
}
async function openFresh(key, viewport={width:1440,height:1000}, options={}) {
  const ctx = await context({ viewport, ...options });
  const page = await ctx.newPage();
  // With scripting off there is no execution context: no init script runs, no
  // evaluate() succeeds and no layout-shift observer exists, so the frame
  // settle and the CLS assertion have to be skipped rather than crash.
  const scripting = options.javaScriptEnabled !== false;
  const errors=[]; const consoleErrors=[];
  page.on('pageerror', e=>errors.push(String(e)));
  page.on('console', m=>{ if(m.type()==='error') consoleErrors.push(m.text()); });
  if(scripting) await page.addInitScript(()=>{
    window.__qaCls=0;
    try { new PerformanceObserver(list=>{for(const e of list.getEntries()) if(!e.hadRecentInput) window.__qaCls+=e.value;}).observe({type:'layout-shift',buffered:true}); } catch {}
  });
  const response = await page.goto(`${BASE}${URLS[key]}`, {waitUntil:'networkidle'});
  assert.equal(response?.status(), 200, `${key}: HTTP 200`);
  if(scripting) await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  return {ctx,page,errors,consoleErrors,scripting};
}
async function closeClean(run,key) {
  if(run.scripting!==false){
    const cls=await run.page.evaluate(()=>window.__qaCls||0);
    assert.ok(cls<=0.1, `${key}: CLS ${cls}`);
  }
  assert.deepEqual(run.errors,[],`${key}: pageerror`);
  assert.deepEqual(run.consoleErrors,[],`${key}: console.error`);
  await run.ctx.close();
}
async function metadata(page,key,label) {
  assert.ok((await page.title()).trim(), `${label}: title`);
  assert.equal(await page.locator('link[rel="canonical"]').getAttribute('href'), CANONICAL[key], `${label}: canonical`);
  assert.match((await page.locator('meta[name="description"]').getAttribute('content'))||'', /\S/, `${label}: description`);
  assert.match((await page.locator('meta[name="robots"]').getAttribute('content'))||'', /index/, `${label}: robots`);
  assert.equal(await page.locator('h1').count(),1,`${label}: H1 único`);
  const badOrder=await page.evaluate(()=>{
    let prev=0; const bad=[];
    for(const h of document.querySelectorAll('h1,h2,h3,h4,h5,h6')){const n=Number(h.tagName[1]); if(prev&&n>prev+1) bad.push(`${prev}->${n}:${h.textContent}`); prev=n;}
    return bad;
  });
  assert.deepEqual(badOrder,[],`${label}: heading order`);
}
async function anchorsAndLinks(page,key) {
  const result=await page.evaluate(()=>{
    const ids=[...document.querySelectorAll('[id]')].map(e=>e.id);
    const dup=ids.filter((id,i)=>ids.indexOf(id)!==i);
    const broken=[...document.querySelectorAll('a[href^="#"]')].map(a=>a.getAttribute('href')).filter(h=>h.length>1&&!document.getElementById(h.slice(1)));
    const positive=[...document.querySelectorAll('[tabindex]')].filter(e=>Number(e.getAttribute('tabindex'))>0).length;
    return {dup:[...new Set(dup)],broken,positive};
  });
  assert.deepEqual(result.dup,[],`${key}: IDs duplicados`);
  assert.deepEqual(result.broken,[],`${key}: anchors rotos`);
  assert.equal(result.positive,0,`${key}: tabindex positivo`);
}
async function overflow(page,label,scripting=true){
  let n;
  if(scripting){
    n=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
  }else{
    // No execution context with scripting off, so read the same measurement
    // from the layout engine itself instead of skipping the check.
    const cdp=await page.context().newCDPSession(page);
    const m=await cdp.send('Page.getLayoutMetrics');
    n=Math.round(m.cssContentSize.width-m.cssLayoutViewport.clientWidth);
    await cdp.detach();
  }
  assert.ok(n<=1,`${label}: overflow horizontal ${n}px`);
}

// Noveris: canonical inventory, schema parity, media and cross-links.
{
  const run=await openFresh('noveris'); const {page}=run;
  await metadata(page,'noveris','Noveris'); await anchorsAndLinks(page,'Noveris');
  const terms=await page.locator('#glosario .id-card h3').allTextContents();
  assert.deepEqual(terms.map(norm),TERMS_BEFORE,'Noveris: términos visibles preservados y en el mismo orden');
  const schema=JSON.parse(await page.locator('script[type="application/ld+json"]').textContent());
  const graph=schema['@graph'];
  const termSet=graph.find(x=>x['@type']==='DefinedTermSet');
  const defined=termSet.hasDefinedTerm.map(x=>x.name);
  for(const term of TERMS_BEFORE) assert.ok(defined.includes(term),`Noveris: DefinedTerm faltante ${term}`);
  assert.equal(new Set(defined).size,defined.length,'Noveris: DefinedTerm duplicado');
  assert.ok(termSet.hasDefinedTerm.every(x=>norm(x.name)&&norm(x.description)), 'Noveris: ningún DefinedTerm puede quedar vacío');
  // A.7/#156 retired the FAQPage JSON-LD node here on purpose (REMOVE_KNOWN_FAQPAGE ·
  // PRESERVE_HUMAN_FAQ): the visible FAQ must survive, the schema duplicate must not.
  const faq=graph.find(x=>x['@type']==='FAQPage');
  assert.equal(faq,undefined,'Noveris: FAQPage schema debe seguir retirado (A.7)');
  const visibleQ=(await page.locator('#preguntas-frecuentes summary').allTextContents()).map(norm);
  assert.ok(visibleQ.length>0,'Noveris: FAQ visible debe seguir presente tras retirar el schema');
  const visibleA=(await page.locator('#preguntas-frecuentes p').allTextContents()).map(norm);
  assert.ok(visibleA.every(a=>a.length>0),'Noveris: respuestas FAQ visibles no vacías');
  assert.equal(termSet.hasDefinedTerm.find(x=>x.name==='Noveris').sameAs,'https://www.wikidata.org/wiki/Q139927664','Noveris: sameAs preservado');
  // Scoped to main: PR95's persistent .section-context strip (2026-08-24)
  // now repeats this same destination sitewide as chrome navigation, so a
  // page-wide count would also catch that unrelated nav layer instead of
  // the page's own contextual content link this assertion actually checks.
  assert.equal(await page.locator('main a[href="/clubes-de-lectura/samuel-entre-mundos/"]').count(),1,'Noveris: enlace contextual al club');
  const media=await page.locator('main img').evaluateAll(imgs=>imgs.map(i=>({alt:i.alt,w:i.getAttribute('width'),h:i.getAttribute('height'),src:i.getAttribute('src')})));
  for(const m of media){assert.ok(m.alt.trim(),`Noveris media alt ${m.src}`); assert.ok(m.w&&m.h,`Noveris media dimensions ${m.src}`);}
  await closeClean(run,'Noveris');
}

// Club: preserve all canonical questions and objective spoiler labelling.
{
  const run=await openFresh('club'); const {page}=run;
  await metadata(page,'club','Club'); await anchorsAndLinks(page,'Club');
  const q=(await page.locator('#guia details summary').allTextContents()).map(x=>norm(x).replace(/^\d+\.\s*/,''));
  assert.deepEqual(q,QUESTIONS,'Club: 10 preguntas canónicas preservadas');
  assert.match(norm(await page.locator('#guia .tool-note').textContent()),/spoilers/i,'Club: bloque final avisa spoilers');
  assert.match(norm(await page.locator('#guia-sin-spoilers .eyebrow').textContent()),/sin spoilers/i,'Club: capa previa marcada sin spoilers');
  assert.ok(await page.locator('a[href="/universo/noveris/"]').count()>0,'Club: enlaza Noveris');
  assert.ok(await page.locator('a[href="/clubes-de-lectura/samuel-entre-mundos/guia-imprimible/"]').count()>0,'Club: enlaza guía imprimible');
  await closeClean(run,'Club');
}

// Printable guide: questions must be byte-equivalent after normalization to Club.
{
  const run=await openFresh('guide'); const {page}=run;
  await metadata(page,'guide','Guía'); await anchorsAndLinks(page,'Guía');
  const q=(await page.locator('.questions li strong').allTextContents()).map(norm);
  assert.deepEqual(q,QUESTIONS,'Guía: preguntas sincronizadas con Club');
  assert.match(norm(await page.locator('#preguntas').locator('xpath=preceding-sibling::*[1]').textContent()),/terminar el libro/i,'Guía: capa postlectura explícita');
  assert.equal(await page.locator('button').filter({hasText:'Imprimir guía'}).count(),1,'Guía: acción de impresión');
  await closeClean(run,'Guía');
}

// Fresh context for every required viewport: never resize an initialized page.
for(const key of Object.keys(URLS)){
  for(const [width,height] of VIEWPORTS){
    const run=await openFresh(key,{width,height});
    await overflow(run.page,`${key} ${width}x${height}`);
    await closeClean(run,`${key} ${width}x${height}`);
  }
}

// Stress long lore/URL in fresh 320 contexts.
for(const key of Object.keys(URLS)){
  const run=await openFresh(key,{width:320,height:900});
  await run.page.evaluate(()=>{
    const host=document.querySelector('main');
    const p=document.createElement('p'); p.dataset.qaStress='';
    p.textContent='CanalizadorInterdimensionalExperimentalSinEspacios https://example.test/'+'ruta'.repeat(35);
    host.append(p);
  });
  await overflow(run.page,`${key} long-content 320`);
  await closeClean(run,`${key} long-content`);
}

// Keyboard/skip-link on all three surfaces.
for(const key of Object.keys(URLS)){
  const run=await openFresh(key);
  await run.page.evaluate(()=>document.activeElement?.blur());
  await run.page.keyboard.press('Tab');
  assert.ok(await run.page.evaluate(()=>document.activeElement?.classList.contains('skip-link')),`${key}: primer Tab alcanza skip link`);
  await closeClean(run,`${key} keyboard`);
}

// 200% text and WCAG text-spacing using a same-origin QA stylesheet.
for(const className of ['qa-text-200','qa-text-spacing']){
  for(const key of Object.keys(URLS)){
    const run=await openFresh(key,{width:390,height:900});
    await run.page.evaluate(()=>new Promise((resolve,reject)=>{const l=document.createElement('link');l.rel='stylesheet';l.href='/qa/samuel-ecosystem-text-resilience.css';l.onload=resolve;l.onerror=reject;document.head.append(l);}));
    await run.page.evaluate(c=>document.documentElement.classList.add(c),className);
    await run.page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
    // Restyling the whole document after load is a deliberate reflow by this
    // harness, so it registers as one huge layout shift that says nothing
    // about the page's own stability. Discard it and keep asserting CLS on
    // anything the page shifts from here on.
    await run.page.evaluate(()=>{window.__qaCls=0;});
    await overflow(run.page,`${key} ${className}`);
    await closeClean(run,`${key} ${className}`);
  }
}

// Reduced motion is genuinely emulated in a new context.
for(const key of Object.keys(URLS)){
  const run=await openFresh(key,{width:390,height:900},{reducedMotion:'reduce'});
  assert.equal(await run.page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true,`${key}: reduced motion emulado`);
  await closeClean(run,`${key} reduced-motion`);
}

// No-JS: critical content remains in HTML.
for(const key of Object.keys(URLS)){
  const run=await openFresh(key,{width:390,height:900},{javaScriptEnabled:false});
  assert.equal(await run.page.locator('h1').count(),1,`${key}: H1 no-JS`);
  if(key==='noveris') assert.equal(await run.page.locator('#glosario .id-card h3').count(),14,'Noveris: glosario no-JS');
  if(key==='club') assert.equal(await run.page.locator('#guia details summary').count(),10,'Club: preguntas no-JS');
  if(key==='guide') assert.equal(await run.page.locator('.questions li').count(),10,'Guía: preguntas no-JS');
  await overflow(run.page,`${key} no-JS`,run.scripting);
  await closeClean(run,`${key} no-JS`);
}

// Required visual evidence.
for(const [key,width,file] of [
  ['noveris',1440,'noveris-1440.png'],['noveris',390,'noveris-390.png'],
  ['club',1440,'club-1440.png'],['club',390,'club-390.png'],['guide',390,'guide-390.png'],
]){
  const run=await openFresh(key,{width,height:1000});
  await run.page.screenshot({path:path.join(OUT,file),fullPage:true});
  await closeClean(run,`${key} screenshot`);
}

// Actual A4 PDF + print-media assertions + text/page extraction with Poppler.
{
  const run=await openFresh('guide',{width:1440,height:1000}); const {page}=run;
  await page.emulateMedia({media:'print'});
  // Switching to print media is a deliberate reflow by this harness (the print
  // stylesheet hides the chrome and re-lays the document), so it registers as
  // one large layout shift that says nothing about the page's own stability.
  // Same reasoning as the text-stress runs above. layout-shift entries are
  // delivered asynchronously, so let them land before clearing the counter —
  // resetting straight after emulateMedia() discards nothing.
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  await page.waitForTimeout(120);
  await page.evaluate(()=>{window.__qaCls=0;});
  for(const sel of ['.skip-link','.topbar','.breadcrumb','.actions']) assert.equal(await page.locator(sel).evaluate(el=>getComputedStyle(el).display),'none',`print: ${sel} oculto`);
  const pdf=path.join(OUT,'samuel-guia-imprimible.pdf');
  await page.pdf({path:pdf,format:'A4',printBackground:false,preferCSSPageSize:true});
  const stat=await fs.stat(pdf); assert.ok(stat.size>20000,`print: PDF útil (${stat.size} bytes)`);
  const canInspectPdf = requirePdfTools();
  if (canInspectPdf) {
    const info=execFileSync('pdfinfo',[pdf],{encoding:'utf8'});
    const pages=Number(info.match(/^Pages:\s+(\d+)/m)?.[1]);
    assert.ok(pages>=2&&pages<=8,`print: páginas razonables (${pages})`);
    const text=execFileSync('pdftotext',[pdf,'-'],{encoding:'utf8'});
    for(const essential of ['Samuel entre mundos','10 preguntas de debate','El final abre una segunda historia','davidportodiaz.com/clubes-de-lectura/samuel-entre-mundos/']) assert.ok(text.includes(essential),`print: falta texto esencial: ${essential}`);
  } else {
    console.log('print: pdfinfo/pdftotext no disponibles; se omiten validaciones de metadata/texto del PDF en este entorno');
  }
  await page.screenshot({path:path.join(OUT,'guide-print.png'),fullPage:true});
  await closeClean(run,'Guía print');
}

await browser.close();
console.log('qa/samuel-ecosystem-browser: OK');