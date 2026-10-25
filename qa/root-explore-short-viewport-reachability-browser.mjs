import assert from 'node:assert/strict';
import { chromium } from 'playwright';

assert.ok(process.env.QA_ORIGIN, 'Se necesita QA_ORIGIN');
const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of [{width:320,height:480},{width:390,height:568},{width:768,height:600}]) {
    const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
    await page.addInitScript(() => { try { sessionStorage.setItem('dp-intro-seen','true'); } catch {} });
    await page.goto(new URL('/',process.env.QA_ORIGIN).href,{waitUntil:'load'});
    await page.evaluate(() => document.fonts.ready);
    const trigger = page.locator('[data-explore-open]:visible').first();
    await trigger.click();
    const dialog = page.locator('[data-explore-dialog]');
    await dialog.waitFor({state:'visible'});
    await page.waitForFunction(() => {
      const d = document.querySelector('[data-explore-dialog]');
      return d?.open && getComputedStyle(d).transform === 'matrix(1, 0, 0, 1, 0, 0)';
    });
    const links = dialog.locator('a:visible');
    const count = await links.count();
    assert.ok(count > 0, `Explorar ${viewport.width}x${viewport.height}: sin enlaces`);
    for (let i=0;i<count;i++) {
      const link=links.nth(i);
      await link.scrollIntoViewIfNeeded({timeout:3000});
      const result=await link.evaluate(el => {
        const r=el.getBoundingClientRect();
        const x=Math.max(0,Math.min(innerWidth-1,r.left+r.width/2));
        const y=Math.max(0,Math.min(innerHeight-1,r.top+r.height/2));
        const hit=document.elementFromPoint(x,y);
        return {rect:{x:r.x,y:r.y,width:r.width,height:r.height},reachable:r.top>=0&&r.bottom<=innerHeight&&(hit===el||el.contains(hit))};
      });
      assert.ok(result.reachable, `Explorar ${viewport.width}x${viewport.height}: enlace ${i} inaccesible; ${JSON.stringify(result.rect)}`);
    }
    await page.close();
  }
} finally { await browser.close(); }