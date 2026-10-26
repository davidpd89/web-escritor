import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_ORIGIN||process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const routes=['/editoriales/minotauro/','/editoriales/nocturna-ediciones/','/editoriales/duermevela-ediciones/'];
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  for(const route of routes)for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const response=await page.goto(`${BASE}${route}`,{waitUntil:'load'});
    assert.ok(response?.ok(),`${route} ${width}px: HTTP incorrecto`);
    const facts=await page.locator('.editorial-fact').evaluateAll(nodes=>nodes.map(el=>{
      const r=el.getBoundingClientRect();
      const dd=el.querySelector('dd');
      const v=dd?.getBoundingClientRect();
      return {label:el.querySelector('dt')?.textContent.trim(),left:r.left,right:r.right,valueLeft:v?.left,valueRight:v?.right,valueWidth:v?.width,visible:getComputedStyle(el).display!=='none'};
    }));
    assert.ok(facts.length>0,`${route} ${width}px: no se encontraron campos editoriales`);
    for(const fact of facts.filter(f=>f.visible)){
      assert.ok(fact.left>=-1 && fact.right<=width+1,`${route} ${width}px: campo ${fact.label} invade márgenes`);
      assert.ok(fact.valueWidth>0,`${route} ${width}px: valor ${fact.label} sin anchura`);
      assert.ok(fact.valueLeft>=-1 && fact.valueRight<=width+1,`${route} ${width}px: valor ${fact.label} fuera del viewport`);
    }
    await page.close();
  }
  console.log('PASS editoriales detail facts geometry');
}finally{await browser.close();}
