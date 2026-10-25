import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const cases = [
  ['manuscrito','[data-chapter-paste]','[data-chapter-analyzer] button[type="submit"]','[data-chapter-results]'],
  ['dialogo','#dialogue-text','[data-dialogue-tool] button[type="submit"]','[data-dialogue-results]'],
  ['legibilidad','[data-readability-input]','[data-readability-form] button[type="submit"]','[data-readability-results]'],
  ['repeticiones','[data-repetition-input]','[data-repetition-form] button[type="submit"]','[data-repetition-results]'],
  ['variedad-lexica','[data-lexical-input]','[data-lexical-form] button[type="submit"]','[data-lexical-results]']
];
const sample = Array.from({length:30},()=> 'Ana abrió la puerta. —No entraré —dijo—. La puerta seguía abierta.').join('\n\n');
const browser = await chromium.launch({headless:true});
try {
  for (const width of [320,360,390]) {
    const context = await browser.newContext({viewport:{width,height:760},isMobile:true,hasTouch:true});
    try {
      for (const [name,input,button,result] of cases) {
        const page = await context.newPage();
        const url = `${ORIGIN}/herramientas/${name}/`;
        try {
          const response = await page.goto(url,{waitUntil:'load'});
          assert(response?.ok(),`${url} @${width}: HTTP ${response?.status()}`);
          await page.locator(input).fill(sample);
          const action = page.locator(button);
          await action.scrollIntoViewIfNeeded();
          assert(await action.isEnabled(),`${url} @${width}: botón no habilitado`);
          const rect = await action.boundingBox();
          assert(rect && rect.width > 0 && rect.height > 0,`${url} @${width}: botón sin superficie visible`);
          const x = rect.x + rect.width/2;
          const y = rect.y + rect.height/2;
          const hit = await page.evaluate(({x,y,selector}) => {
            const target = document.querySelector(selector);
            const top = document.elementFromPoint(x,y);
            return Boolean(target && top && (target === top || target.contains(top)));
          },{x,y,selector:button});
          assert(hit,`${url} @${width}: centro del botón tapado en (${x}, ${y})`);
          await page.touchscreen.tap(x,y);
          await page.locator(result).waitFor({state:'visible',timeout:10000});
          assert((await page.locator(result).innerText()).trim(),`${url} @${width}: la pulsación no produjo resultados`);
        } finally {
          await page.close();
        }
      }
    } finally {
      await context.close();
    }
  }
} finally {
  await browser.close();
}
console.log('tools-mobile-touch-smoke: PASS');