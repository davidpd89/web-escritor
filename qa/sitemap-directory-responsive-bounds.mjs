import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});

try{
  for(const width of [320,768,1024,1440]){
    const page=await browser.newPage({viewport:{width,height:900}});
    const response=await page.goto(BASE+'/mapa-del-sitio/',{waitUntil:'load'});
    assert(response?.ok(),`/mapa-del-sitio/ ${width}px: HTTP ${response?.status()}`);
    await page.evaluate(()=>document.fonts.ready);
    const data=await page.evaluate(()=>{
      const links=[...document.querySelectorAll('main .directory-list a[href]')].filter(a=>a.getClientRects().length&&getComputedStyle(a).visibility!=='hidden');
      return {
        viewport:document.documentElement.clientWidth,
        scroll:document.documentElement.scrollWidth,
        links:links.map(a=>{
          const r=a.getBoundingClientRect();
          const p=a.closest('.directory-list').getBoundingClientRect();
          return {label:a.textContent.trim(),left:r.left,right:r.right,top:r.top,bottom:r.bottom,parentLeft:p.left,parentRight:p.right};
        })
      };
    });
    assert(data.links.length>0,`/mapa-del-sitio/ ${width}px: ningún enlace del directorio`);
    assert(data.scroll<=data.viewport+2,`/mapa-del-sitio/ ${width}px: scrollWidth=${data.scroll}, viewport=${data.viewport}`);
    for(const link of data.links){
      assert(link.left>=-1&&link.right<=width+1,`/mapa-del-sitio/ ${width}px: enlace ${link.label} fuera del viewport: ${JSON.stringify(link)}`);
      assert(link.left>=link.parentLeft-1&&link.right<=link.parentRight+1,`/mapa-del-sitio/ ${width}px: enlace ${link.label} sobresale de su lista: ${JSON.stringify(link)}`);
      assert(link.bottom>link.top,`/mapa-del-sitio/ ${width}px: enlace ${link.label} sin altura visible`);
    }
    await page.close();
  }
}finally{await browser.close();}
console.log('PASS sitemap-directory-responsive-bounds');