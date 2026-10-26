import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const widths = [320, 768, 1024, 1440];
const root = 'editoriales';
const routes = ['/editoriales/', ...fs.readdirSync(root, {withFileTypes:true}).filter(e => e.isDirectory() && fs.existsSync(path.join(root,e.name,'index.html'))).map(e => `/editoriales/${e.name}/`)];
assert.ok(routes.length > 3, 'editoriales: no se descubrieron suficientes fichas reales');
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
const failures = [];
try {
  for (const width of widths) {
    const context = await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    try {
      for (let offset=0;offset<routes.length;offset+=8) {
        await Promise.all(routes.slice(offset,offset+8).map(async route => {
          const page = await context.newPage();
          try {
            const response = await page.goto(BASE+route,{waitUntil:'domcontentloaded',timeout:30000});
            assert.equal(response?.status(),200,`${route} ${width}px: respuesta HTTP ${response?.status()}`);
            await page.locator('main#contenido h1').first().waitFor({state:'visible'});
            const result = await page.evaluate(() => ({title:document.querySelector('main#contenido h1')?.textContent.trim(),length:document.body.innerText.trim().length,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth}));
            assert.ok(result.title,`${route} ${width}px: encabezado vacío`);
            assert.ok(result.length>200,`${route} ${width}px: respuesta documental vacía (${result.length} caracteres)`);
            assert.ok(result.overflow<=1,`${route} ${width}px: desbordamiento horizontal ${result.overflow}px`);
          } catch(e) { failures.push(`${route} ${width}px: ${e.message}`); }
          finally {await page.close();}
        }));
      }
    } finally {await context.close();}
  }
  assert.deepEqual(failures,[],failures.join('\n'));
  console.log(`PASS: ${routes.length} páginas editoriales en cuatro resoluciones`);
} finally {await browser.close();}
