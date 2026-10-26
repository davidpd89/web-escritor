import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const route='/empieza-aqui/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try {
  for(const width of [390,1024]) {
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto(`${ORIGIN}${route}`,{waitUntil:'load'});
    const links=page.locator('main .findability-entry a[href]');
    const count=await links.count();
    assert(count>=7,`${route}@${width}: faltan enlaces para evaluar el foco`);
    for(let i=0;i<count;i++) {
      const link=links.nth(i);
      if(!await link.isVisible()) continue;
      await link.focus();
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const state=await link.evaluate(el=>{
        const s=getComputedStyle(el);
        const r=el.getBoundingClientRect();
        return {focused:document.activeElement===el,indicator:(s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0)||s.boxShadow!=='none',visible:r.width>0&&r.height>0&&r.top<innerHeight&&r.bottom>0&&r.left<innerWidth&&r.right>0,href:el.getAttribute('href')};
      });
      assert(state.focused,`${route}@${width}: enlace ${state.href} no recibe foco`);
      assert(state.indicator,`${route}@${width}: enlace ${state.href} sin indicador de foco`);
      assert(state.visible,`${route}@${width}: enlace ${state.href} enfocado fuera del viewport`);
    }
    await context.close();
  }
  console.log('empieza-aqui-all-links-focus-regression: OK');
} finally {await browser.close();}
