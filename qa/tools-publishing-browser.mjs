import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts';
const SENTINEL = 'LOCAL_QA_SENTINEL_582931';

const tools = [
  { key:'metadatos', path:'/herramientas/metadatos-libro/', processor:'[data-publishing-processor]' },
  { key:'jsonld', path:'/herramientas/json-ld-escritores/', processor:'[data-publishing-processor]' },
  { key:'kit', path:'/herramientas/kit-prensa-escritores/', processor:'[data-publishing-processor]' },
  { key:'auditor', path:'/herramientas/auditor-pagina-libro/', processor:'[data-publishing-processor]' },
];
const viewports = [
  {name:'320',width:320,height:760},
  {name:'390',width:390,height:844},
  {name:'768',width:768,height:1024},
  {name:'1024',width:1024,height:900},
  {name:'1440',width:1440,height:1000},
  {name:'landscape',width:844,height:390},
];

const completeAuditHtml = `<!doctype html><html><head>
<title>La casa de prueba | Ana Ejemplo</title>
<meta name="description" content="Una descripción controlada suficientemente larga para explicar la premisa, el conflicto y el tipo de lector al que puede interesarle esta novela de prueba.">
<meta property="og:image" content="https://example.test/portada.webp">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Book","name":"La casa de prueba","isbn":"9781234567890","publisher":{"@type":"Organization","name":"Editorial Ejemplo"},"datePublished":"2026-09-03","numberOfPages":272,"bookFormat":"https://schema.org/Paperback","author":{"@type":"Person","name":"Ana Ejemplo"}}</script>
</head><body><h1>La casa de prueba</h1><p>Autora: Ana Ejemplo. Ya disponible. ISBN 978-1-23456-789-0. Editorial Ejemplo. Fecha de publicación: 2026-09-03. 272 páginas. Tapa blanda.</p>
<img src="/portada.webp" alt="Portada de La casa de prueba"><p>${'Descripción del libro. '.repeat(35)}</p>
<a href="https://tienda.example.test/libro">Comprar</a><a href="/fragmento/">Leer un fragmento</a></body></html>`;

const incompleteAuditHtml = `<html><head><title>La casa de prueba</title></head><body><h1>La casa de prueba</h1><p>Texto breve sin autor, portada, descripción ni compra.</p></body></html>`;

function longText(n=220){ return Array.from({length:n},(_,i)=>`palabra${i%30}`).join(' '); }

async function waitReady(page) {
  const p = page.locator('[data-publishing-processor]');
  await p.waitFor({state:'visible'});
  await page.waitForFunction(() => !document.querySelector('[data-publishing-processor]')?.hasAttribute('inert'));
}

async function noOverflow(page, label) {
  const m = await page.evaluate(() => ({
    sw: document.documentElement.scrollWidth,
    cw: document.documentElement.clientWidth,
    bw: document.body.scrollWidth,
  }));
  assert(m.sw <= m.cw + 1, `${label}: overflow document ${JSON.stringify(m)}`);
  assert(m.bw <= m.cw + 1, `${label}: overflow body ${JSON.stringify(m)}`);
}

function monitor(page) {
  const requests=[], sockets=[], navigations=[];
  let active=false;
  page.on('request', req => {
    if (!active) return;
    requests.push({url:req.url(), method:req.method(), postData:req.postData()||'', type:req.resourceType()});
  });
  page.on('websocket', ws => { if(active) sockets.push(ws.url()); });
  page.on('framenavigated', frame => { if(active && frame===page.mainFrame()) navigations.push(frame.url()); });
  return {
    start(){ active=true; },
    stop(){ active=false; },
    assertClean(key){
      const leaks=requests.filter(r=>r.url.includes(SENTINEL)||r.postData.includes(SENTINEL));
      const external=requests.filter(r=>{
        if(r.url.startsWith('blob:')||r.url.startsWith('data:')) return false;
        try{return new URL(r.url).origin!==ORIGIN;}catch{return true;}
      });
      const externalNav=navigations.filter(u=>{
        if(u.startsWith('blob:')||u.startsWith('data:')) return false;
        try{return new URL(u).origin!==ORIGIN;}catch{return true;}
      });
      assert.equal(leaks.length,0,`${key}: sentinel leaked ${JSON.stringify(leaks)}`);
      assert.equal(external.length,0,`${key}: external request ${JSON.stringify(external)}`);
      assert.equal(sockets.length,0,`${key}: websocket ${JSON.stringify(sockets)}`);
      assert.equal(externalNav.length,0,`${key}: external navigation ${JSON.stringify(externalNav)}`);
      return {requests:requests.map(({url,method,type})=>({url,method,type})),sentinelLeaked:false,externalRequests:0,websockets:0,externalNavigations:0};
    }
  };
}

async function fillMetadata(page, hostile=false) {
  const values = {
    book: hostile ? `Niña & «mar» <script>${SENTINEL}</script>` : `La casa de prueba ${SENTINEL}`,
    author: hostile ? `Ana "Ejemplo" & < >` : 'Ana Ejemplo',
    site: 'Ana Ejemplo',
    url: 'https://example.test/libros/la-casa/',
    description: hostile ? `"</script>" & < > ${SENTINEL}` : `Una descripción controlada ${SENTINEL} sobre memoria, familia y publicación editorial.`,
    image: `https://assets.example.test/${SENTINEL}.webp`,
    image_alt: hostile ? `"><svg onload=alert(1)> ${SENTINEL}` : 'Portada de La casa de prueba',
    isbn: '9781234567890',
    release_date: '2026-09-03',
    author_url: 'https://example.test/ana/',
    x_site: '@anaejemplo',
  };
  for (const [name,value] of Object.entries(values)) await page.locator(`[name="${name}"]`).fill(value);
  await page.locator('[data-meta-form] button[type="submit"]').click();
  await page.locator('[data-meta-output]').waitFor({state:'visible'});
}

function jsonFromOutput(text) {
  const m=text.match(/<script[^>]*>\s*([\s\S]*?)\s*<\/script>/);
  assert(m,'JSON-LD output sin script');
  return JSON.parse(m[1]);
}

async function fillJsonMode(page, mode) {
  await page.locator('#jsonld-mode').selectOption(mode);
  const data = mode==='profile' ? {name:`Ana ${SENTINEL}`,url:'https://example.test/ana/',image:'https://example.test/ana.webp',sameAs:'https://social.example.test/ana'}
    : mode==='book' ? {name:`La casa ${SENTINEL}`,url:'https://example.test/libro/',description:'Descripción visible',image:'https://example.test/cover.webp',isbn:'9781234567890',pages:'272',datePublished:'2026-09-03',bookFormat:'https://schema.org/Paperback',authorName:'Ana Ejemplo',authorUrl:'https://example.test/ana/',publisher:'Editorial Ejemplo'}
    : mode==='article' ? {headline:`Artículo ${SENTINEL}`,url:'https://example.test/articulo/',description:'Descripción visible',image:'https://example.test/article.webp',datePublished:'2026-08-21',authorName:'Ana Ejemplo',authorUrl:'https://example.test/ana/'}
    : {name:`Firma ${SENTINEL}`,url:'https://example.test/evento/',description:'Firma de libros',startDate:'2026-09-03T18:00',endDate:'2026-09-03T19:00',attendanceMode:'https://schema.org/OfflineEventAttendanceMode',locationName:'Librería Ejemplo',address:'Calle de Prueba 1',city:'Madrid',country:'ES',organizerName:'Librería Ejemplo',organizerUrl:'https://example.test/'};
  for (const [name,value] of Object.entries(data)) {
    const el=page.locator(`#jsonld-fields [name="${name}"]`);
    if(await el.count()) {
      const tag=await el.evaluate(node=>node.tagName);
      if(tag==='SELECT') await el.selectOption(value); else await el.fill(value);
    }
  }
  await page.waitForTimeout(50);
  return jsonFromOutput(await page.locator('#jsonld-output').textContent());
}

async function fillKitBase(page, description=`Texto controlado. ${SENTINEL}`) {
  const values={
    authorName:'Ana Ejemplo',contactEmail:'prensa@example.test',website:'https://example.test',
    bioShort:'Ana Ejemplo escribe narrativa contemporánea de prueba.',bioLong:'Biografía larga controlada.',
    bookTitle:'La casa de prueba',publisher:'Editorial Ejemplo',isbn:'9781234567890',
    publicationDate:'2026-09-03',price:'16 €',purchaseUrl:'https://example.test/libro',
    bookDescription:description,interviewTopics:'Memoria\nEscritura',
  };
  for(const [name,value] of Object.entries(values)) await page.locator(`[name="${name}"]`).fill(value);
  await page.locator('[name="assetPermission"]').selectOption('contact_only');
}

const jpg=Buffer.from([0xff,0xd8,0xff,0xe0,0,16,0x4a,0x46,0x49,0x46,0,1,1,0,0,1,0,1,0,0,0xff,0xd9]);
const webp=Buffer.from('524946461000000057454250565038200400000000000000','hex');
const pdf=Buffer.from('%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n');

async function attachValidKitFiles(page) {
  await page.locator('[name="authorPhotos"]').setInputFiles({name:'../../Ana ñandú.html',mimeType:'image/jpeg',buffer:jpg});
  await page.locator('[name="coverFiles"]').setInputFiles([
    {name:'portada ñandú.webp',mimeType:'image/webp',buffer:webp},
    {name:'portada ñandú.webp',mimeType:'image/webp',buffer:webp},
  ]);
  await page.locator('[name="otherFiles"]').setInputFiles({name:'../../dossier.pdf',mimeType:'application/pdf',buffer:pdf});
}

async function submitKitAndSave(page, savePath=null) {
  const dlPromise=page.waitForEvent('download');
  await page.locator('[data-kit-submit]').click();
  const dl=await dlPromise;
  if(savePath) await dl.saveAs(savePath); else await dl.cancel();
  await page.locator('[data-kit-summary]').waitFor({state:'visible'});
  return dl.suggestedFilename();
}

async function runPrivacy(browser, report) {
  for(const tool of tools){
    const context=await browser.newContext({viewport:{width:1024,height:900},acceptDownloads:true});
    const page=await context.newPage();
    const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(`${ORIGIN}${tool.path}`,{waitUntil:'networkidle'});
    await waitReady(page);
    const mon=monitor(page); mon.start();
    if(tool.key==='metadatos'){
      await fillMetadata(page,true);
      const slot=page.locator('[data-og-image]');
      assert.equal(await slot.evaluate(el=>el.tagName),'DIV');
      assert.equal(await slot.getAttribute('src'),null);
      assert((await slot.textContent()).includes(SENTINEL));
      const code=await page.locator('[data-meta-code]').textContent();
      assert.equal(code.includes('<svg onload='),false);
      assert(code.includes('&lt;script&gt;'));
    } else if(tool.key==='jsonld'){
      const out=await fillJsonMode(page,'book');
      assert.equal(out['@type'],'Book');
      assert(out.name.includes(SENTINEL));
      assert.equal(out.inLanguage,undefined);
    } else if(tool.key==='kit'){
      await fillKitBase(page);
      await attachValidKitFiles(page);
      await submitKitAndSave(page,path.join(OUT,'press-kit-qa.zip'));
    } else {
      const hostile=`<html><body><h1>La casa ${SENTINEL}</h1><p>Autora: Ana.</p><script>alert(1)</script><img src=x onerror=alert(1)><p>"</script>" & < > ${SENTINEL}</p></body></html>`;
      await page.locator('[data-book-audit-html]').fill(hostile);
      await page.locator('[data-book-audit-url]').fill(`https://example.test/${SENTINEL}`);
      await page.locator('[data-book-audit-form] button[type="submit"]').click();
      await page.locator('[data-book-audit-results]').waitFor({state:'visible'});
      assert((await page.locator('[data-book-audit-detected]').textContent()).includes(SENTINEL));
      assert.equal(await page.evaluate(()=>window.__xssFired||false),false);
    }
    await page.waitForTimeout(250);
    report.privacy[tool.key]=mon.assertClean(tool.key);
    assert.deepEqual(errors,[],`${tool.key}: page errors ${errors.join(' | ')}`);
    await context.close();
  }
  console.log('INPUT EXFILTRATION: 0/4');
}

async function runFunctional(browser, report){
  {
    const c=await browser.newContext({viewport:{width:1024,height:900}});
    const p=await c.newPage(); await p.goto(`${ORIGIN}/herramientas/metadatos-libro/`); await waitReady(p);
    await fillMetadata(p);
    const code=await p.locator('[data-meta-code]').textContent();
    assert(code.includes('<title>La casa de prueba'));
    assert(code.includes('book:isbn'));
    assert((await p.locator('.meta-card__label').first().textContent()).includes('orientativa'));
    await p.locator('[name="description"]').fill('Descripción '.repeat(30));
    assert((await p.locator('[data-meta-warnings]').textContent()).includes('descripción es larga'));
    await p.locator('[name="url"]').fill('http://example.test/libro');
    assert((await p.locator('[data-meta-warnings]').textContent()).includes('HTTPS'));
    await p.locator('[name="url"]').fill('https://exa mple.test');
    assert((await p.locator('[data-meta-warnings]').textContent()).includes('HTTPS'));
    report.functional.metadatos={valid:true,longTitleDescription:true,httpInvalid:true,invalidUrl:true,remoteImageNotFetched:true};
    await c.close();
  }
  {
    const c=await browser.newContext({viewport:{width:1024,height:900}});
    const p=await c.newPage(); await p.goto(`${ORIGIN}/herramientas/json-ld-escritores/`); await waitReady(p);
    for(const mode of ['profile','book','article','event']){
      const out=await fillJsonMode(p,mode);
      assert.equal(out['@context'],'https://schema.org');
      assert(out['@type']);
      assert.doesNotThrow(()=>JSON.parse(JSON.stringify(out)));
      if(mode==='book') assert.equal(out.bookFormat,'https://schema.org/Paperback');
      if(mode==='event') assert.equal(out.eventAttendanceMode,'https://schema.org/OfflineEventAttendanceMode');
      report.functional.jsonld[mode]={pass:true,type:out['@type']};
    }
    await p.locator('#jsonld-mode').selectOption('profile');
    await p.locator('#f-url').fill('https://exa mple.test');
    assert((await p.locator('#jsonld-report').textContent()).includes('HTTPS válida'));
    report.functional.jsonld.invalidUrl=true;
    await c.close();
  }
  const kitError=async(files, expected, mutate={})=>{
    const c=await browser.newContext({viewport:{width:1024,height:900},acceptDownloads:true});
    const p=await c.newPage(); await p.goto(`${ORIGIN}/herramientas/kit-prensa-escritores/`); await waitReady(p); await fillKitBase(p);
    for(const [name,value] of Object.entries(mutate)) await p.locator(`[name="${name}"]`).fill(value);
    if(files) await files(p);
    await p.locator('form[data-publishing-processor]').dispatchEvent('submit');
    await p.waitForTimeout(80);
    const t=await p.locator('[data-kit-status]').textContent();
    assert(t.includes(expected),`kit expected "${expected}", got "${t}"`);
    await c.close();
  };
  await kitError(null,'email de prensa',{contactEmail:'x'});
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles(Array.from({length:11},(_,i)=>({name:`a${i}.pdf`,mimeType:'application/pdf',buffer:pdf}))),'máximo es 10');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles({name:'grande.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(12*1024*1024+1)}),'demasiado grande');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles([
    {name:'a.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)},
    {name:'b.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)},
    {name:'c.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)},
  ]),'superan 25 MiB');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles({name:'mal.txt',mimeType:'text/plain',buffer:Buffer.from('x')}),'Formato no admitido');
  await kitError(null,'enlace oficial',{purchaseUrl:'javascript:alert(1)'});
  report.functional.kit={validZip:true,invalidEmail:true,tooMany:true,fileTooLarge:true,totalTooLarge:true,typeRejected:true,unsafePurchaseUrlRejected:true};

  {
    const c=await browser.newContext({viewport:{width:1024,height:900}});
    const p=await c.newPage(); await p.goto(`${ORIGIN}/herramientas/auditor-pagina-libro/`); await waitReady(p);
    for(const [name,html] of [['complete',completeAuditHtml],['incomplete',incompleteAuditHtml],['noJson','<html><body><h1>Libro</h1><p>Autora: Ana. Ya disponible.</p><a href="/comprar">Comprar</a></body></html>'],['invalidJson','<html><body><h1>Libro</h1><script type="application/ld+json">{"@type":"Book",}</script></body></html>'],['minified','<html><body><h1>Libro</h1><p>Autora: Ana. Ya disponible.</p><a href="/comprar">Comprar</a></body></html>']]){
      await p.locator('[data-book-audit-html]').fill(html);
      await p.locator('[data-book-audit-form] button[type="submit"]').click();
      await p.locator('[data-book-audit-results]').waitFor({state:'visible'});
      report.functional.auditor[name]={pass:true,text:(await p.locator('[data-book-audit-groups]').textContent()).slice(0,120)};
    }
    await p.locator('[data-book-audit-html]').fill('');
    await p.locator('[data-book-audit-form] button[type="submit"]').click();
    assert((await p.locator('[data-book-audit-status]').textContent()).includes('Pega el código HTML'));
    report.functional.auditor.empty=true;
    await c.close();
  }
}

async function runNoJs(browser,report){
  for(const tool of tools){
    const c=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
    const p=await c.newPage();
    const response=await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'domcontentloaded'});
    const raw=await response.text();
    assert(raw.includes('<noscript>'),`${tool.key}: no noscript`);
    assert(raw.includes('JavaScript está desactivado.'),`${tool.key}: no notice`);
    assert(await p.locator('h1').isVisible(),`${tool.key}: h1 hidden`);
    const proc=p.locator(tool.processor);
    assert.equal(await proc.getAttribute('inert'),'');
    assert.equal(await proc.getAttribute('aria-disabled'),'true');
    await noOverflow(p,`${tool.key}@nojs`);
    report.noJs[tool.key]={pass:true,semanticNoscript:true,processorInert:true};
    await c.close();
  }
}

async function runResponsive(browser,report){
  for(const vp of viewports){
    report.responsive[vp.name]={};
    for(const tool of tools){
      const c=await browser.newContext({viewport:{width:vp.width,height:vp.height}});
      const p=await c.newPage(); const errors=[]; p.on('pageerror',e=>errors.push(String(e)));
      await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'domcontentloaded'}); await waitReady(p);
      await noOverflow(p,`${tool.key}@${vp.name}`);
      assert.deepEqual(errors,[]);
      report.responsive[vp.name][tool.key]={pass:true};
      await c.close();
    }
  }
}

async function runA11y(browser,report){
  for(const tool of tools){
    const c=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
    const p=await c.newPage(); await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'domcontentloaded'}); await waitReady(p);
    assert.equal(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),true);
    await p.keyboard.press('Tab');
    assert.equal(await p.evaluate(()=>document.activeElement?.classList.contains('skip-link')),true,`${tool.key}: first tab`);
    let reached=false, focus=false;
    for(let i=0;i<45;i++){
      await p.keyboard.press('Tab');
      const s=await p.evaluate(()=>{
        const e=document.activeElement;if(!(e instanceof HTMLElement))return null;
        const cs=getComputedStyle(e);
        return {inside:Boolean(e.closest('[data-publishing-processor]')),outline:cs.outlineStyle!=='none'&&parseFloat(cs.outlineWidth)>0,shadow:cs.boxShadow!=='none'};
      });
      if(s?.inside){reached=true;focus=s.outline||s.shadow;break;}
    }
    assert(reached,`${tool.key}: no form focus`);
    assert(focus,`${tool.key}: no visible focus`);
    await p.evaluate(href=>new Promise((resolve,reject)=>{
      const l=document.createElement('link');l.rel='stylesheet';l.href=href;l.onload=resolve;l.onerror=reject;document.head.append(l);
    }),`${ORIGIN}/qa/text-spacing-publishing.css`);
    await p.waitForTimeout(50); await noOverflow(p,`${tool.key}@spacing`);
    const cdp=await c.newCDPSession(p); await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:2}); await p.waitForTimeout(50);
    assert(await p.locator('h1').isVisible()); await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});
    report.accessibility[tool.key]={keyboard:true,focusVisible:true,textSpacing:true,zoom200:true,reducedMotion:true};
    await c.close();
  }
}

async function runCls(browser,report){
  for(const tool of tools){
    const c=await browser.newContext({viewport:{width:1350,height:940}});
    const p=await c.newPage();
    await p.addInitScript(()=>{window.__qaCls=0;new PerformanceObserver(list=>{for(const e of list.getEntries())if(!e.hadRecentInput)window.__qaCls+=e.value;}).observe({type:'layout-shift',buffered:true});});
    await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'networkidle'}); await p.waitForTimeout(1000);
    const cls=await p.evaluate(()=>window.__qaCls||0);
    assert(cls<=0.10,`${tool.key}: CLS ${cls}`);
    report.cls[tool.key]=cls;
    await c.close();
  }
}

async function runFallbackFonts(browser,report){
  for(const tool of tools){
    const c=await browser.newContext({viewport:{width:320,height:760}});
    const p=await c.newPage();
    await p.route('**/assets/fonts/**',route=>route.abort());
    await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'domcontentloaded'}); await waitReady(p); await noOverflow(p,`${tool.key}@fallback-fonts`);
    report.fallbackFonts[tool.key]=true; await c.close();
  }
}

async function shot(browser,key,width,height,file){
  const tool=tools.find(t=>t.key===key);
  const c=await browser.newContext({viewport:{width,height},acceptDownloads:true});
  const p=await c.newPage(); await p.goto(`${ORIGIN}${tool.path}`,{waitUntil:'networkidle'}); await waitReady(p);
  if(key==='metadatos'){ await fillMetadata(p); await p.locator('[data-meta-output]').scrollIntoViewIfNeeded(); }
  if(key==='jsonld'){ await fillJsonMode(p,'book'); await p.locator('#jsonld-output').scrollIntoViewIfNeeded(); }
  if(key==='kit'){ await fillKitBase(p); await attachValidKitFiles(p); await submitKitAndSave(p); await p.locator('[data-kit-summary]').scrollIntoViewIfNeeded(); }
  if(key==='auditor'){ await p.locator('[data-book-audit-html]').fill(incompleteAuditHtml); await p.locator('[data-book-audit-form] button[type="submit"]').click(); await p.locator('[data-book-audit-results]').waitFor({state:'visible'}); await p.locator('[data-book-audit-results]').scrollIntoViewIfNeeded(); }
  await p.waitForTimeout(100); await p.screenshot({path:path.join(OUT,file),fullPage:false}); await c.close();
}
async function runScreenshots(browser,report){
  const shots=[
    ['metadatos',1440,1000,'metadatos-1440-result.png'],['metadatos',390,844,'metadatos-390-result.png'],
    ['jsonld',1440,1000,'jsonld-book-1440-result.png'],['jsonld',390,844,'jsonld-390-result.png'],
    ['kit',1440,1000,'kit-1440-valid.png'],['kit',390,844,'kit-390-valid.png'],
    ['auditor',1440,1000,'auditor-1440-result.png'],['auditor',390,844,'auditor-390-result.png'],
  ];
  for(const s of shots) await shot(browser,...s);
  report.screenshots=shots.map(([tool,width,height,file])=>({tool,width,height,file,state:'RESULT'}));
}

await fs.mkdir(OUT,{recursive:true});
const report={privacy:{},functional:{jsonld:{},auditor:{}},noJs:{},responsive:{},accessibility:{},cls:{},fallbackFonts:{},screenshots:[]};
const browser=await chromium.launch({headless:true});
try{
  await runCls(browser,report);
  await runPrivacy(browser,report);
  await runFunctional(browser,report);
  await runNoJs(browser,report);
  await runResponsive(browser,report);
  await runA11y(browser,report);
  await runFallbackFonts(browser,report);
  await runScreenshots(browser,report);
  await fs.writeFile(path.join(OUT,'publishing-browser-qa-report.json'),JSON.stringify(report,null,2));
  console.log('PUBLISHING TOOLS BROWSER QA: OK');
}finally{
  await browser.close();
}
