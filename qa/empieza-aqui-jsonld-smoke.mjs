import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const route='/empieza-aqui/';
const origin=process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  const page=await browser.newPage();
  const response=await page.goto(new URL(route,origin).href,{waitUntil:'domcontentloaded'});
  assert.equal(response?.status(),200,`${route}: respuesta HTTP incorrecta`);
  const data=await page.evaluate(()=>({canonical:document.querySelector('link[rel~="canonical"]')?.href,blocks:[...document.querySelectorAll('script[type="application/ld+json"]')].map(x=>x.textContent)}));
  assert(data.blocks.length>0,`${route}: no hay JSON-LD`);
  const nodes=[];
  for(const block of data.blocks){
    let value;
    try{value=JSON.parse(block);}catch(e){assert.fail(`${route}: JSON-LD inválido: ${e.message}`);}
    const queue=[value];
    while(queue.length){const item=queue.shift();if(Array.isArray(item)){queue.push(...item);continue;}if(!item||typeof item!=='object')continue;nodes.push(item);if(item['@graph'])queue.push(item['@graph']);}
  }
  const hasType=(n,t)=>[].concat(n['@type']||[]).includes(t);
  const web=nodes.filter(n=>hasType(n,'WebPage')&&n.url===data.canonical);
  assert.equal(web.length,1,`${route}: WebPage para ${data.canonical}: ${web.length}`);
  assert.equal(web[0]['@id'],data.canonical,`${route}: @id WebPage incorrecto`);
  const breadcrumbs=web[0].breadcrumb;
  const candidates=[...nodes.filter(n=>hasType(n,'BreadcrumbList')),...[].concat(breadcrumbs||[]).filter(n=>n&&typeof n==='object'&&hasType(n,'BreadcrumbList'))];
  assert(candidates.length>0,`${route}: falta BreadcrumbList`);
  const valid=candidates.some(b=>{
    const items=[].concat(b.itemListElement||[]);
    return items.length>=2&&items.every((x,i)=>x.position===i+1)&&items[0].item==='https://davidportodiaz.com/'&&items.at(-1).item===data.canonical&&items.at(-1).name==='Empieza aquí';
  });
  assert(valid,`${route}: breadcrumb sin Inicio > Empieza aquí o con posiciones incorrectas`);
  console.log('empieza-aqui JSON-LD: OK');
}finally{await browser.close();}
