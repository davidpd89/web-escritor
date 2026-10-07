import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const FUZZ=[
  'áéíóú ÁÉÍÓÚ',
  'ñ Ñ ü Ü',
  'e\u0301 n\u0303 u\u0308',
  '💫📚🕰️',
  '\"<svg/onload=alert(1)>',
  "'; DROP TABLE editoriales; --",
  '%E0%A4%A',
  'a'.repeat(512),
];

await assertProductionRelease({origin:O,sha:S,label:'filter-fuzz'});
const browser=await chromium.launch({headless:true});
const failures=[];

async function noScriptInjection(page,label){
  const injected=await page.evaluate(()=>({
    svg:document.querySelectorAll('svg[onload]').length,
    scripts:[...document.scripts].filter(s=>/DROP TABLE|alert\(1\)/.test(s.textContent||'')).length,
    html:(document.body?.innerHTML||'').includes('<svg/onload=alert(1)>'),
  }));
  assert.equal(injected.svg,0,label+': injected svg/onload reached DOM');
  assert.equal(injected.scripts,0,label+': hostile text reached a script');
  assert.equal(injected.html,false,label+': hostile search text was interpreted as markup');
}

try{
  {
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    try{
      const r=await page.goto(O+'/editoriales/?qa_filter_fuzz=1#estado=__invalid__&pais=%E0%A4%A&q=%E0%A4%A',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,'editoriales fuzz: HTTP');
      await page.waitForFunction(()=>document.querySelector('[data-editoriales-search]'));
      assert.equal(await page.locator('[data-editoriales-status]').inputValue(),'','editoriales fuzz: invalid status was not sanitized');
      assert.equal(await page.locator('[data-editoriales-country]').inputValue(),'','editoriales fuzz: invalid country was not sanitized');
      const total=await page.locator('[data-editorial-card]').count();
      assert.ok(total>50,'editoriales fuzz: unexpectedly small corpus '+total);
      for(const [i,value] of FUZZ.entries()){
        const input=page.locator('[data-editoriales-search]');
        await input.fill(value);
        await page.waitForTimeout(30);
        const state=await page.evaluate(()=>({
          value:document.querySelector('[data-editoriales-search]')?.value,
          hash:location.hash,
          countText:document.querySelector('[data-editoriales-count]')?.textContent||'',
          visible:[...document.querySelectorAll('[data-editorial-card]')].filter(x=>!x.hidden).length,
        }));
        assert.equal(state.value,value,'editoriales fuzz '+i+': input value mutated unexpectedly');
        assert.match(state.countText,/^\d+\s+editorial(?:es)?$/,'editoriales fuzz '+i+': invalid count text '+state.countText);
        assert.ok(state.visible>=0&&state.visible<=total,'editoriales fuzz '+i+': visible count outside corpus');
        assert.doesNotMatch(state.hash,/<svg|onload=|DROP TABLE/i,'editoriales fuzz '+i+': URL hash contains unescaped hostile markup');
        const raw=state.hash.replace(/^#/,'');
        assert.doesNotThrow(()=>new URLSearchParams(raw),'editoriales fuzz '+i+': generated hash cannot be parsed');
        await noScriptInjection(page,'editoriales fuzz '+i);
      }
      await page.locator('[data-editoriales-reset]').click();
      await page.waitForFunction(()=>location.hash==='');
      assert.equal(await page.locator('[data-editorial-card]:not([hidden])').count(),total,'editoriales fuzz: reset did not restore corpus');
      assert.deepEqual(errors,[],'editoriales fuzz page errors: '+errors.join(' | '));
    }catch(e){failures.push(String(e?.message||e))}
    finally{await context.close()}
  }

  {
    const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    try{
      const r=await page.goto(O+'/convocatorias-escritores/?qa_filter_fuzz=1',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,'radar fuzz: HTTP');
      await page.waitForFunction(()=>document.querySelector('[data-radar-search]'));
      // The closed section ships in the HTML (SEO) but is hidden until the checkbox
      // is ticked, so the default corpus excludes it.
      const total=await page.locator('[data-radar-item]:not([data-radar-kind="expired"])').count();
      assert.ok(total>20,'radar fuzz: unexpectedly small corpus '+total);
      for(const [i,value] of FUZZ.entries()){
        await page.locator('[data-radar-search]').fill(value);
        await page.waitForTimeout(30);
        const state=await page.evaluate(()=>({
          value:document.querySelector('[data-radar-search]')?.value,
          countText:document.querySelector('[data-radar-count]')?.textContent||'',
          visible:[...document.querySelectorAll('[data-radar-item]')].filter(x=>!x.hidden).length,
        }));
        assert.equal(state.value,value,'radar fuzz '+i+': input value mutated unexpectedly');
        assert.match(state.countText,/^\d+\s+convocatoria(?:s)?\s+visible(?:s)?$/,'radar fuzz '+i+': invalid count text '+state.countText);
        assert.ok(state.visible>=0&&state.visible<=total,'radar fuzz '+i+': visible count outside corpus');
        await noScriptInjection(page,'radar fuzz '+i);
      }
      const clear=page.locator('[data-radar-clear]').first();
      if(await clear.count()) await clear.click();
      else await page.locator('[data-radar-search]').fill('');
      await page.waitForTimeout(30);
      assert.equal(await page.locator('[data-radar-item]:not([hidden])').count(),total,'radar fuzz: clear did not restore corpus');
      assert.deepEqual(errors,[],'radar fuzz page errors: '+errors.join(' | '));
    }catch(e){failures.push(String(e?.message||e))}
    finally{await context.close()}
  }
}finally{
  await browser.close();
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production filter input fuzz: '+FUZZ.length+' values across Editoriales + Convocatorias');
