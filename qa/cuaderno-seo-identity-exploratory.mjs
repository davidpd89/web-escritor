import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const SITE='https://davidportodiaz.com';
function collect(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?collect(path.join(dir,e.name)):e.name==='index.html'?[path.join(dir,e.name)]:[]);}
const files=collect('cuaderno');
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage();
 for(const file of files){
  const route='/'+path.dirname(file).replaceAll(path.sep,'/')+'/';
  const response=await page.goto(BASE+route);
  assert.equal(response.status(),200,route);
  const data=await page.evaluate(()=>({
   canonical:[...document.querySelectorAll('link[rel="canonical"]')].map(e=>e.href),
   og:[...document.querySelectorAll('meta[property="og:url"]')].map(e=>e.content),
   robots:[...document.querySelectorAll('meta[name="robots"]')].map(e=>e.content.toLowerCase()),
   title:document.title.trim()
  }));
  const expected=SITE+route;
  assert.deepEqual(data.canonical,[expected],`${route}: canonical`);
  assert.deepEqual(data.og,[expected],`${route}: og:url`);
  assert.ok(data.title.length>0,`${route}: title vacío`);
  assert.equal(data.robots.length,1,`${route}: robots duplicado o ausente`);
  assert.ok(!data.robots[0].split(',').some(t=>t.trim()==='noindex'),`${route}: noindex inesperado`);
 }
 console.log(`PASS cuaderno SEO identity: ${files.length} páginas`);
}finally{await browser.close();}
