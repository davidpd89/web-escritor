import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = (process.env.SITE_BASE_URL || 'https://davidportodiaz.com').replace(/\/$/, '');
const ROUTES = ['/', '/herramientas/', '/editoriales/', '/prensa.html'];
const WIDTHS = [320,768,1024,1440];
const browser = await chromium.launch({headless:true});

try {
  for (const width of WIDTHS) {
    for (const route of ROUTES) {
      const page = await browser.newPage({viewport:{width,height:900}});
      try {
        const response = await page.goto(BASE + route,{waitUntil:'load'});
        assert.equal(response?.status(),200,`${route} @ ${width}px: HTTP ${response?.status()}`);
        const state = await page.evaluate(() => {
          const unsafe = [];
          for (const el of document.querySelectorAll('*')) {
            for (const attr of el.attributes) {
              if (/^on[a-z]+$/i.test(attr.name) || (/^(href|src|action|formaction)$/i.test(attr.name) && /^\s*javascript:/i.test(attr.value))) {
                unsafe.push(`${el.tagName.toLowerCase()}[${attr.name}]`);
              }
            }
          }
          return {unsafe,overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth};
        });
        assert.deepEqual(state.unsafe,[],`${route} @ ${width}px: atributos o destinos ejecutables: ${state.unsafe.join(', ')}`);
        assert.ok(state.overflow <= 2,`${route} @ ${width}px: desbordamiento horizontal de ${state.overflow}px`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}