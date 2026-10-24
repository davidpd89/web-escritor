import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
async function open(ctx){const page=await ctx.newPage();await page.route('**/*',r=>r.request().url().startsWith(BASE)?r.continue():r.abort());await page.goto(BASE+'/fragmento/');return page;}
async function reach(page){await page.evaluate(()=>{scrollTo(0,(document.body.scrollHeight-innerHeight)*.7);dispatchEvent(new Event('scroll'));});await page.waitForTimeout(100);return page.locator('#sticky-cta').evaluate(e=>e.classList.contains('visible'));}
try {
  const a=await browser.newContext({reducedMotion:'reduce'});
  const page=await open(a);
  assert.equal(await reach(page),true);
  await page.locator('#sticky-cta-close').click();
  assert.equal(await page.evaluate(()=>sessionStorage.getItem('sticky-cta-dismissed')),'1');
  await page.reload();
  assert.equal(await reach(page),false,'La barra reaparece después de recargar');
  await a.close();
  const b=await browser.newContext({reducedMotion:'reduce'});
  const fresh=await open(b);
  assert.equal(await fresh.evaluate(()=>sessionStorage.getItem('sticky-cta-dismissed')),null);
  assert.equal(await reach(fresh),true,'La nueva sesión hereda un cierre anterior');
  await b.close();
} finally {await browser.close();}
console.log('fragmento-sticky-session-scope: OK');