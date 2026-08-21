import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const OUT=process.env.QA_OUT||'qa-artifacts';
const SENTINEL='LOCAL_QA_SENTINEL_582931';
const tools=[
  ['metadatos','/herramientas/metadatos-libro/'],
  ['jsonld','/herramientas/json-ld-escritores/'],
  ['kit','/herramientas/kit-prensa-escritores/'],
  ['auditor','/herramientas/auditor-pagina-libro/'],
];
const viewports=[['320',320,760],['390',390,844],['768',768,1024],['1024',1024,900],['1440',1440,1000],['landscape',844,390]];
const jpg=Buffer.from([0xff,0xd8,0xff,0xe0,0,16,0x4a,0x46,0x49,0x46,0,1,1,0,0,1,0,1,0,0,0xff,0xd9]);
const webp=Buffer.from('524946461000000057454250565038200400000000000000','hex');
const pdf=Buffer.from('%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n');
const incomplete='<html><head><title>La casa de prueba</title></head><body><h1>La casa de prueba</h1><p>Texto breve.</p></body></html>';

async function ready(page){
  await page.locator('[data-publishing-processor]').waitFor({state:'visible'});
  await page.waitForFunction(()=>!document.querySelector('[data-publishing-processor]')?.hasAttribute('inert'));
  const csp=await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
  assert(csp?.includes("connect-src 'none'"),'CSP sin connect-src none');
}
async function noOverflow(page,label){
  const m=await page.evaluate(()=>({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth,bw:document.body.scrollWidth}));
  assert(m.sw<=m.cw+1,`${label}: document overflow ${JSON.stringify(m)}`);
  assert(m.bw<=m.cw+1,`${label}: body overflow ${JSON.stringify(m)}`);
}
function networkGuard(page){
  const req=[],ws=[],nav=[];let active=false;
  page.on('request',r=>{if(active)req.push({url:r.url(),body:r.postData()||'',type:r.resourceType()});});
  page.on('websocket',w=>{if(active)ws.push(w.url());});
  page.on('framenavigated',f=>{if(active&&f===page.mainFrame())nav.push(f.url());});
  return {start(){active=true;},check(key){
    const external=req.filter(r=>!r.url.startsWith('blob:')&&!r.url.startsWith('data:')&&new URL(r.url).origin!==ORIGIN);
    const leaks=req.filter(r=>r.url.includes(SENTINEL)||r.body.includes(SENTINEL));
    const externalNav=nav.filter(u=>!u.startsWith('blob:')&&!u.startsWith('data:')&&new URL(u).origin!==ORIGIN);
    assert.equal(leaks.length,0,`${key}: sentinel leaked`);assert.equal(external.length,0,`${key}: external request ${JSON.stringify(external)}`);
    assert.equal(ws.length,0,`${key}: websocket`);assert.equal(externalNav.length,0,`${key}: navigation ${JSON.stringify(externalNav)}`);
    return {pass:true,externalRequests:0,sentinelLeaked:false,websockets:0,externalNavigations:0,requests:req.map(x=>({url:x.url,type:x.type}))};
  }};
}
async function fillMeta(page,hostile=false){
  const f=page.locator('[data-meta-form]');
  const v={book:hostile?`Niña & <script>${SENTINEL}</script>`:`La casa ${SENTINEL}`,author:'Ana «Ejemplo»',site:'Ana Ejemplo',url:'https://example.test/libro/',description:hostile?`"</script>" & < > ${SENTINEL}`:`Descripción editorial ${SENTINEL}`,image:`https://assets.example.test/${SENTINEL}.webp`,image_alt:hostile?`"><svg onload=alert(1)> ${SENTINEL}`:'Portada de prueba',isbn:'9781234567890',release_date:'2026-09-03',author_url:'https://example.test/ana/',x_site:'@ana'};
  for(const [n,x] of Object.entries(v))await f.locator(`[name="${n}"]`).fill(x);
  await f.locator('button[type="submit"]').click();await page.locator('[data-meta-output]').waitFor({state:'visible'});
}
function parseOutput(text){const m=text.match(/<script[^>]*>\s*([\s\S]*?)\s*<\/script>/);assert(m);return JSON.parse(m[1]);}
async function jsonMode(page,mode){
  await page.locator('#jsonld-mode').selectOption(mode);
  const d=mode==='profile'?{name:`Ana ${SENTINEL}`,url:'https://example.test/ana/',image:'https://example.test/a.webp',sameAs:'https://social.example.test/ana'}:
    mode==='book'?{name:`Libro ${SENTINEL}`,url:'https://example.test/libro/',description:'Descripción',image:'https://example.test/c.webp',isbn:'9781234567890',pages:'272',datePublished:'2026-09-03',bookFormat:'https://schema.org/Paperback',authorName:'Ana Ejemplo',authorUrl:'https://example.test/ana/',publisher:'Editorial Ejemplo'}:
    mode==='article'?{headline:`Artículo ${SENTINEL}`,url:'https://example.test/a/',image:'https://example.test/a.webp',datePublished:'2026-08-21',authorName:'Ana Ejemplo',authorUrl:'https://example.test/ana/'}:
    {name:`Firma ${SENTINEL}`,url:'https://example.test/e/',startDate:'2026-09-03T18:00',endDate:'2026-09-03T19:00',attendanceMode:'https://schema.org/OfflineEventAttendanceMode',locationName:'Librería Ejemplo',address:'Calle 1',city:'Madrid',country:'ES',organizerName:'Librería',organizerUrl:'https://example.test/'};
  for(const [n,x] of Object.entries(d)){const el=page.locator(`#jsonld-fields [name="${n}"]`);if(await el.count()){if(await el.evaluate(e=>e.tagName)==='SELECT')await el.selectOption(x);else await el.fill(x);}}
  await page.waitForTimeout(40);return parseOutput(await page.locator('#jsonld-output').textContent());
}
async function fillKit(page){
  const f=page.locator('form[data-publishing-processor]');
  const d={authorName:'Ana Ejemplo',contactEmail:'prensa@example.test',website:'https://example.test',bioShort:'Autora de prueba.',bioLong:'Biografía larga.',bookTitle:'La casa de prueba',publisher:'Editorial Ejemplo',isbn:'9781234567890',publicationDate:'2026-09-03',price:'16 €',purchaseUrl:'https://example.test/libro',bookDescription:`Texto controlado ${SENTINEL}`,interviewTopics:'Memoria\nEscritura'};
  for(const[n,x]of Object.entries(d))await f.locator(`[name="${n}"]`).fill(x);await f.locator('[name="assetPermission"]').selectOption('contact_only');
}
async function kitFiles(page){
  await page.locator('[name="authorPhotos"]').setInputFiles({name:'../../Ana ñandú.html',mimeType:'image/jpeg',buffer:jpg});
  await page.locator('[name="coverFiles"]').setInputFiles([{name:'portada ñandú.webp',mimeType:'image/webp',buffer:webp},{name:'portada ñandú.webp',mimeType:'image/webp',buffer:webp}]);
  await page.locator('[name="otherFiles"]').setInputFiles({name:'../../dossier.pdf',mimeType:'application/pdf',buffer:pdf});
}
async function downloadKit(page,file){const p=page.waitForEvent('download');await page.locator('[data-kit-submit]').click();const d=await p;if(file)await d.saveAs(file);else await d.cancel();await page.locator('[data-kit-summary]').waitFor({state:'visible'});}

await fs.mkdir(OUT,{recursive:true});
const report={privacy:{},functional:{jsonld:{},auditor:{}},noJs:{},responsive:{},accessibility:{},cls:{},fallbackFonts:{},screenshots:[]};
const browser=await chromium.launch({headless:true});
try{
  for(const[key,url]of tools){
    const c=await browser.newContext({viewport:{width:1024,height:900},acceptDownloads:true});const p=await c.newPage();const errors=[];p.on('pageerror',e=>errors.push(String(e)));let dialogs=0;p.on('dialog',d=>{dialogs++;d.dismiss();});
    await p.goto(ORIGIN+url,{waitUntil:'networkidle'});await ready(p);const g=networkGuard(p);g.start();
    if(key==='metadatos'){
      await fillMeta(p,true);const slot=p.locator('[data-og-image]');assert.equal(await slot.evaluate(e=>e.tagName),'DIV');assert.equal(await slot.getAttribute('src'),null);assert((await slot.textContent()).includes(SENTINEL));const code=await p.locator('[data-meta-code]').textContent();assert(!code.includes('<svg onload='));assert(code.includes('&lt;script&gt;'));
    }else if(key==='jsonld'){
      const out=await jsonMode(p,'book');assert.equal(out['@type'],'Book');assert(out.name.includes(SENTINEL));
    }else if(key==='kit'){
      await fillKit(p);await kitFiles(p);await downloadKit(p,path.join(OUT,'press-kit-qa.zip'));
    }else{
      const hostile=`<html><body><h1>Libro ${SENTINEL}</h1><p>Autora: Ana.</p><script>alert(1)</script><img src=x onerror=alert(1)><p>\"</script>\" & < ></p></body></html>`;
      await p.locator('[data-book-audit-html]').fill(hostile);await p.locator('[data-book-audit-url]').fill(`https://example.test/${SENTINEL}`);await p.locator('[data-book-audit-form] button[type="submit"]').click();await p.locator('[data-book-audit-results]').waitFor({state:'visible'});assert((await p.locator('[data-book-audit-detected]').textContent()).includes(SENTINEL));assert.equal(dialogs,0);
    }
    await p.waitForTimeout(200);report.privacy[key]=g.check(key);assert.deepEqual(errors,[],`${key}: ${errors.join(' | ')}`);await c.close();
  }
  console.log('INPUT EXFILTRATION: 0/4');

  {const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(ORIGIN+tools[0][1]);await ready(p);await fillMeta(p);const f=p.locator('[data-meta-form]');assert((await p.locator('.meta-card__label').first().textContent()).includes('orientativa'));assert((await p.locator('[data-meta-code]').textContent()).includes('book:isbn'));await f.locator('[name="description"]').fill('Descripción '.repeat(30));assert((await p.locator('[data-meta-warnings]').textContent()).includes('descripción es larga'));await f.locator('[name="url"]').fill('http://example.test/x');assert((await p.locator('[data-meta-warnings]').textContent()).includes('HTTPS'));await f.locator('[name="url"]').fill('https://exa mple.test');assert((await p.locator('[data-meta-warnings]').textContent()).includes('HTTPS'));report.functional.metadatos={pass:true,longDescription:true,httpRejected:true,invalidUrlRejected:true};await c.close();}

  {const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(ORIGIN+tools[1][1]);await ready(p);for(const m of ['profile','book','article','event']){const out=await jsonMode(p,m);assert.equal(out['@context'],'https://schema.org');assert(out['@type']);if(m==='book')assert.equal(out.bookFormat,'https://schema.org/Paperback');if(m==='event')assert.equal(out.eventAttendanceMode,'https://schema.org/OfflineEventAttendanceMode');report.functional.jsonld[m]={pass:true,type:out['@type']};}await p.locator('#jsonld-mode').selectOption('profile');await p.locator('#f-url').fill('https://exa mple.test');assert((await p.locator('#jsonld-report').textContent()).includes('HTTPS válida'));await c.close();}

  async function kitError(files,needle,patch={}){const c=await browser.newContext({viewport:{width:1024,height:900},acceptDownloads:true}),p=await c.newPage();await p.goto(ORIGIN+tools[2][1]);await ready(p);await fillKit(p);for(const[n,x]of Object.entries(patch))await p.locator(`form[data-publishing-processor] [name="${n}"]`).fill(x);if(files)await files(p);await p.locator('form[data-publishing-processor]').dispatchEvent('submit');await p.waitForTimeout(80);assert((await p.locator('[data-kit-status]').textContent()).includes(needle),needle);await c.close();}
  await kitError(null,'email de prensa',{contactEmail:'x'});
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles(Array.from({length:11},(_,i)=>({name:`a${i}.pdf`,mimeType:'application/pdf',buffer:pdf}))),'máximo es 10');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles({name:'grande.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(12*1024*1024+1)}),'demasiado grande');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles([{name:'a.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)},{name:'b.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)},{name:'c.pdf',mimeType:'application/pdf',buffer:Buffer.alloc(9*1024*1024)}]),'superan 25 MiB');
  await kitError(async p=>p.locator('[name="otherFiles"]').setInputFiles({name:'mal.txt',mimeType:'text/plain',buffer:Buffer.from('x')}),'Formato no admitido');
  await kitError(null,'enlace oficial',{purchaseUrl:'javascript:alert(1)'});report.functional.kit={pass:true,errorCases:true};

  {const c=await browser.newContext({viewport:{width:1024,height:900}}),p=await c.newPage();await p.goto(ORIGIN+tools[3][1]);await ready(p);const cases={complete:`<html><head><meta name="description" content="${'Descripción '.repeat(20)}"><meta property="og:image" content="/cover.webp"><script type="application/ld+json">{"@type":"Book","name":"Libro","isbn":"9781234567890","author":{"@type":"Person","name":"Ana"}}</script></head><body><h1>Libro</h1><p>Autora: Ana. Ya disponible. ISBN 9781234567890. Editorial X. 200 páginas. Tapa blanda.</p><a href="/comprar">Comprar</a></body></html>`,incomplete,invalid:'<html><body><h1>Libro</h1><script type="application/ld+json">{"@type":"Book",}</script></body></html>',noJson:'<html><body><h1>Libro</h1><p>Autora: Ana. Ya disponible.</p></body></html>'};for(const[n,h]of Object.entries(cases)){await p.locator('[data-book-audit-html]').fill(h);await p.locator('[data-book-audit-form] button[type="submit"]').click();await p.locator('[data-book-audit-results]').waitFor({state:'visible'});report.functional.auditor[n]=true;}await p.locator('[data-book-audit-html]').fill('');await p.locator('[data-book-audit-form] button[type="submit"]').click();assert((await p.locator('[data-book-audit-status]').textContent()).includes('Pega el código HTML'));report.functional.auditor.empty=true;await c.close();}

  for(const[key,url]of tools){const c=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}}),p=await c.newPage();const r=await p.goto(ORIGIN+url,{waitUntil:'domcontentloaded'}),raw=await r.text();assert(raw.includes('<noscript>'));assert(raw.includes('JavaScript está desactivado.'));assert(await p.locator('h1').isVisible());const pr=p.locator('[data-publishing-processor]');assert.equal(await pr.getAttribute('inert'),'');assert.equal(await pr.getAttribute('aria-disabled'),'true');await noOverflow(p,`${key}@nojs`);report.noJs[key]={pass:true,noscript:true,inert:true};await c.close();}

  for(const[n,w,h]of viewports){report.responsive[n]={};for(const[key,url]of tools){const c=await browser.newContext({viewport:{width:w,height:h}}),p=await c.newPage();const err=[];p.on('pageerror',e=>err.push(String(e)));await p.goto(ORIGIN+url,{waitUntil:'domcontentloaded'});await ready(p);await noOverflow(p,`${key}@${n}`);assert.deepEqual(err,[]);report.responsive[n][key]=true;await c.close();}}

  for(const[key,url]of tools){const c=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'}),p=await c.newPage();await p.goto(ORIGIN+url,{waitUntil:'domcontentloaded'});await ready(p);assert(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches));await p.keyboard.press('Tab');assert(await p.evaluate(()=>document.activeElement?.classList.contains('skip-link')));let focus=false;for(let i=0;i<45;i++){await p.keyboard.press('Tab');const x=await p.evaluate(()=>{const e=document.activeElement,cs=e instanceof HTMLElement?getComputedStyle(e):null;return e instanceof HTMLElement&&Boolean(e.closest('[data-publishing-processor]'))&&(cs.outlineStyle!=='none'||cs.boxShadow!=='none');});if(x){focus=true;break;}}assert(focus,`${key}: focus`);await p.evaluate(h=>new Promise((ok,bad)=>{const l=document.createElement('link');l.rel='stylesheet';l.href=h;l.onload=ok;l.onerror=bad;document.head.append(l);}),ORIGIN+'/qa/text-spacing-publishing.css');await p.waitForTimeout(50);await noOverflow(p,`${key}@spacing`);const s=await c.newCDPSession(p);await s.send('Emulation.setPageScaleFactor',{pageScaleFactor:2});assert(await p.locator('h1').isVisible());report.accessibility[key]={keyboard:true,focusVisible:true,textSpacing:true,zoom200:true,reducedMotion:true};await c.close();}

  for(const[key,url]of tools){const c=await browser.newContext({viewport:{width:1350,height:940}}),p=await c.newPage();await p.addInitScript(()=>{window.__cls=0;new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value;}).observe({type:'layout-shift',buffered:true});});await p.goto(ORIGIN+url,{waitUntil:'networkidle'});await p.waitForTimeout(600);const cls=await p.evaluate(()=>window.__cls||0);assert(cls<=.10,`${key}: CLS ${cls}`);report.cls[key]=cls;await c.close();}
  for(const[key,url]of tools){const c=await browser.newContext({viewport:{width:320,height:760}}),p=await c.newPage();await p.route('**/assets/fonts/**',r=>r.abort());await p.goto(ORIGIN+url);await ready(p);await noOverflow(p,`${key}@fallback`);report.fallbackFonts[key]=true;await c.close();}

  async function shot(key,w,h,file){const url=tools.find(x=>x[0]===key)[1],c=await browser.newContext({viewport:{width:w,height:h},acceptDownloads:true}),p=await c.newPage();await p.goto(ORIGIN+url,{waitUntil:'networkidle'});await ready(p);if(key==='metadatos'){await fillMeta(p);await p.locator('[data-meta-output]').scrollIntoViewIfNeeded();}if(key==='jsonld'){await jsonMode(p,'book');await p.locator('#jsonld-output').scrollIntoViewIfNeeded();}if(key==='kit'){await fillKit(p);await kitFiles(p);await downloadKit(p);await p.locator('[data-kit-summary]').scrollIntoViewIfNeeded();}if(key==='auditor'){await p.locator('[data-book-audit-html]').fill(incomplete);await p.locator('[data-book-audit-form] button[type="submit"]').click();await p.locator('[data-book-audit-results]').waitFor({state:'visible'});await p.locator('[data-book-audit-results]').scrollIntoViewIfNeeded();}await p.screenshot({path:path.join(OUT,file),fullPage:false});report.screenshots.push({key,w,h,file});await c.close();}
  for(const s of [['metadatos',1440,1000,'metadatos-1440-result.png'],['metadatos',390,844,'metadatos-390-result.png'],['jsonld',1440,1000,'jsonld-book-1440-result.png'],['jsonld',390,844,'jsonld-390-result.png'],['kit',1440,1000,'kit-1440-valid.png'],['kit',390,844,'kit-390-valid.png'],['auditor',1440,1000,'auditor-1440-result.png'],['auditor',390,844,'auditor-390-result.png']])await shot(...s);
  await fs.writeFile(path.join(OUT,'publishing-browser-qa-report.json'),JSON.stringify(report,null,2));console.log('PUBLISHING TOOLS BROWSER QA: OK');
}finally{await browser.close();}
