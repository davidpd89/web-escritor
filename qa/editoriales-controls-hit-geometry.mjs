import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const widths = [320, 768, 1024, 1440];
const selectors = ['[data-editoriales-search]', '[data-editoriales-genre]', '[data-editoriales-status]', '[data-editoriales-country]', '[data-editoriales-sort]', '[data-editoriales-direct]'];
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  for (const width of widths) {
    const page = await browser.newPage({viewport:{width,height:900}});
    const response = await page.goto(`${BASE}/editoriales/`,{waitUntil:'load'});
    assert.ok(response?.ok(), `/editoriales/ ${width}px: HTTP incorrecto`);
    for (const selector of selectors) {
      const control = page.locator(selector);
      assert.equal(await control.count(),1,`/editoriales/ ${width}px: falta ${selector}`);
      await control.scrollIntoViewIfNeeded();
      const geometry = await control.evaluate(el => {
        const r=el.getBoundingClientRect();
        const x=r.left+r.width/2, y=r.top+r.height/2;
        const hit=document.elementFromPoint(x,y);
        return {left:r.left,right:r.right,width:r.width,height:r.height,hit:hit===el||el.contains(hit)};
      });
      assert.ok(geometry.left>=-1 && geometry.right<=width+1,`/editoriales/ ${width}px ${selector}: márgenes ${geometry.left}/${geometry.right}`);
      assert.ok(geometry.width>0 && geometry.height>0,`/editoriales/ ${width}px ${selector}: control sin superficie`);
      assert.ok(geometry.hit,`/editoriales/ ${width}px ${selector}: centro interceptado`);
    }
    await page.close();
  }
  console.log('PASS editoriales controls hit geometry');
} finally {await browser.close();}
