import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const route='/empieza-aqui/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const js of [true,false]) {
    const context=await browser.newContext({javaScriptEnabled:js});
    const page=await context.newPage();
    await page.goto(`${ORIGIN}${route}`,{waitUntil:'load'});
    const groups=page.locator('main .findability-entry');
    assert.equal(await groups.count(),7,`${route} JS=${js}: faltan rutas`);
    for(let i=0;i<await groups.count();i++) {
      const group=groups.nth(i);
      const id=await group.getAttribute('id');
      const links=group.locator('a[href]');
      const names=new Map();
      for(let j=0;j<await links.count();j++) {
        const link=links.nth(j);
        const href=await link.getAttribute('href');
        const name=await link.ariaSnapshot();
        const match=name.match(/^- link(?:\s+\"([^\"]+)\")?/m);
        const accessible=(match?.[1]||'').trim();
        assert(accessible,`${route} JS=${js}: ruta ${id}, enlace ${href} sin nombre accesible`);
        const previous=names.get(accessible);
        assert(!previous||previous===href,`${route} JS=${js}: ruta ${id}, nombre ${accessible} compartido por ${previous} y ${href}`);
        names.set(accessible,href);
      }
    }
    await context.close();
  }
  console.log('empieza-aqui-accessible-link-names-regression: OK');
} finally {await browser.close();}
