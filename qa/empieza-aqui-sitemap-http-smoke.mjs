import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const route='/empieza-aqui/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  const page=await browser.newPage();
  const response=await page.goto(new URL(route,origin).href,{waitUntil:'domcontentloaded'});
  assert.equal(response?.status(),200,`${route}: HTTP ${response?.status()}`);
  const canonical=await page.locator('link[rel~="canonical"]').getAttribute('href');
  assert(canonical,`${route}: canonical ausente`);
  const sitemapResponse=await page.request.get(new URL('/sitemap.xml',origin).href);
  assert.equal(sitemapResponse.status(),200,'/sitemap.xml: respuesta HTTP incorrecta');
  const xml=await sitemapResponse.text();
  const result=await page.evaluate(({xml,canonical})=>{
    const document=new DOMParser().parseFromString(xml,'application/xml');
    const errors=document.getElementsByTagName('parsererror');
    if(errors.length)return {error:errors[0].textContent};
    const urls=[...document.getElementsByTagNameNS('*','url')];
    const matches=urls.filter(u=>[...u.children].some(c=>c.localName==='loc'&&c.textContent.trim()===canonical));
    return {count:matches.length,root:document.documentElement.localName};
  },{xml,canonical});
  assert(!result.error,`/sitemap.xml: XML inválido ${result.error}`);
  assert.equal(result.root,'urlset','/sitemap.xml: raíz inesperada');
  assert.equal(result.count,1,`${route}: canonical ${canonical} aparece ${result.count} veces en sitemap`);
  const robots=await page.locator('meta[name="robots" i]').evaluateAll(xs=>xs.map(x=>x.content));
  assert(!robots.some(x=>/(^|[,\s])noindex([,\s]|$)/i.test(x)),`${route}: sitemap anuncia documento noindex`);
  console.log('empieza-aqui sitemap HTTP: OK');
}finally{await browser.close();}
