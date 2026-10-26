import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.SITE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const route = '/accesibilidad/';

test('identidad SEO visible con tamaños reales y texto ampliado', async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [320,390,768,1280]) {
      for (const scale of [1,2]) {
        const context = await browser.newContext({viewport:{width,height:850}});
        try {
          const page = await context.newPage();
          const response = await page.goto(new URL(route,base).href,{waitUntil:'domcontentloaded'});
          assert.equal(response?.status(),200,`${route} ${width}px: HTTP`);
          await page.evaluate(scale=>{document.documentElement.style.fontSize=`${16*scale}px`;},scale);
          const result = await page.locator('main h1').evaluate(el=>{
            const box=el.getBoundingClientRect();
            const style=getComputedStyle(el);
            return {text:el.textContent.trim(),width:box.width,height:box.height,left:box.left,right:box.right,font:parseFloat(style.fontSize),visibility:style.visibility,display:style.display,scroll:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth};
          });
          const label=`${route} ${width}px escala ${scale}`;
          assert.match(result.text,/declaración de accesibilidad/i,`${label}: H1 ${result.text}`);
          assert.ok(result.width>0 && result.height>0,`${label}: caja ${JSON.stringify(result)}`);
          assert.ok(result.font>=16,`${label}: font-size ${result.font}px`);
          assert.notEqual(result.display,'none',`${label}: H1 oculto`);
          assert.notEqual(result.visibility,'hidden',`${label}: H1 invisible`);
          assert.ok(result.left>=-1 && result.right<=width+1,`${label}: caja horizontal ${result.left}..${result.right}`);
          assert.ok(result.scroll<=result.viewport+2,`${label}: overflow ${result.scroll}/${result.viewport}`);
        } finally { await context.close(); }
      }
    }
  } finally { await browser.close(); }
});