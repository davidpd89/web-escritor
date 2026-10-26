import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.FERIAS_BASE_URL || process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const context = await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page = await context.newPage();
  const requested = new Set();
  page.on('request',r=>{if(r.resourceType()==='image') requested.add(new URL(r.url()).pathname);});
  const response = await page.goto(`${BASE}/ferias.html`,{waitUntil:'networkidle'});
  assert.ok(response?.ok(),`ferias.html: HTTP ${response?.status()}`);
  const distant = await page.locator('img').evaluateAll(images=>images.filter(img=>img.getBoundingClientRect().top>innerHeight*3).map(img=>({src:new URL(img.currentSrc||img.src).pathname,alt:img.alt})));
  assert.ok(distant.length>0,'ferias.html: no se localizaron imágenes documentales suficientemente alejadas del viewport');
  for(const image of distant) assert.ok(!requested.has(image.src),`ferias.html: imagen lejana descargada anticipadamente: ${image.src}`);
  const target=page.locator('img').filter({visible:true}).last();
  await target.scrollIntoViewIfNeeded();
  await target.evaluate(async img=>{if(!img.complete) await new Promise((resolve,reject)=>{img.addEventListener('load',resolve,{once:true});img.addEventListener('error',reject,{once:true});});});
  assert.ok(await target.evaluate(img=>img.naturalWidth>0),`ferias.html: la última imagen documental no se carga al entrar en pantalla`);
  await context.close();
} finally {await browser.close();}
