import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const routes=['/','/empieza-aqui/','/mapa-del-sitio/'];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  const page=await browser.newPage();
  const records=[];
  for(const route of routes){
    const response=await page.goto(new URL(route,origin).href,{waitUntil:'domcontentloaded'});
    assert.equal(response?.status(),200,`${route}: HTTP ${response?.status()}`);
    const record=await page.evaluate(()=>({
      title:document.title.trim(),
      descriptions:[...document.querySelectorAll('meta[name="description" i]')].map(x=>x.content.trim()),
      canonicals:[...document.querySelectorAll('link[rel~="canonical" i]')].map(x=>x.href)
    }));
    assert(record.title,`${route}: title vacío`);
    assert.equal(record.descriptions.length,1,`${route}: descriptions ${record.descriptions.length}`);
    assert(record.descriptions[0],`${route}: description vacía`);
    assert.equal(record.canonicals.length,1,`${route}: canonicals ${record.canonicals.length}`);
    records.push({route,title:record.title,description:record.descriptions[0],canonical:record.canonicals[0]});
  }
  for(const field of ['title','description','canonical']){
    for(let i=0;i<records.length;i++)for(let j=i+1;j<records.length;j++){
      assert.notEqual(records[i][field],records[j][field],`${records[i].route} y ${records[j].route}: ${field} duplicado: ${records[i][field]}`);
    }
  }
  console.log('empieza-aqui SEO uniqueness: OK');
}finally{await browser.close();}
