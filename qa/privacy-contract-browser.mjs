import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.PRIVACY_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.PRIVACY_ARTIFACT_DIR || 'artifacts/privacy-legal';
const SENTINEL = 'privacy.qa.582931@example.test';
const WORKER_RE = /^https:\/\/subscribe\.davidpd89\.workers\.dev(?:\/.*)?$/;
await fs.mkdir(OUT, { recursive: true });
const report = { base: BASE, generatedAt: new Date().toISOString(), legal: {}, network: {}, storage: {}, sourceInventory: {}, newsletter: {}, notes: [] };
function assert(ok, message){ if(!ok) throw new Error(message); }
function external(url){ try { return new URL(url).origin !== new URL(BASE).origin; } catch { return false; } }
async function walk(dir){ const out=[]; for(const ent of await fs.readdir(dir,{withFileTypes:true})){ if(['.git','node_modules','artifacts','.lighthouseci'].includes(ent.name)) continue; const p=path.join(dir,ent.name); if(ent.isDirectory()) out.push(...await walk(p)); else if(/\.(?:html|js|mjs|json|toml|yml|yaml)$/i.test(ent.name)) out.push(p); } return out; }
async function storageSnapshot(page){ return page.evaluate(async()=>({localStorage:{...localStorage},sessionStorage:{...sessionStorage},indexedDB:await indexedDB.databases().then(x=>x.map(d=>d.name)),cacheStorage:'caches' in globalThis?await caches.keys():[]})); }
async function overflowDetails(page){ return page.evaluate(()=>{ const vw=document.documentElement.clientWidth; return [...document.querySelectorAll('body *')].map(el=>{const r=el.getBoundingClientRect();return {tag:el.tagName,cls:el.className||'',text:(el.textContent||'').trim().slice(0,80),left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width)}}).filter(x=>x.right>vw+1||x.left<-1).sort((a,b)=>b.right-a.right).slice(0,6); }); }
const files=await walk('.');
const patterns={goatcounter:/gc\.zgo\.at|goatcounter/i,metricool:/tracker\.metricool|beTracker/i,brevo:/brevo|sendinblue/i,cloudflare:/cloudflare|turnstile|workers\.dev/i,clarity:/clarity\.ms|Microsoft Clarity/i,googleAnalytics:/google-analytics|gtag\s*\(/i,facebookPixel:/fbq\s*\(|connect\.facebook\.net/i,hotjar:/hotjar|hj\s*\(/i,youtube:/youtube\.com\/embed/i,instagram:/instagram\.com\/embed/i};
for(const [provider,re] of Object.entries(patterns)){ const hits=[]; for(const file of files){ const text=await fs.readFile(file,'utf8'); if(re.test(text)) hits.push(file.replaceAll('\\','/')); } report.sourceInventory[provider]=hits; }

const browser=await chromium.launch({headless:true});
async function capture(route, viewport={width:1440,height:1000}, js=true){
  const context=await browser.newContext({viewport,javaScriptEnabled:js});
  await context.clearCookies();
  const page=await context.newPage(); const requests=[]; const consoleMessages=[];
  page.on('request',r=>{ if(external(r.url())) requests.push({url:r.url(),method:r.method(),postData:r.postData()}); });
  page.on('console',m=>consoleMessages.push(m.text()));
  await page.route(/https?:\/\/(?:gc\.zgo\.at|tracker\.metricool\.com)\/.*/, async r=>r.fulfill({status:200,contentType:'application/javascript',body:''}));
  await page.goto(BASE+route,{waitUntil:'networkidle'});
  return {context,page,requests,consoleMessages};
}
const expected={
  '/privacidad.html':{title:'Política de privacidad — David Porto Díaz',description:'Política de privacidad de davidportodiaz.com. Información sobre el tratamiento de datos personales conforme al RGPD.',canonical:'https://davidportodiaz.com/privacidad.html',h1:'Política de privacidad',dateModified:'2026-08-21',headings:['Responsable del tratamiento','Datos que recopilamos','Finalidad del tratamiento','Base legal','Conservación de datos','Tus derechos','Proveedores de servicios (encargados del tratamiento)','Cookies','Transferencias internacionales']},
  '/aviso-legal.html':{title:'Aviso legal — David Porto Díaz',description:'Aviso legal de davidportodiaz.com. Responsable, propiedad intelectual, enlaces afiliados y limitación de responsabilidad.',canonical:'https://davidportodiaz.com/aviso-legal.html',h1:'Aviso legal',headings:['1. Responsable del sitio web','2. Objeto y finalidad','3. Propiedad intelectual','4. Marca y nombre comercial','5. Enlaces a terceros','6. Aviso de enlaces de afiliado','7. Exención de responsabilidad','8. Ley aplicable y jurisdicción','9. Datos personales','10. Contacto']}
};
const viewports=[[320,720],[390,844],[768,1024],[1024,768],[1440,1000],[1728,1100],[844,390]];
for(const [route,meta] of Object.entries(expected)){
  const {context,page,requests}=await capture(route);
  assert(await page.title()===meta.title,`${route}: title drift`);
  assert(await page.locator('meta[name="description"]').getAttribute('content')===meta.description,`${route}: description drift`);
  assert(await page.locator('meta[name="robots"]').getAttribute('content')==='noindex, follow',`${route}: robots drift`);
  assert(await page.locator('link[rel="canonical"]').getAttribute('href')===meta.canonical,`${route}: canonical drift`);
  assert((await page.locator('h1').allTextContents()).join('').trim()===meta.h1,`${route}: H1 drift`);
  assert(JSON.stringify((await page.locator('.legal-prose h2').allTextContents()).map(x=>x.trim()))===JSON.stringify(meta.headings),`${route}: legal heading inventory drift`);
  assert(await page.locator('link[href*="v1-legal.css"]').count()===1,`${route}: V1 legal CSS missing`);
  assert(await page.locator('link[href*="styles.css"]').count()===0,`${route}: legacy styles still loaded`);
  assert(await page.locator('script[src*="script.js"]').count()===0,`${route}: legacy runtime still loaded`);
  assert(await page.locator('script[type="speculationrules"]').count()===0,`${route}: speculationrules still present`);
  assert(await page.locator('link[rel="preconnect"][href*="goatcounter"],link[rel="preconnect"][href*="gc.zgo.at"]').count()===0,`${route}: analytics preconnect before action`);
  if(meta.dateModified){ const ld=await page.locator('script[type="application/ld+json"]').textContent(); assert(ld?.includes(`"dateModified":"${meta.dateModified}"`),`${route}: dateModified drift`); }
  for(const a of await page.locator('a[target="_blank"]').all()){ const rel=(await a.getAttribute('rel')||'').split(/\s+/); assert(rel.includes('noopener'),`${route}: target=_blank without noopener`); }
  assert(requests.length===0,`${route}: external request on fresh legal visit: ${requests.map(x=>x.url).join(', ')}`);
  report.network[route]={fresh:[...requests]};
  await page.locator('[data-explore-open]').focus(); await page.keyboard.press('Enter'); assert(await page.locator('#explore-dialog').evaluate(el=>el.open),`${route}: Explore keyboard open failed`); await page.keyboard.press('Escape');
  await page.emulateMedia({media:'print'}); assert(await page.locator('main').isVisible(),`${route}: main hidden in print`); assert(await page.locator('.site-header').evaluate(el=>getComputedStyle(el).display)==='none',`${route}: header visible in print`); await page.emulateMedia({media:'screen'});
  report.legal[route]={externalFresh:requests.length,sections:await page.locator('.legal-prose>section').count(),headings:meta.headings};
  await context.close();
  for(const [w,h] of viewports){ const shot=await capture(route,{width:w,height:h}); const overflow=await shot.page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth); if(overflow>1){ const offenders=await overflowDetails(shot.page); await shot.context.close(); throw new Error(`${route}: horizontal overflow ${w}x${h} (${overflow}px): ${JSON.stringify(offenders)}`); } await shot.context.close(); }
  for(const w of [1440,390]){ const shot=await capture(route,{width:w,height:w===390?844:1000}); await shot.page.screenshot({path:path.join(OUT,`${route.includes('privacidad')?'privacidad':'aviso'}-${w}.png`),fullPage:true}); await shot.context.close(); }
  const nojs=await capture(route,{width:390,height:844},false); assert(await nojs.page.locator('h1').isVisible(),`${route}: no-JS H1 invisible`); assert(nojs.requests.length===0,`${route}: no-JS external request`); await nojs.context.close();
  const spacing=await capture(route,{width:320,height:720}); await spacing.page.addStyleTag({content:'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'}); const spacingOverflow=await spacing.page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth); assert(spacingOverflow<=1,`${route}: text-spacing overflow (${spacingOverflow}px)`); await spacing.context.close();
}

// Current project contract has no analytics consent manager/banner. Verify state instead of inventing accept/reject UI.
const home=await capture('/',{width:390,height:844});
const consentCount=await home.page.locator('[data-consent],#cookie-banner,.cookie-banner,[class*="consent-banner"]').count();
assert(consentCount===0,'Unexpected consent manager/banner appeared');
report.network.consent={managerPresent:false,accept:'N/A — no consent manager in current technical contract',reject:'N/A — no consent manager in current technical contract',persistence:'N/A'};
report.network.homeFresh=[...home.requests];
report.storage.homeFresh=await storageSnapshot(home.page);
const goatLoads=home.requests.filter(r=>r.url.includes('gc.zgo.at/count.js')).length;
const metricoolLoads=home.requests.filter(r=>r.url.includes('tracker.metricool.com/resources/be.js')).length;
assert(goatLoads<=1,'Duplicate GoatCounter script load'); assert(metricoolLoads<=1,'Duplicate Metricool script load');

// Newsletter contract: unchecked/invalid must block; checked may POST only after explicit action. Intercept Worker — never send a live email.
let workerBodies=[];
await home.page.route(WORKER_RE,async r=>{ workerBodies.push(r.request().postData()||''); await r.fulfill({status:201,contentType:'application/json',body:'{"ok":true}'}); });
const form=home.page.locator('#newsletter-form-home');
assert(await form.count()===1,'Home newsletter fixture missing');
const checkbox=home.page.locator('#nl-gdpr-home'); assert(!(await checkbox.isChecked()),'Newsletter checkbox prechecked');
assert(await home.page.locator('label[for="nl-gdpr-home"]').count()===1,'Newsletter checkbox lacks explicit label');
await home.page.locator('#nl-email-home').fill('not-an-email'); await checkbox.check(); await form.locator('button[type="submit"]').click(); await home.page.waitForTimeout(100); assert(workerBodies.length===0,'Invalid email submitted');
await checkbox.uncheck(); await home.page.locator('#nl-email-home').fill(SENTINEL); await form.locator('button[type="submit"]').click(); await home.page.waitForTimeout(100); assert(workerBodies.length===0,'Unchecked newsletter submitted');
await checkbox.check(); await form.locator('button[type="submit"]').click(); await home.page.waitForTimeout(250); assert(workerBodies.length===1,'Checked newsletter did not submit exactly once');
const payload=JSON.parse(workerBodies[0]); assert(payload.email===SENTINEL,'Newsletter email mismatch'); assert(payload.source==='home','Newsletter source mismatch'); assert(!('consent' in payload),'Unexpected consent field sent to Worker');
const nonSubscriptionRequests=home.requests.filter(r=>!WORKER_RE.test(r.url));
const leakHaystack=JSON.stringify({requests:nonSubscriptionRequests,console:home.consoleMessages,url:home.page.url(),storage:await storageSnapshot(home.page)});
assert(!leakHaystack.includes(SENTINEL),'Email sentinel leaked outside intercepted subscription payload');
report.newsletter.success={payloadKeys:Object.keys(payload),source:payload.source,uncheckedBlocked:true,invalidBlocked:true,sentinelLeak:false};
report.storage.homeAfterSubscription=await storageSnapshot(home.page);
report.storage.cookies=await home.context.cookies(); await home.context.close();

async function newsletterErrorCase(name, handler, expectSuccess=false){
  const state=await capture('/',{width:390,height:844}); let calls=0;
  await state.page.route(WORKER_RE,async r=>{calls++; await handler(r);});
  await state.page.locator('#nl-email-home').fill('qa-newsletter@example.test'); await state.page.locator('#nl-gdpr-home').check(); await state.page.locator('#newsletter-form-home button[type="submit"]').click(); await state.page.waitForTimeout(250);
  if(expectSuccess){ assert(await state.page.locator('#newsletter-form-home input[type="email"]').count()===0,`Newsletter ${name}: success state not rendered`); }
  else { assert(await state.page.locator('#nl-email-home').count()===1,`Newsletter ${name}: input lost on recoverable error`); assert((await state.page.locator('#nl-status-home').textContent()||'').trim().length>0,`Newsletter ${name}: no user-visible error`); }
  assert(calls===1,`Newsletter ${name}: expected one Worker request, got ${calls}`); report.newsletter[name]={calls,successState:expectSuccess}; await state.context.close();
}
await newsletterErrorCase('duplicate',r=>r.fulfill({status:400,contentType:'application/json',body:'{"duplicate":true}'}),true);
await newsletterErrorCase('rateLimit429',r=>r.fulfill({status:429,contentType:'application/json',body:'{"error":"rate_limited"}'}));
await newsletterErrorCase('server500',r=>r.fulfill({status:500,contentType:'application/json',body:'{"error":"upstream"}'}));
await newsletterErrorCase('timeout',r=>r.abort('timedout'));

// Assistant read-only: a local query must not load Turnstile or create the remote session id.
const assistant=await capture('/asistente/',{width:390,height:844});
assert(!assistant.requests.some(r=>r.url.includes('challenges.cloudflare.com')),'Assistant loaded Turnstile before remote need');
await assistant.page.locator('[data-assistant-query]').fill('¿Dónde puedo leer un fragmento gratis?'); await assistant.page.locator('[data-assistant-submit]').click(); await assistant.page.waitForTimeout(600);
assert(!assistant.requests.some(r=>r.url.includes('challenges.cloudflare.com')),'Assistant local query loaded Turnstile');
const assistantStorage=await storageSnapshot(assistant.page); assert(!('davidporto-assistant-session-v1' in assistantStorage.sessionStorage),'Assistant local query created remote session id');
report.network.assistantLocal=[...assistant.requests]; report.storage.assistantLocal=assistantStorage; await assistant.context.close();

await fs.writeFile(path.join(OUT,'privacy-contract-report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({ok:true,legal:report.legal,newsletter:report.newsletter,consent:report.network.consent},null,2));
await browser.close();
