import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.SITE_BASE_URL||'http://127.0.0.1:8765').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{
  await Promise.all(Array.from({length:8},async(_,i)=>{
    const width=i%2?320:390;
    const context=await browser.newContext({viewport:{width,height:900}});
    try{
      const page=await context.newPage();
      const response=await page.goto(`${BASE}/mapa-del-sitio/`,{waitUntil:'load'});
      assert.equal(response?.status(),200,`mapa-del-sitio ${width}px visita ${i}: HTTP ${response?.status()}`);
      const result=await page.evaluate(()=>{
        const links=[...document.querySelectorAll('main .directory-list a')];
        return {count:links.length,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,links:links.map(a=>{const s=getComputedStyle(a),r=a.getBoundingClientRect();return {text:a.textContent.trim(),height:r.height,scroll:a.scrollWidth,client:a.clientWidth,whiteSpace:s.whiteSpace,overflow:s.overflow,textOverflow:s.textOverflow};})};
      });
      assert(result.count>=15,`mapa-del-sitio ${width}px: solo ${result.count} enlaces`);
      assert(result.overflow<=1,`mapa-del-sitio ${width}px: desbordamiento ${result.overflow}px`);
      for(const a of result.links){
        assert(a.text,`mapa-del-sitio ${width}px: enlace sin texto`);
        assert(a.height>0,`mapa-del-sitio ${width}px: ${a.text} altura nula`);
        assert(a.scroll<=a.client+2||a.overflow==='visible',`mapa-del-sitio ${width}px: ${a.text} desbordado`);
        assert(!(a.whiteSpace==='nowrap'&&a.textOverflow==='ellipsis'),`mapa-del-sitio ${width}px: ${a.text} truncado`);
      }
    }finally{await context.close();}
  }));
  console.log('PASS directory link reflow under load');
}finally{await browser.close();}