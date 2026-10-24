import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const BASE = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const browser = await chromium.launch({headless:true});
const modes = ['mouse', 'enter', 'space', 'touch'];
const destinations = [];
try {
  for (const mode of modes) {
    const context = await browser.newContext({viewport:{width:390,height:844}, ...(mode==='touch'?{hasTouch:true,isMobile:true}:{})});
    const page = await context.newPage();
    try {
      const response = await page.goto(`${BASE}/metodologia-editorial/`,{waitUntil:'load'});
      assert.equal(response?.status(),200);
      const trigger = page.locator('main .tool-findings-block [data-email-reveal]');
      assert.equal(await trigger.count(),1);
      if(mode==='mouse') await trigger.click();
      if(mode==='touch') await trigger.tap();
      if(mode==='enter'||mode==='space') {
        await trigger.focus();
        await page.keyboard.press(mode==='enter'?'Enter':'Space');
      }
      const revealed = page.locator('main .tool-findings-block a[data-email-revealed="true"]');
      await revealed.waitFor({state:'attached'});
      const state = await revealed.evaluate(el=>({href:el.getAttribute('href'),focused:document.activeElement===el,label:el.getAttribute('aria-label')}));
      assert.match(state.href,/^mailto:[^@]+@[^@]+/);
      assert.equal(state.focused,true,`${mode}: foco perdido`);
      assert.ok(state.label&&state.label.includes('@'));
      destinations.push(state.href);
    } finally { await context.close(); }
  }
  assert.equal(new Set(destinations).size,1,'Las modalidades generan distintos destinos');
  console.log('PASS methodology input modalities');
} finally { await browser.close(); }