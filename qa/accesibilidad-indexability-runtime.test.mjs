import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.SITE_URL || process.env.BASE_URL || 'http://127.0.0.1:8000';
const route = '/accesibilidad/';
const expected = 'https://davidportodiaz.com/accesibilidad/';

 test('indexabilidad real independiente de viewport y JavaScript', async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const width of [320,390,768,1280]) {
      for (const javaScriptEnabled of [true,false]) {
        const context = await browser.newContext({viewport:{width,height:800},javaScriptEnabled});
        try {
          const page = await context.newPage();
          const response = await page.goto(new URL(route,base).href,{waitUntil:'domcontentloaded'});
          assert.equal(response?.status(),200,`${route} ${width}px: HTTP inesperado`);
          const data = await page.evaluate(() => ({
            canonical:[...document.querySelectorAll('link[rel~="canonical"]')].map(e=>e.href),
            robots:[...document.querySelectorAll('meta[name="robots"]')].map(e=>e.content),
            title:document.title,
            description:document.querySelector('meta[name="description"]')?.content,
            heading:document.querySelector('main h1')?.textContent.trim()
          }));
          const label = `${route} ${width}px JS=${javaScriptEnabled}`;
          assert.deepEqual(data.canonical,[expected],`${label}: canonical ${JSON.stringify(data.canonical)}`);
          assert.equal(data.robots.length,1,`${label}: robots ${JSON.stringify(data.robots)}`);
          assert.doesNotMatch(data.robots[0],/\b(?:noindex|nofollow|none)\b/i,`${label}: robots ${data.robots[0]}`);
          assert.match(data.title,/accesibilidad/i,`${label}: title ${data.title}`);
          assert.ok(data.description?.trim(),`${label}: descripción vacía`);
          assert.match(data.heading||'',/accesibilidad/i,`${label}: H1 ${data.heading}`);
        } finally { await context.close(); }
      }
    }
  } finally { await browser.close(); }
});