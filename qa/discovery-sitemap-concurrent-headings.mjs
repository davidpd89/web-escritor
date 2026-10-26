import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'http://127.0.0.1:8765').replace(/\/$/, '');
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  await Promise.all(Array.from({length:12}, async (_,i) => {
    const context = await browser.newContext({viewport:{width:i%2?390:1440,height:900}});
    try {
      const page = await context.newPage();
      const response = await page.goto(`${BASE}/mapa-del-sitio/`,{waitUntil:'load'});
      assert.equal(response?.status(),200,`mapa-del-sitio visita ${i}: HTTP ${response?.status()}`);
      const data = await page.locator('main').evaluate(main => {
        const headings = [...main.querySelectorAll('h1,.directory-group h2')];
        return headings.map(el => {
          const s=getComputedStyle(el),r=el.getBoundingClientRect();
          return {text:el.textContent.trim(),size:parseFloat(s.fontSize),line:parseFloat(s.lineHeight),height:r.height,scroll:el.scrollHeight,client:el.clientHeight};
        });
      });
      assert(data.length>=8,`mapa-del-sitio visita ${i}: solo ${data.length} encabezados`);
      for(const h of data){
        assert(h.text,`mapa-del-sitio visita ${i}: encabezado vacío`);
        assert(h.size>=12,`mapa-del-sitio visita ${i}: ${h.text} tamaño ${h.size}px`);
        assert(h.line>0,`mapa-del-sitio visita ${i}: ${h.text} interlineado inválido`);
        assert(h.height>0,`mapa-del-sitio visita ${i}: ${h.text} altura nula`);
        assert(h.scroll<=h.client+2,`mapa-del-sitio visita ${i}: ${h.text} recortado ${h.scroll}/${h.client}`);
      }
    } finally {await context.close();}
  }));
  console.log('PASS sitemap concurrent headings');
} finally {await browser.close();}