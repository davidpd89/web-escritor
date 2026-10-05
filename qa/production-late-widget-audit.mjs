import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=['/autor.html','/editoriales/','/convocatorias-escritores/','/cuaderno/','/herramientas/'];

await assertProductionRelease({origin:O,sha:S,label:'late-widget'});
const browser=await chromium.launch({headless:true});
const failures=[];

try{
  for(const route of ROUTES){
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const r=await page.goto(O+route+'?qa_late_widget=1',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,route+': HTTP '+r?.status());

      const launcher=page.locator('.assistant-widget__launcher').first();
      await launcher.waitFor({state:'visible',timeout:5000});
      assert.equal(await page.locator('[data-assistant-widget]').count(),1,route+': duplicate assistant widget roots');
      assert.equal(await launcher.getAttribute('aria-expanded'),'false',route+': launcher starts expanded');
      assert.equal((await launcher.getAttribute('aria-label')||'').trim(),'Abrir asistente',route+': launcher accessible name drift');

      await launcher.focus();
      await launcher.click();
      const panel=page.locator('#assistant-widget-panel').first();
      await panel.waitFor({state:'visible',timeout:3000});
      assert.equal(await launcher.getAttribute('aria-expanded'),'true',route+': launcher did not expose expanded state');
      assert.equal(await panel.getAttribute('role'),'dialog',route+': panel dialog role missing');
      const labelledBy=await panel.getAttribute('aria-labelledby');
      assert.ok(labelledBy,route+': panel missing aria-labelledby');
      assert.equal(await page.locator('#'+labelledBy).count(),1,route+': panel label target missing');

      const frame=page.locator('.assistant-widget__frame').first();
      await frame.waitFor({state:'visible',timeout:3000});
      assert.match((await frame.getAttribute('title')||''),/asistente/i,route+': iframe title missing');
      const src=await frame.getAttribute('src');
      assert.ok(src&&src.startsWith('/asistente/embed.html?from='),route+': iframe source drift '+src);

      const assistant=page.frameLocator('.assistant-widget__frame');
      await assistant.locator('[data-assistant-query]').waitFor({state:'visible',timeout:5000});
      const close=page.locator('.assistant-widget__header-actions button[aria-label="Cerrar asistente"]').first();
      await close.click();
      await panel.waitFor({state:'hidden',timeout:3000});
      assert.equal(await launcher.getAttribute('aria-expanded'),'false',route+': launcher stayed expanded after close');
      assert.equal(await page.evaluate(()=>document.activeElement?.classList.contains('assistant-widget__launcher')),true,route+': focus not restored to launcher');
      assert.deepEqual(errors,[],route+': page errors '+errors.join(' | '));
    }catch(e){
      failures.push(String(e?.message||e));
    }finally{
      await context.close();
    }
  }

  {
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    try{
      const r=await page.goto(O+'/asistente/?qa_late_widget=1',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,'assistant page HTTP');
      await page.waitForTimeout(1800);
      assert.equal(await page.locator('[data-assistant-widget]').count(),0,'full assistant page must not mount floating widget');
    }catch(e){failures.push(String(e?.message||e))}
    finally{await context.close()}
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS late-loaded assistant widget on '+ROUTES.length+' representative routes + exclusion on /asistente/');
