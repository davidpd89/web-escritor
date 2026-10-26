import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=(process.env.BASE_URL||process.env.QA_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage({viewport:{width:320,height:900},reducedMotion:'reduce'});
  const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
  assert(response?.ok(),`/mapa-del-sitio/: HTTP ${response?.status()}`);
  await page.locator('.findability-directory').waitFor({state:'visible'});
  await page.addStyleTag({content:'html{font-size:200%!important}body *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'});
  await page.evaluate(async()=>{await document.fonts.ready;await new Promise(resolve=>requestAnimationFrame(resolve));});
  const result=await page.evaluate(()=>{
    const links=[...document.querySelectorAll('.findability-directory a')];
    const bad=links.filter(el=>{
      const r=el.getBoundingClientRect();
      return r.width===0||r.height===0||r.left < -1||r.right>innerWidth+1||el.scrollWidth>el.clientWidth+2;
    }).map(el=>({text:el.textContent.trim().slice(0,80),width:el.scrollWidth,available:el.clientWidth}));
    return {count:links.length,bad,scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth};
  });
  assert(result.count>20,`/mapa-del-sitio/: solo ${result.count} enlaces examinados`);
  assert(result.scrollWidth<=result.clientWidth+1,`/mapa-del-sitio/ 320px con texto 200%: desbordamiento ${result.scrollWidth}/${result.clientWidth}`);
  assert.deepEqual(result.bad,[],`/mapa-del-sitio/ 320px con texto 200%: enlaces recortados ${JSON.stringify(result.bad)}`);
} finally {await browser.close();}
console.log('PASS: findability text spacing reflow');