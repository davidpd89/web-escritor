import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage({viewport:{width:390,height:800}});
  let posts=0;
  await page.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
  page.on('request',r=>{if(r.url().includes('/api/assistant')&&r.method()==='POST')posts++;});
  await page.goto(origin+'/asistente/',{waitUntil:'domcontentloaded'});
  await page.locator('[data-assistant-query]').fill('Quiero leer un fragmento');
  await page.locator('[data-assistant-submit]').click();
  const chips=page.locator('.assistant-message--assistant .assistant-reply-chip');
  await chips.first().waitFor();
  assert.equal(await chips.count(),2);
  await chips.filter({hasText:'Samuel'}).click();
  await page.locator('.assistant-message--user').nth(1).waitFor();
  await page.locator('.assistant-message__sources a[href="/fragmento/"]').waitFor();
  assert.equal(await page.locator('.assistant-message--user').count(),2);
  const last=page.locator('.assistant-message--assistant').last();
  assert.match(await last.innerText(),/primer capítulo/i);
  assert.equal(await last.locator('.assistant-message__sources a[href="/fragmento/"]').count(),1);
  assert.equal(posts,0);
  assert.equal(await page.locator('[data-pending="true"]').count(),0);
} finally {await browser.close();}
console.log('assistant-multiturn-browser: OK');