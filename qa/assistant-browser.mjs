import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const origin = process.env.QA_ORIGIN || "http://127.0.0.1:4173";
const out = process.env.QA_OUT || "qa-artifacts/assistant";
await fs.mkdir(out,{recursive:true});
const browser = await chromium.launch({headless:true});
const viewports = [[320,900],[390,900],[768,1000],[1024,900],[1440,1000],[1728,1000],[844,390]];
const shots = new Set(["320x900","390x900","768x1000","1024x900","1440x1000","1728x1000"]);
let failures=[];
const check=(cond,msg)=>{if(!cond) failures.push(msg)};

for (const [width,height] of viewports) {
  const context=await browser.newContext({viewport:{width,height},reducedMotion:"reduce"});
  const page=await context.newPage();
  let assistantPosts=0, turnstileRequests=0;
  page.on("request",r=>{ if(r.url().includes("/api/assistant")&&r.method()==="POST") assistantPosts++; if(r.url().includes("challenges.cloudflare.com")) turnstileRequests++; });
  await page.route("**/api/assistant/config",route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({protocol_version:1,ok:true,enabled:false,turnstile_site_key:""})}));
  await page.goto(`${origin}/asistente/`,{waitUntil:"networkidle"});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
  check(overflow<=1,`${width}x${height}: horizontal overflow ${overflow}px`);
  check(await page.locator('link[rel="canonical"]').getAttribute("href")==="https://davidportodiaz.com/asistente/",`${width}x${height}: canonical drift`);
  check(await page.locator('meta[name="robots"]').getAttribute("content")==="noindex,nofollow",`${width}x${height}: robots drift`);
  check(await page.locator("[data-assistant-example]").count()===3,`${width}x${height}: starter count`);
  await page.locator("[data-assistant-query]").fill("x");
  await page.locator("[data-assistant-submit]").click();
  check((await page.locator("[data-assistant-status]").innerText()).includes("concreta"),`${width}x${height}: one-char validation`);
  await page.locator("[data-assistant-query]").evaluate((el)=>{el.removeAttribute("maxlength");el.value="x".repeat(501)});
  await page.locator("[data-assistant-submit]").click();
  check((await page.locator("[data-assistant-status]").innerText()).includes("500"),`${width}x${height}: max+1 validation`);
  await page.locator("[data-assistant-query]").fill("ASSISTANT_QA_SECRET_582931");
  await page.locator("[data-assistant-submit]").click();
  await page.waitForTimeout(150);
  check(assistantPosts===0,`${width}x${height}: remote POST while disabled`);
  check(turnstileRequests===0,`${width}x${height}: Turnstile loaded while disabled`);
  const textResilience=await page.evaluate(()=>{const el=document.querySelector("[data-assistant-answer]");el.hidden=false;el.textContent="W".repeat(400);return document.documentElement.scrollWidth-document.documentElement.clientWidth});
  check(textResilience<=1,`${width}x${height}: long-token overflow`);
  if(shots.has(`${width}x${height}`)) await page.screenshot({path:path.join(out,`assistant-${width}x${height}.png`),fullPage:true});
  await context.close();
}

// Keyboard path and focus: example -> textarea, then status validation without moving focus elsewhere.
{
  const context=await browser.newContext({viewport:{width:390,height:900}}); const page=await context.newPage();
  await page.route("**/api/assistant/config",route=>route.fulfill({status:200,contentType:"application/json",body:'{"protocol_version":1,"ok":true,"enabled":false,"turnstile_site_key":""}'}));
  await page.goto(`${origin}/asistente/`); await page.locator("[data-assistant-example]").first().focus(); await page.keyboard.press("Enter");
  check(await page.locator("[data-assistant-query]").evaluate(el=>el===document.activeElement),"keyboard: starter must focus query");
  await context.close();
}

// 200% zoom-like viewport pressure + WCAG text spacing.
{
  const context=await browser.newContext({viewport:{width:640,height:900}}); const page=await context.newPage();
  await page.goto(`${origin}/asistente/`); await page.addStyleTag({content:"*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}"});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth); check(overflow<=1,`text-spacing/200%: overflow ${overflow}px`); await context.close();
}

// No-JS must still expose navigation and the explicit site-map fallback.
{
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:900}}); const page=await context.newPage(); await page.goto(`${origin}/asistente/`);
  check(await page.locator('a[href="/mapa-del-sitio/"]').count()>0,"no-JS: site-map fallback missing");
  check(await page.locator('nav[aria-label="Navegación principal"] a').count()>=3,"no-JS: primary navigation missing"); await context.close();
}
await browser.close();
if(failures.length){console.error("Assistant browser QA FAILED:\n- "+failures.join("\n- "));process.exit(1)}
console.log(`assistant-browser: OK (${viewports.length} viewports, 6 screenshots, keyboard, no-JS, reduced-motion, text-spacing)`);
