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

const browser=await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
async function capture(route, viewport={width:1440,height:1000}, js=true, graceMs=null){
  const context=await browser.newContext({viewport,javaScriptEnabled:js});
  await context.clearCookies();
  // Real visitors get a 30s grace window (assets/analytics-consent-banner.js)
  // before a scroll/click/unload can implicitly accept -- QA overrides it to
  // 0 wherever it verifies that eventual behavior, so the suite doesn't need
  // a real 30s wait per flow.
  if(graceMs!==null) await context.addInitScript((ms)=>{ window.__ANALYTICS_CONSENT_GRACE_MS__=ms; }, graceMs);
  const page=await context.newPage(); const requests=[]; const consoleMessages=[];
  page.on('request',r=>{ if(external(r.url())) requests.push({url:r.url(),method:r.method(),postData:r.postData()}); });
  page.on('console',m=>consoleMessages.push(m.text()));
  await page.route(/https?:\/\/(?:gc\.zgo\.at|tracker\.metricool\.com)\/.*/, async r=>r.fulfill({status:200,contentType:'application/javascript',body:''}));
  await page.goto(BASE+route,{waitUntil:'networkidle'});
  const introEnter=page.locator('[data-intro-enter]').first();
  if(await introEnter.count()>0){ await introEnter.click(); await page.waitForTimeout(900); }
  return {context,page,requests,consoleMessages};
}
const expected={
  '/privacidad.html':{title:'Política de privacidad — David Porto Díaz',description:'Política de privacidad de davidportodiaz.com. Información sobre el tratamiento de datos personales conforme al RGPD.',canonical:'https://davidportodiaz.com/privacidad.html',h1:'Política de privacidad',dateModified:'2026-09-09',headings:['Responsable del tratamiento','Datos que recopilamos','Finalidad del tratamiento','Base legal','Conservación de datos','Tus derechos','Proveedores de servicios (encargados del tratamiento y otros responsables)','Cookies','Transferencias internacionales']},
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

// Minimal analytics-consent banner (2026-09-08): GoatCounter/Metricool never
// set cookies regardless of any choice here -- this banner is Clarity-only.
// A visitor with no stored decision must see it exactly once; their choice
// (granted/denied) must persist in localStorage and the banner must not
// reappear on a later visit ("returning user"). Regression coverage for the
// TDZ bug (const declared after its first use, silently swallowed by the
// function's own try/catch, so the banner reappeared on every load even
// after a real choice was stored) -- caught by this exact accept-then-reload
// sequence in a real headless browser, not the sandboxed preview tool used
// during development, which never reproduced it.
const home=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844});
const bannerSel='[data-analytics-consent-banner]';
assert(await home.page.locator(bannerSel).count()===1,'Consent banner missing on first visit');
assert((await home.page.locator(bannerSel).textContent()||'').includes('Clarity'),'Consent banner does not mention Clarity');
report.network.homeFresh=[...home.requests];
report.storage.homeFresh=await storageSnapshot(home.page);
const goatLoads=home.requests.filter(r=>r.url.includes('gc.zgo.at/count.js')).length;
const metricoolLoads=home.requests.filter(r=>r.url.includes('tracker.metricool.com/resources/be.js')).length;
assert(goatLoads<=1,'Duplicate GoatCounter script load'); assert(metricoolLoads<=1,'Duplicate Metricool script load');
// Storage is versioned+timestamped as of 2026-09-08 ({value,v,ts}), not a
// bare string -- AEPD guidance treats a stored cookie consent as stale after
// long enough that re-asking is warranted, so the value needs a recorded
// moment to expire from; this snapshot lets each read pull out .value while
// still asserting a real timestamp landed.
const readConsent=async(page)=>page.evaluate(()=>JSON.parse(localStorage.getItem('dp-analytics-consent')||'null'));
await home.page.getByRole('button',{name:'Acepto ayudarte'}).click();
assert(await home.page.locator(bannerSel).count()===0,'Consent banner did not dismiss after Acepto ayudarte');
const accepted=await readConsent(home.page);
assert(accepted&&accepted.value==='granted','Acepto ayudarte did not store granted');
assert(typeof accepted.ts==='number'&&accepted.ts>0,'Stored consent is missing a timestamp');
await home.page.reload({waitUntil:'networkidle'});
assert(await home.page.locator(bannerSel).count()===0,'Consent banner reappeared for a returning user who already accepted');
assert((await readConsent(home.page)).value==='granted','Accepted choice did not survive reload');
report.network.consent={managerPresent:true,accept:'stores {value:granted,v,ts}, banner dismissed, does not reappear on reload',reject:'checked in a separate context below',persistence:'localStorage dp-analytics-consent survives reload'};
await home.context.close();

const rejectFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844});
await rejectFlow.page.getByRole('button',{name:'Rechazo ayudarte'}).click();
assert(await rejectFlow.page.locator(bannerSel).count()===0,'Consent banner did not dismiss after Rechazo ayudarte');
assert((await readConsent(rejectFlow.page)).value==='denied','Rechazo ayudarte did not store denied');
await rejectFlow.page.reload({waitUntil:'networkidle'});
assert(await rejectFlow.page.locator(bannerSel).count()===0,'Consent banner reappeared for a returning user who already rejected');
assert((await readConsent(rejectFlow.page)).value==='denied','Rejected choice did not survive reload');
await rejectFlow.context.close();

// Implicit-accept-by-continued-use (2026-09-08, explicit site-owner decision):
// browsing the site without clicking either button is treated as acceptance.
// Only "Rechazo ayudarte" itself must ever produce denied -- every other
// interaction with the page (click elsewhere, scroll, navigate away) while
// the banner is showing must resolve to granted, and clicking a REAL banner
// button must never get short-circuited by this path (the implicit-accept
// listener explicitly ignores clicks that land inside the banner).
const scrollFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844},true,0);
await scrollFlow.page.mouse.wheel(0,400);
await scrollFlow.page.waitForTimeout(50);
assert(await scrollFlow.page.locator(bannerSel).count()===0,'Consent banner did not dismiss after scrolling without responding');
assert((await readConsent(scrollFlow.page)).value==='granted','Scrolling without responding did not store granted');
await scrollFlow.context.close();

const clickElsewhereFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844},true,0);
await clickElsewhereFlow.page.locator('body').click({position:{x:5,y:5}});
await clickElsewhereFlow.page.waitForTimeout(50);
assert(await clickElsewhereFlow.page.locator(bannerSel).count()===0,'Consent banner did not dismiss after a click elsewhere on the page');
assert((await readConsent(clickElsewhereFlow.page)).value==='granted','Clicking elsewhere without responding did not store granted');
await clickElsewhereFlow.context.close();

const navigateFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844},true,0);
// header-home, not "first a[href]": the actual first link in DOM order is a
// skip-link that stays off-screen until keyboard-focused, which Playwright's
// .click() refuses to act on ("element is outside of the viewport") -- this
// one is a real, always-visible link.
await navigateFlow.page.locator('a.header-home').first().click();
await navigateFlow.page.waitForLoadState('networkidle');
assert((await readConsent(navigateFlow.page)).value==='granted','Navigating away without responding did not store granted');
await navigateFlow.context.close();

// 30s grace window (2026-09-09, explicit site-owner instruction): a scroll
// arriving before the window elapses must NOT decide anything, so the
// visitor actually has time to see the banner. Uses the real default (no
// graceMs override) with a shortened window instead, so this exercises the
// exact same code path production uses, not a separate zero-grace mode.
// 3s, not a value close to capture()'s own goto/networkidle overhead: the
// grace clock starts the instant the banner script runs, before capture()
// even returns control here, so a window only slightly longer than that
// overhead flakes shut before the first assertion below ever gets to run.
const GRACE_TEST_MS=3000;
const graceFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844},true,GRACE_TEST_MS);
await graceFlow.page.mouse.wheel(0,400);
await graceFlow.page.waitForTimeout(50);
assert(await graceFlow.page.locator(bannerSel).count()===1,'Consent banner dismissed by a scroll inside the grace window');
assert((await readConsent(graceFlow.page))===null,'Scrolling inside the grace window stored a decision');
await graceFlow.page.waitForTimeout(GRACE_TEST_MS);
await graceFlow.page.mouse.wheel(0,400);
await graceFlow.page.waitForTimeout(50);
assert(await graceFlow.page.locator(bannerSel).count()===0,'Consent banner still present after the grace window elapsed and a further scroll');
assert((await readConsent(graceFlow.page)).value==='granted','Scrolling after the grace window elapsed did not store granted');
await graceFlow.context.close();

// Legacy bare-string values (pre-versioning, before 2026-09-08) must migrate
// on read rather than being treated as corrupt/absent -- otherwise every
// visitor who already chose under the old format gets re-asked once.
const migrateFlow=await capture('/las-manecillas-del-recuerdo/kindle/',{width:390,height:844});
await migrateFlow.page.evaluate(()=>localStorage.setItem('dp-analytics-consent','granted'));
await migrateFlow.page.reload({waitUntil:'networkidle'});
assert(await migrateFlow.page.locator(bannerSel).count()===0,'Legacy bare-string consent was not honored; banner reappeared');
const migrated=await readConsent(migrateFlow.page);
assert(migrated&&migrated.value==='granted'&&typeof migrated.ts==='number'&&migrated.ts>0,'Legacy bare-string consent was not migrated to the versioned shape');
await migrateFlow.context.close();

// Newsletter DOI contract: invalid/unchecked block; accepted POST is pending, never confirmed locally.
// Home no longer carries the footer newsletter fixture; lectores-beta keeps
// the explicit consent flow and is the canonical privacy-critical form.
let workerBodies=[];
const newsletterRoute=await capture('/lectores-beta/',{width:390,height:844});
await newsletterRoute.page.route(WORKER_RE,async r=>{ workerBodies.push(r.request().postData()||''); await r.fulfill({status:201,contentType:'application/json',body:'{"ok":true,"state":"pending_confirmation"}'}); });
const form=newsletterRoute.page.locator('#lectores-beta-form');
assert(await form.count()===1,'Lectores beta newsletter fixture missing');
const checkbox=newsletterRoute.page.locator('#lectores-beta-gdpr'); assert(!(await checkbox.isChecked()),'Newsletter checkbox prechecked');
assert(await newsletterRoute.page.locator('label[for="lectores-beta-gdpr"]').count()===1,'Newsletter checkbox lacks explicit label');
await newsletterRoute.page.locator('#lectores-beta-email').fill('not-an-email'); await checkbox.check(); await form.locator('button[type="submit"]').click(); await newsletterRoute.page.waitForTimeout(100); assert(workerBodies.length===0,'Invalid email submitted');
await checkbox.uncheck(); await newsletterRoute.page.locator('#lectores-beta-email').fill(SENTINEL); await form.locator('button[type="submit"]').click(); await newsletterRoute.page.waitForTimeout(100); assert(workerBodies.length===0,'Unchecked newsletter submitted');
await checkbox.check(); await form.locator('button[type="submit"]').click(); await newsletterRoute.page.waitForTimeout(250); assert(workerBodies.length===1,'Checked newsletter did not submit exactly once');
assert(await newsletterRoute.page.locator('#lectores-beta-form input[type="email"]').count()===0,'Pending DOI state not rendered');
assert((await newsletterRoute.page.locator('#lectores-beta-form').textContent()||'').includes('confirma'),'Pending DOI copy does not ask for confirmation');
const pendingStorage=await storageSnapshot(newsletterRoute.page); assert(!('nl-subscribed' in pendingStorage.localStorage),'Initial DOI request marked user as subscribed');
const payload=JSON.parse(workerBodies[0]); assert(payload.email===SENTINEL,'Newsletter email mismatch'); assert(payload.source==='lectores-beta','Newsletter source mismatch'); assert(!('consent' in payload),'Unexpected consent field sent to Worker');
const nonSubscriptionRequests=newsletterRoute.requests.filter(r=>!WORKER_RE.test(r.url));
const leakHaystack=JSON.stringify({requests:nonSubscriptionRequests,console:newsletterRoute.consoleMessages,url:newsletterRoute.page.url(),storage:await storageSnapshot(newsletterRoute.page)});
assert(!leakHaystack.includes(SENTINEL),'Email sentinel leaked outside intercepted subscription payload');
report.newsletter.pending={payloadKeys:Object.keys(payload),source:payload.source,uncheckedBlocked:true,invalidBlocked:true,sentinelLeak:false,prematureSubscribed:false};
report.storage.newsletterAfterSubscription=await storageSnapshot(newsletterRoute.page);
report.storage.cookies=await newsletterRoute.context.cookies(); await newsletterRoute.context.close();

async function newsletterErrorCase(name, handler, expectSuccess=false){
  const state=await capture('/lectores-beta/',{width:390,height:844}); let calls=0;
  await state.page.route(WORKER_RE,async r=>{calls++; await handler(r);});
  await state.page.locator('#lectores-beta-email').fill('qa-newsletter@example.test'); await state.page.locator('#lectores-beta-gdpr').check(); await state.page.locator('#lectores-beta-form button[type="submit"]').click(); await state.page.waitForTimeout(250);
  if(expectSuccess){ assert(await state.page.locator('#lectores-beta-form input[type="email"]').count()===0,`Newsletter ${name}: success state not rendered`); }
  else { assert(await state.page.locator('#lectores-beta-email').count()===1,`Newsletter ${name}: input lost on recoverable error`); assert((await state.page.locator('#lectores-beta-status').textContent()||'').trim().length>0,`Newsletter ${name}: no user-visible error`); }
  assert(calls===1,`Newsletter ${name}: expected one Worker request, got ${calls}`); report.newsletter[name]={calls,successState:expectSuccess}; await state.context.close();
}
await newsletterErrorCase('legacyDuplicate400',r=>r.fulfill({status:400,contentType:'application/json',body:'{"duplicate":true}'}));
await newsletterErrorCase('rateLimit429',r=>r.fulfill({status:429,contentType:'application/json',body:'{"error":"rate_limited"}'}));
await newsletterErrorCase('server500',r=>r.fulfill({status:500,contentType:'application/json',body:'{"error":"upstream"}'}));
await newsletterErrorCase('timeout',r=>r.abort('timedout'));

// Repeated submit events while the first request is pending must yield one POST.
{
  const state=await capture('/lectores-beta/',{width:390,height:844}); let calls=0;
  await state.page.route(WORKER_RE,async r=>{ calls++; await new Promise(resolve=>setTimeout(resolve,180)); await r.fulfill({status:201,contentType:'application/json',body:'{"ok":true,"state":"pending_confirmation"}'}); });
  await state.page.locator('#lectores-beta-email').fill('qa-double-submit@example.test'); await state.page.locator('#lectores-beta-gdpr').check();
  await state.page.locator('#lectores-beta-form').evaluate(formEl=>{ formEl.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); formEl.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); });
  await state.page.waitForTimeout(450); assert(calls===1,`Newsletter double submit: expected one Worker request, got ${calls}`);
  assert(await state.page.locator('#lectores-beta-form input[type="email"]').count()===0,'Newsletter double submit: pending state not rendered');
  report.newsletter.doubleSubmit={calls}; await state.context.close();
}

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
