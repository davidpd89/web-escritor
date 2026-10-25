import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = (process.env.QA_BASE_URL || 'http://127.0.0.1:4173').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
try {
  for (const path of ['/recomendaciones/','/editoriales/']) {
    for (const width of [390,1440]) {
      const context = await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
      await context.route('**/*', route => new URL(route.request().url()).origin === new URL(base).origin ? route.continue() : route.abort());
      await context.addInitScript(() => {
        window.__qaShifts = [];
        new PerformanceObserver(list => {
          for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__qaShifts.push({value:entry.value,start:entry.startTime});
        }).observe({type:'layout-shift',buffered:true});
      });
      const page = await context.newPage();
      const response = await page.goto(base + path,{waitUntil:'load'});
      assert.equal(response.status(),200,`${path} ${width}: HTTP`);
      await page.evaluate(() => document.fonts.ready);
      const result = await page.evaluate(() => {
        const shifts = window.__qaShifts || [];
        let maximum = 0;
        for (let i=0;i<shifts.length;i++) {
          let score = 0;
          for (let j=i;j<shifts.length && shifts[j].start-shifts[i].start<=5000 && (j===i || shifts[j].start-shifts[j-1].start<=1000);j++) score+=shifts[j].value;
          maximum=Math.max(maximum,score);
        }
        return {cls:maximum,heading:!!document.querySelector('main h1')?.getClientRects().length};
      });
      assert(result.heading,`${path} ${width}: encabezado principal invisible`);
      assert(result.cls<=0.10,`${path} ${width}: CLS ${result.cls.toFixed(4)} supera 0.10`);
      await context.close();
    }
  }
} finally { await browser.close(); }