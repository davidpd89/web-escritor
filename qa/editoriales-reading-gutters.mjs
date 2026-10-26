import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE=process.env.QA_ORIGIN||process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const response=await page.goto(`${BASE}/editoriales/`,{waitUntil:'load'});
    assert.ok(response?.ok(),`/editoriales/ ${width}px: respuesta inválida`);
    const selectors=['main#contenido .tool-hero','main#contenido .tool-finder','main#contenido [data-editorial-card]'];
    const boxes=[];
    for(const selector of selectors){
      const locator=page.locator(selector).first();
      assert.equal(await locator.count(),1,`/editoriales/ ${width}px: falta ${selector}`);
      const r=await locator.boundingBox();
      assert.ok(r,`/editoriales/ ${width}px: ${selector} no tiene geometría`);
      assert.ok(r.x>=-1 && r.x+r.width<=width+1,`/editoriales/ ${width}px: ${selector} fuera de márgenes: ${JSON.stringify(r)}`);
      assert.ok(r.width>0,`/editoriales/ ${width}px: ${selector} sin anchura`);
      boxes.push(r);
    }
    assert.ok(boxes[1].y>=boxes[0].y,`/editoriales/ ${width}px: filtros antes del encabezado`);
    assert.ok(boxes[2].y>=boxes[1].y,`/editoriales/ ${width}px: resultados antes del buscador`);
    await page.close();
  }
  console.log('PASS editoriales reading gutters');
}finally{await browser.close();}
