import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const CASES=[
  ['winter-boundary','2026-01-01T23:30:00Z','2026-01-02'],
  ['summer-boundary','2026-07-01T22:30:00Z','2026-07-02'],
  ['summer-before-boundary','2026-07-01T21:30:00Z','2026-07-01'],
];
const ZONES=['America/Los_Angeles','Europe/Madrid','Asia/Tokyo'];

await assertProductionRelease({origin:O,sha:S,label:'radar-timezone'});
const browser=await chromium.launch({headless:true});
const failures=[];
try{
  for(const zone of ZONES){
    const context=await browser.newContext({timezoneId:zone,viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
    const page=await context.newPage();
    try{
      const r=await page.goto(O+'/convocatorias-escritores/?qa_radar_timezone=1',{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(r?.status(),200,zone+': HTTP '+r?.status());
      await page.waitForFunction(()=>window.DPRadarDates?.siteCivilDate);
      for(const [label,instant,expected] of CASES){
        const got=await page.evaluate((value)=>{
          const d=window.DPRadarDates.siteCivilDate(value);
          return d ? [d.year,String(d.month).padStart(2,'0'),String(d.day).padStart(2,'0')].join('-') : null;
        },instant);
        assert.equal(got,expected,zone+' '+label+': '+instant+' => '+got+', expected '+expected);
      }
      const tz=await page.evaluate(()=>window.DPRadarDates.SITE_TIME_ZONE);
      assert.equal(tz,'Europe/Madrid',zone+': site timezone contract drift');
    }catch(e){failures.push(String(e?.message||e))}
    finally{await context.close()}
  }
}finally{await browser.close()}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production radar timezone invariance: '+ZONES.length+' visitor zones x '+CASES.length+' Madrid-boundary instants');
