import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const ROUTES=[
  '/', '/autor.html', '/libros/', '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/', '/cuaderno/', '/herramientas/',
  '/editoriales/', '/convocatorias-escritores/', '/metodologia-editorial/',
  '/prensa.html', '/mapa-del-sitio/'
];

const browser=await chromium.launch({headless:true});
const failures=[];
try{
  for(const route of ROUTES){
    const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const nav=await page.goto(`${O}${route}?qa_focus_restore=1`,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(nav?.status(),200,`${route}: HTTP ${nav?.status()}`);

      const enter=page.locator('[data-intro-enter]').first();
      if(await enter.count()){
        await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
        const intro=page.locator('[data-intro]').first();
        if(await intro.count()) await intro.waitFor({state:'hidden',timeout:2500});
      }

      const opener=page.locator('[data-explore-open]:visible').first();
      if(await opener.count()){
        await opener.focus();
        await opener.click();
        const dialog=page.locator('[data-explore-dialog]').first();
        await dialog.waitFor({state:'visible',timeout:3000});
        assert.equal(await opener.getAttribute('aria-expanded'),'true',`${route}: Explore opener aria-expanded did not become true`);

        const close=page.locator('[data-explore-close]').first();
        await close.waitFor({state:'visible',timeout:3000});
        assert.equal(await close.evaluate(el=>document.activeElement===el),true,`${route}: Explore close control did not receive initial focus`);

        // Playwright's isVisible() is not the same thing as "the browser will
        // put focus here": the newsletter form inside the dialog carries an
        // anti-spam honeypot (<input name="website" tabindex="-1"> inside a
        // div[aria-hidden][inert].sr-only) that has layout boxes and reads as
        // visible, but is unfocusable -- calling .focus() on it is a no-op.
        // Treating it as the dialog's last stop made this audit demand that
        // reverse Tab land on the honeypot, which can never happen. The cycle
        // is defined by real tabbability, and the honeypot staying out of it
        // is part of the contract.
        const focusables=dialog.locator('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])');
        const visible=[];
        for(let i=0;i<await focusables.count();i++){
          const el=focusables.nth(i);
          const tabbable=await el.evaluate((node)=>{
            if(!(node instanceof HTMLElement)||node.tabIndex<0) return false;
            if(node.closest('[hidden],[inert],[aria-hidden="true"]')) return false;
            const style=getComputedStyle(node);
            if(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse') return false;
            return node.getClientRects().length>0;
          });
          if(tabbable) visible.push(el);
        }
        if(visible.length>1){
          const first=visible[0], last=visible[visible.length-1];
          await first.focus();
          await page.keyboard.press('Shift+Tab');
          assert.equal(await last.evaluate(el=>document.activeElement===el),true,`${route}: reverse Tab escaped Explore dialog`);
          await last.focus();
          await page.keyboard.press('Tab');
          assert.equal(await first.evaluate(el=>document.activeElement===el),true,`${route}: forward Tab escaped Explore dialog`);
          assert.equal(
            await page.evaluate(()=>Boolean(document.activeElement?.closest('[hidden],[inert],[aria-hidden="true"]'))),
            false,
            `${route}: el ciclo de foco del dialogo pasa por contenido inert/aria-hidden`,
          );
        }

        await page.keyboard.press('Escape');
        await dialog.waitFor({state:'hidden',timeout:3000});
        await page.waitForTimeout(120);
        assert.equal(await opener.getAttribute('aria-expanded'),'false',`${route}: Explore opener aria-expanded did not reset`);
        assert.equal(await opener.evaluate(el=>document.activeElement===el),true,`${route}: focus was not restored to Explore opener after Escape`);
      }

      const submenu=page.locator('.masthead-nav__submenu-trigger:visible').first();
      if(await submenu.count()){
        await submenu.focus();
        await submenu.click();
        assert.equal(await submenu.getAttribute('aria-expanded'),'true',`${route}: masthead submenu did not open`);
        await page.keyboard.press('Escape');
        await page.waitForTimeout(50);
        assert.equal(await submenu.getAttribute('aria-expanded'),'false',`${route}: masthead submenu aria-expanded did not reset on Escape`);
        assert.equal(await submenu.evaluate(el=>document.activeElement===el),true,`${route}: focus was not restored to masthead submenu trigger`);
      }
    }catch(e){
      failures.push(String(e?.message||e));
    }finally{
      await context.close();
    }
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production focus restoration/trap contract: ${ROUTES.length} representative routes`);
