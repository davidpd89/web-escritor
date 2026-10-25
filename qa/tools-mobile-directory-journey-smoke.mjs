import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,360,390]) {
    const context = await browser.newContext({viewport:{width,height:760},isMobile:true,hasTouch:true});
    const page = await context.newPage();
    try {
      const hub = `${ORIGIN}/herramientas/`;
      const response = await page.goto(hub,{waitUntil:'load'});
      assert(response?.ok(),`${hub} @${width}: HTTP ${response?.status()}`);
      const destinations = await page.locator('[data-tool] h3 a').evaluateAll(links => links.map(a=>({href:a.getAttribute('href'),name:a.textContent.trim()})));
      assert(destinations.length > 0,`${hub} @${width}: directorio sin herramientas`);
      for (const item of destinations) {
        await page.goto(hub,{waitUntil:'load'});
        const link = page.locator('[data-tool] h3 a').filter({hasText:item.name}).first();
        assert(await link.isVisible(),`${hub} @${width}: enlace oculto: ${item.name}`);
        await link.scrollIntoViewIfNeeded();
        const navigation = page.waitForURL(url=>url.pathname !== '/herramientas/',{timeout:10000});
        await link.click();
        await navigation;
        const pathname = new URL(page.url()).pathname;
        const expected = new URL(item.href,hub).pathname;
        assert.equal(pathname,expected,`${hub} @${width}: destino incorrecto para ${item.name}`);
        assert(await page.locator('h1').first().isVisible(),`${pathname} @${width}: H1 no visible`);
        const metrics = await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:document.documentElement.clientWidth}));
        assert(metrics.scroll <= metrics.width+1,`${pathname} @${width}: desbordamiento ${JSON.stringify(metrics)}`);
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('tools-mobile-directory-journey-smoke: PASS');