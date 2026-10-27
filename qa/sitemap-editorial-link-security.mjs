import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage();
  const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
  assert(response?.ok(),`/mapa-del-sitio/: HTTP ${response?.status()}`);
  const links=await page.locator('main .directory-list a:visible').evaluateAll(nodes=>nodes.map(a=>({label:a.textContent.trim(),href:a.getAttribute('href'),url:a.href,active:a.querySelectorAll('script,iframe,object,embed,form,svg script').length})));
  assert(links.length>0,'/mapa-del-sitio/: ningún enlace editorial visible');
  for(const link of links){
    assert(link.label,`/mapa-del-sitio/: enlace sin texto: ${link.href}`);
    assert.equal(link.active,0,`/mapa-del-sitio/: ${link.label}: contenido activo en etiqueta`);
    const url=new URL(link.url);
    assert(['http:','https:'].includes(url.protocol),`/mapa-del-sitio/: ${link.label}: protocolo ${url.protocol}`);
    assert(!url.username&&!url.password,`/mapa-del-sitio/: ${link.label}: credenciales en ${link.url}`);
    assert(url.protocol==='https:'||url.origin===new URL(BASE).origin,`/mapa-del-sitio/: ${link.label}: destino HTTP externo ${link.url}`);
  }
} finally {await browser.close();}
console.log('PASS sitemap-editorial-link-security');