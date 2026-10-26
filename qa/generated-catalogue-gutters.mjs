import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base=(process.env.SITE_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [320,768,1024,1440]) {
    const page=await browser.newPage({viewport:{width,height:900}});
    const route='/recomendaciones/';
    const response=await page.goto(base+route,{waitUntil:'domcontentloaded'});
    assert.equal(response.status(),200,`${route} ${width}px: HTTP inesperado`);
    await page.locator('.catalogue-hero').waitFor({state:'visible'});
    await page.evaluate(()=>document.fonts.ready);
    const m=await page.evaluate(()=>{
      const hero=document.querySelector('.catalogue-hero');
      const root=document.documentElement;
      const r=hero.getBoundingClientRect();
      return {left:r.left,right:r.right,width:r.width,gutter:parseFloat(getComputedStyle(root).getPropertyValue('--page-gutter')),scroll:root.scrollWidth,viewport:root.clientWidth};
    });
    assert.ok(Number.isFinite(m.gutter)&&m.gutter>0,`${route} ${width}px: token --page-gutter inválido`);
    assert.ok(m.left>=-2&&m.right<=width+2,`${route} ${width}px: hero fuera de pantalla (${m.left}, ${m.right})`);
    assert.ok(m.width>=Math.min(220,width*.65),`${route} ${width}px: ancho de lectura ${m.width}px insuficiente`);
    assert.ok(m.scroll<=m.viewport+2,`${route} ${width}px: desbordamiento ${m.scroll-m.viewport}px`);
    await page.close();
  }
}finally{await browser.close();}
console.log('PASS: márgenes y ancho de catálogo en cuatro resoluciones');
