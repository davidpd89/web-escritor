import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const route = '/empieza-aqui/';
const canonical = 'https://davidportodiaz.com/empieza-aqui/';
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  const response = await page.goto(new URL(route,origin).href,{waitUntil:'domcontentloaded'});
  assert(response,`${route}: respuesta HTTP ausente`);
  assert.equal(response.status(),200,`${route}: HTTP ${response.status()}`);
  assert.match(response.headers()['content-type'] || '',/text\/html/i,`${route}: Content-Type incorrecto`);
  const seo = await page.evaluate(() => ({
    title:document.title.trim(),
    descriptions:[...document.querySelectorAll('meta[name="description" i]')].map(x=>x.content.trim()),
    canonicals:[...document.querySelectorAll('link[rel~="canonical" i]')].map(x=>x.href),
    robots:[...document.querySelectorAll('meta[name="robots" i]')].map(x=>x.content.toLowerCase()),
    h1:[...document.querySelectorAll('main h1')].map(x=>x.textContent.trim())
  }));
  assert(seo.title,`${route}: title vacío`);
  assert.equal(seo.descriptions.length,1,`${route}: número de descriptions ${seo.descriptions.length}`);
  assert(seo.descriptions[0],`${route}: description vacía`);
  assert.deepEqual(seo.canonicals,[canonical],`${route}: canonical incorrecta ${JSON.stringify(seo.canonicals)}`);
  assert.equal(seo.h1.length,1,`${route}: número de H1 ${seo.h1.length}`);
  assert(seo.h1[0],`${route}: H1 vacío`);
  assert(!seo.robots.some(x=>/(^|[,\s])noindex([,\s]|$)/i.test(x)),`${route}: robots noindex ${seo.robots}`);
  assert(!/(^|[,\s])noindex([,\s]|$)/i.test(response.headers()['x-robots-tag'] || ''),`${route}: X-Robots-Tag noindex`);
  console.log('empieza-aqui served SEO: OK');
} finally {await browser.close();}
