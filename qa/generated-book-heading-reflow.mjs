import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';

const base=(process.env.SITE_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
const books=JSON.parse(fs.readFileSync('data/reading-catalogue.json','utf8')).libros.filter(b=>b.estado==='publicado').sort((a,b)=>b.titulo.length-a.titulo.length).slice(0,8);
assert.ok(books.length,'No hay títulos publicados');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    for(const book of books){
      const route=`/recomendaciones/libros/${book.slug}/`;
      const response=await page.goto(base+route,{waitUntil:'domcontentloaded'});
      assert.equal(response.status(),200,`${route} ${width}px: HTTP inesperado`);
      const heading=page.locator('.catalogue-book-heading h1');
      await heading.waitFor({state:'visible'});
      await page.evaluate(()=>document.fonts.ready);
      const m=await heading.evaluate(el=>{
        const r=el.getBoundingClientRect(),p=el.parentElement.getBoundingClientRect(),s=getComputedStyle(el);
        return {text:el.textContent.trim(),left:r.left,right:r.right,width:r.width,height:r.height,parentLeft:p.left,parentRight:p.right,font:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),scroll:el.scrollWidth,client:el.clientWidth};
      });
      assert.equal(m.text,book.titulo,`${route} ${width}px: título visible diferente del JSON`);
      assert.ok(m.left>=m.parentLeft-2&&m.right<=m.parentRight+2,`${route} ${width}px: H1 fuera de su contenedor`);
      assert.ok(m.scroll<=m.client+2,`${route} ${width}px: H1 desborda ${m.scroll-m.client}px`);
      assert.ok(m.font>=16&&m.height>=m.line*.9,`${route} ${width}px: tipografía H1 ilegible (${m.font}px, alto ${m.height}px)`);
    }
    await page.close();
  }
}finally{await browser.close();}
console.log(`PASS: reflujo de ${books.length} títulos largos`);
