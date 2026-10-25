import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=process.env.QA_BASE_URL||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  for(const width of [320,390,600,601,768,1024,1025,1440]){
    const context=await browser.newContext({viewport:{width,height:900}});
    await context.route('**/*',route=>new URL(route.request().url()).origin===new URL(BASE).origin?route.continue():route.abort());
    const page=await context.newPage();
    await page.goto(BASE+'/libros/',{waitUntil:'load'});
    const covers=page.locator('main .books-stage img, main .books-stage-anthology img');
    assert.equal(await covers.count(),3,'Deben existir tres portadas editoriales');
    for(let i=0;i<await covers.count();i++){
      const img=covers.nth(i);
      await img.scrollIntoViewIfNeeded();
      const data=await img.evaluate(async el=>{
        try{await el.decode();}catch{}
        const rect=el.getBoundingClientRect();
        return {complete:el.complete,naturalWidth:el.naturalWidth,naturalHeight:el.naturalHeight,width:rect.width,height:rect.height,alt:el.alt,currentSrc:el.currentSrc};
      });
      assert.ok(data.complete&&data.naturalWidth>0&&data.naturalHeight>0,`Portada ${i} no decodificada a ${width}px: ${JSON.stringify(data)}`);
      assert.ok(data.alt.trim(),`Portada ${i} sin texto alternativo`);
      assert.ok(data.width>0&&data.height>0,`Portada ${i} sin dimensiones renderizadas`);
      assert.ok(data.currentSrc.startsWith(BASE+'/assets/'),`Portada ${i} utiliza recurso inesperado`);
    }
    await context.close();
  }
}finally{await browser.close();}
console.log('libros-cover-decode-matrix: OK');