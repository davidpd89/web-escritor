import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true});
try {
  for(const width of [390,1280]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',serviceWorkers:'block'});
    const page=await context.newPage();
    const requests=[];
    page.on('request',request=>{if(request.resourceType()==='image'&&new URL(request.url()).origin===BASE)requests.push(request.url());});
    const response=await page.goto(BASE+'/libros/',{waitUntil:'load'});
    assert.equal(response?.status(),200,`/libros/ ${width}px: HTTP incorrecto`);
    const data=await page.evaluate(()=>[...document.images].map(img=>({src:img.currentSrc||img.src,hidden:!!img.closest('[hidden], [aria-hidden="true"]'),loading:img.loading,complete:img.complete,naturalWidth:img.naturalWidth})));
    const visible=data.filter(item=>!item.hidden);
    assert.ok(visible.length>0,`/libros/ ${width}px: no se encontraron imágenes visibles`);
    const requested=new Set(requests);
    for(const item of data.filter(item=>item.hidden)) {
      if(!item.src||visible.some(other=>other.src===item.src))continue;
      assert.ok(!requested.has(item.src),`/libros/ ${width}px: imagen oculta descargada: ${item.src}`);
    }
    const duplicates=requests.filter((url,i)=>requests.indexOf(url)!==i);
    assert.deepEqual(duplicates,[],`/libros/ ${width}px: peticiones duplicadas de imágenes: ${duplicates.join(', ')}`);
    await context.close();
  }
} finally {await browser.close();}
console.log('PASS media-initial-image-request-budget');