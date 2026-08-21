import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

const BASE = process.env.PRIVACY_BASE_URL || 'http://127.0.0.1:4173';
const OUT = process.env.PRIVACY_ARTIFACT_DIR || 'artifacts/privacy-legal';
const SENTINEL = 'privacy.qa.582931@example.test';
const WORKER_RE = /^https:\/\/subscribe\.davidpd89\.workers\.dev(?:\/.*)?$/;
await fs.mkdir(OUT, { recursive: true });
const report = { base: BASE, generatedAt: new Date().toISOString(), legal: {}, network: {}, storage: {}, sourceInventory: {}, notes: [] };
function assert(ok, message){ if(!ok) throw new Error(message); }
function external(url){ try { return new URL(url).origin !== new URL(BASE).origin; } catch { return false; } }
async function walk(dir){ const out=[]; for(const ent of await fs.readdir(dir,{withFileTypes:true})){ if(['.git','node_modules','artifacts','.lighthouseci'].includes(ent.name)) continue; const p=path.join(dir,ent.name); if(ent.isDirectory()) out.push(...await walk(p)); else if(/\.(?:html|js|mjs|json|toml|yml|yaml)$/i.test(ent.name)) out.push(p); } return out; }
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
  '/privacidad.html':{title:'Política de privacidad — David Porto Díaz',canonical:'https://davidportodiaz.com/privacidad.html',h1:'Política de privacidad',dateModified:'2026-08-21'},
  '/aviso-legal.html':{title:'Aviso legal — David Porto Díaz',canonical:'https://davidportodiaz.com/aviso-legal.html',h1:'Aviso legal'}
};
const viewports=[[320,720],[390,844],[768,1024],[1024,768],[1440,1000],[1728,1100],[844,390]];
for(const [route,meta] of Object.entries(expected)){
  const {context,page,requests}=await capture(route);
  assert(await page.title()===meta.title,`${route}: title drift`);
  assert(await page.locator('meta[name="robots"]').getAttribute('content')==='noindex, follow',`${route}: robots drift`);
  assert(await page.locator('link[rel="canonical"]').getAttribute('href')===meta.canonical,`${route}: canonical drift`);
  assert((await page.locator('h1').allTextContents()).join('').trim()===meta.h1,`${route}: H1 drift`);
  assert(await page.locator('link[href*="v1-legal.css"]').count()===1,`${route}: V1 legal CSS missing`);
  assert(await page.locator('link[href*="styles.css"]').count()===0,`${route}: legacy styles still loaded`);
  assert(await page.locator('script[src*="script.js"]').count()===0,`${route}: legacy runtime still loaded`);
  assert(await page.locator('script[type="speculationrules"]').count()===0,`${route}: speculationrules still present`);
  assert(await page.locator('link[rel="preconnect"][href*="goatcounter"],link[rel="preconnect"][href*="gc.zgo.at"]').count()===0,`${route}: analytics preconnect before action`);
  if(meta.dateModified){ const ld=await page.locator('script[type="application/ld+json"]').textContent(); assert(ld?.includes(`"dateModified":"${meta.dateModified}"`),`${route}: dateModified drift`); }
  assert(requests.length===0,`${route}: external request on fresh legal visit: ${requests.map(x=>x.url).join(', ')}`);
  report.network[route]={fresh:requests};
  await page.locator('[data-explore-open]').focus(); await page.keyboard.press('Enter'); assert(await page.locator('#explore-dialog').evaluate(el=>el.open),`${route}: Explore keyboard open failed`); await page.keyboard.press('Escape');
  await page.emulateMedia({media:'print'}); assert(await page.locator('main').isVisible(),`${route}: main hidden in print`); assert(await page.locator('.site-header').evaluate(el=>getComputedStyle(el).display)==='none',`${route}: header visible in print`); await page.emulateMedia({media:'screen'});
  report.legal[route]={externalFresh:requests.length,sections:await page.locator('.legal-prose>section').count()};
  await context.close();
  for(const [w,h] of viewports){ const shot=await capture(route,{width:w,height:h}); const overflow=await shot.page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth); assert(overflow<=1,`${route}: horizontal overflow ${w}x${h} (${overflow}px)`); await shot.context.close(); }
  for(const w of [1440,390]){ const shot=await capture(route,{width:w,height:w===390?844:1000}); await shot.page.screenshot({path:path.join(OUT,`${route.includes('privacidad')?'privacidad':'aviso'}-${w}.png`),fullPage:true}); await shot.context.close(); }
  const nojs=await capture(route,{width:390,height:844},false); assert(await nojs.page.locator('h1').isVisible(),`${route}: no-JS H1 invisible`); assert(nojs.requests.length===0,`${route}: no-JS external request`); await nojs.context.close();
  const spacing=await capture(route,{width:320,height:720}); await spacing.page.addStyleTag({content:'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'}); const spacingOverflow=await spacing.page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth); assert(spacingOverflow<=1,`${route}: text-spacing overflow`); await spacing.context.close();
}

// Current project contract has no analytics consent manager/banner. Verify state instead of inventing accept/reject UI.
const home=await capture('/',{width:390,height:844});
const consentCount=await home.page.locator('[data-consent],#cookie-banner,.cookie-banner,[class*="consent-banner"]').count();
assert(consentCount===0,'Unexpected consent manager/banner appeared');
report.network.consent={managerPresent:false,accept:'N/A — no consent manager in current technical contract',reject:'N/A — no consent manager in current technical contract',persistence:'N/A'};
report.network.homeFresh=home.requests;
const goatLoads=home.requests.filter(r=>r.url.includes('gc.zgo.at/count.js')).length;
const metricoolLoads=home.requests.filter(r=>r.url.includes('tracker.metricool.com/resources/be.js')).length;
assert(goatLoads<=1,'Duplicate GoatCounter script load'); assert(metricoolLoads<=1,'Duplicate Metricool script load');

// Newsletter contract: unchecked must block; checked may POST only after explicit action. Intercept Worker — never send a live email.
let workerBodies=[];
await home.page.route(WORKER_RE,async r=>{ workerBodies.push(r.request().postData()||''); await r.fulfill({status:201,contentType:'application/json',body:'{"ok":true}'}); });
const form=home.page.locator('#newsletter-form-home');
assert(await form.count()===1,'Home newsletter fixture missing');
const checkbox=home.page.locator('#nl-gdpr-home'); assert(!(await checkbox.isChecked()),'Newsletter checkbox prechecked');
await home.page.locator('#nl-email-home').fill(SENTINEL); await form.locator('button[type="submit"]').click(); await home.page.waitForTimeout(150); assert(workerBodies.length===0,'Unchecked newsletter submitted');
await checkbox.check(); await form.locator('button[type="submit"]').click(); await home.page.waitForTimeout(250); assert(workerBodies.length===1,'Checked newsletter did not submit exactly once');
const payload=JSON.parse(workerBodies[0]); assert(payload.email===SENTINEL,'Newsletter email mismatch'); assert(payload.source==='home','Newsletter source mismatch'); assert(!('consent' in payload),'Unexpected consent field sent to Worker');
const nonSubscriptionRequests=home.requests.filter(r=>!WORKER_RE.test(r.url));
const leakHaystack=JSON.stringify({requests:nonSubscriptionRequests,console:home.consoleMessages,url:home.page.url(),storage:await home.page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}))});
assert(!leakHaystack.includes(SENTINEL),'Email sentinel leaked outside intercepted subscription payload');
report.newsletter={payloadKeys:Object.keys(payload),source:payload.source,uncheckedBlocked:true,sentinelLeak:false};
report.storage.home=await home.page.evaluate(async()=>({localStorage:{...localStorage},sessionStorage:{...sessionStorage},indexedDB:await indexedDB.databases().then(x=>x.map(d=>d.name)),cacheStorage:'caches' in globalThis?await caches.keys():[]}));
report.storage.cookies=await home.context.cookies(); await home.context.close();

// Assistant read-only: initial/local path must not load Turnstile; session key is only expected on remote query path.
const assistant=await capture('/asistente/',{width:390,height:844});
assert(!assistant.requests.some(r=>r.url.includes('challenges.cloudflare.com')),'Assistant loaded Turnstile before remote need');
report.network.assistantInitial=assistant.requests;
report.storage.assistantInitial=await assistant.page.evaluate(()=>({localStorage:{...localStorage},sessionStorage:{...sessionStorage}}));
await assistant.context.close();

await fs.writeFile(path.join(OUT,'privacy-contract-report.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({ok:true,legal:report.legal,newsletter:report.newsletter,consent:report.network.consent},null,2));
await browser.close();
