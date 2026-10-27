import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const cases = [{ width: 390, height: 844 }, { width: 1440, height: 900 }];

try {
  for (const viewport of cases) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    try {
      const response = await page.goto(`${ORIGIN}/mapa-del-sitio/`, { waitUntil: 'load' });
      assert.equal(response?.status(), 200, `mapa-del-sitio ${viewport.width}px: HTTP ${response?.status()}`);
      const results = await page.locator('.findability-hero h1, .findability-hero__kicker, .findability-hero__lead, .directory-group h2, .directory-group__label').evaluateAll(nodes => {
        const parse = s => { const m = s.match(/^rgba?\(([^)]+)\)$/); if (!m) throw new Error(`Color no interpretable: ${s}`); return m[1].split(/[,\s/]+/).filter(Boolean).map(Number); };
        const lum = c => { const a = c.slice(0,3).map(n => { const x=n/255; return x<=.04045?x/12.92:((x+.055)/1.055)**2.4; }); return .2126*a[0]+.7152*a[1]+.0722*a[2]; };
        return nodes.filter(n => n.getClientRects().length).map(n => {
          const style=getComputedStyle(n);
          const fg=parse(style.color);
          let parent=n, bg=[255,255,255];
          while(parent) { const c=parse(getComputedStyle(parent).backgroundColor); if(c.length===3 || c[3]===1) {bg=c;break;} parent=parent.parentElement; }
          const x=lum(fg), y=lum(bg);
          const ratio=(Math.max(x,y)+.05)/(Math.min(x,y)+.05);
          const size=parseFloat(style.fontSize), weight=Number(style.fontWeight)||400;
          const minimum=size>=24||(size>=18.66&&weight>=700)?3:4.5;
          return {text:n.textContent.trim(),ratio,minimum,color:style.color,background:bg.join(',')};
        });
      });
      assert(results.length >= 10, `mapa-del-sitio ${viewport.width}px: no se encontraron suficientes encabezados y etiquetas`);
      for(const r of results) assert(r.ratio>=r.minimum, `mapa-del-sitio ${viewport.width}px: ${JSON.stringify(r.text)} contraste ${r.ratio.toFixed(2)}:1 inferior a ${r.minimum}:1; ${r.color} sobre ${r.background}`);
    } finally { await context.close(); }
  }
  console.log('sitemap-editorial-color-contrast: PASS');
} finally { await browser.close(); }
