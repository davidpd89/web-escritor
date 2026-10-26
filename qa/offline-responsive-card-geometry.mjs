import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE = (process.env.QA_ORIGIN || process.env.SITE_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});

try {
  for (const width of [320,768,1024,1440]) {
    const page = await browser.newPage({viewport:{width,height:844}});
    const response = await page.goto(BASE+'/offline.html',{waitUntil:'load'});
    assert(response?.ok(),`/offline.html ${width}px: HTTP ${response?.status()}`);
    await page.evaluate(()=>document.fonts.ready);
    const result = await page.evaluate(()=>{
      const rect = selector => {
        const el = document.querySelector(selector);
        assertElement(el,selector);
        const r = el.getBoundingClientRect();
        return {left:r.left,right:r.right,width:r.width};
      };
      function assertElement(el,selector){if(!el)throw Error(`Elemento ausente: ${selector}`);}
      return {
        viewport:document.documentElement.clientWidth,
        scroll:document.documentElement.scrollWidth,
        main:rect('main'),
        card:rect('.offline-card'),
        heading:rect('#offline-title'),
        lead:rect('.lead'),
        actions:[...document.querySelectorAll('.actions button')].filter(el=>getComputedStyle(el).display!=='none').map(el=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right};})
      };
    });
    assert(result.scroll<=result.viewport+2,`/offline.html ${width}px: scrollWidth=${result.scroll}, viewport=${result.viewport}`);
    for(const name of ['main','card','heading','lead']){
      const r=result[name];
      assert(r.left>=-1&&r.right<=width+1,`/offline.html ${width}px: ${name} fuera del viewport: ${JSON.stringify(r)}`);
    }
    assert(result.card.left>=8,`/offline.html ${width}px: margen izquierdo insuficiente: ${result.card.left}px`);
    assert(width-result.card.right>=8,`/offline.html ${width}px: margen derecho insuficiente: ${width-result.card.right}px`);
    if(width>=1024)assert(result.main.width<=682,`/offline.html ${width}px: ancho de lectura ${result.main.width}px supera el máximo editorial`);
    for(const [i,r] of result.actions.entries())assert(r.left>=-1&&r.right<=width+1,`/offline.html ${width}px: acción ${i} desbordada: ${JSON.stringify(r)}`);
    await page.close();
  }
} finally {
  await browser.close();
}
console.log('PASS offline-responsive-card-geometry');