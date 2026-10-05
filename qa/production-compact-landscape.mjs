import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/autor.html',
  '/libros/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
  '/prensa.html',
  '/mapa-del-sitio/',
];
const VIEWPORTS=[
  {width:844,height:390,label:'phone-landscape-wide'},
  {width:667,height:375,label:'phone-landscape-compact'},
];

async function releaseCheck(){
  if(!S)return;
  const r=await fetch(`${O}/_release/${S}.json?qa_landscape_release=1`,{signal:AbortSignal.timeout(15000)});
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}
await releaseCheck();

const browser=await chromium.launch({headless:true});
const failures=[],report=[];
try{
  for(const vp of VIEWPORTS){
    for(const route of ROUTES){
      const context=await browser.newContext({viewport:{width:vp.width,height:vp.height},reducedMotion:'reduce'});
      const page=await context.newPage();
      const pageErrors=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
      try{
        const nav=await page.goto(`${O}${route}?qa_landscape=1`,{waitUntil:'domcontentloaded',timeout:25000});
        assert.equal(nav?.status(),200,`${route}: HTTP ${nav?.status()}`);
        await page.waitForTimeout(350);
        const enter=page.locator('[data-intro-enter]').first();
        if(await enter.count()){
          await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
          const intro=page.locator('[data-intro]').first();
          if(await intro.count()) await intro.waitFor({state:'hidden',timeout:2500});
        }

        const geometry=await page.evaluate(()=>{
          const root=document.documentElement;
          const main=document.querySelector('main');
          const mr=main?.getBoundingClientRect();
          const fixed=[...document.querySelectorAll('body *')].filter(el=>{
            const s=getComputedStyle(el),r=el.getBoundingClientRect();
            return (s.position==='fixed'||s.position==='sticky')&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
          }).map(el=>{
            const r=el.getBoundingClientRect();
            return {tag:el.tagName.toLowerCase(),id:el.id||'',cls:String(el.className||'').slice(0,100),height:r.height,width:r.width,top:r.top,bottom:r.bottom};
          });
          return {
            overflow:root.scrollWidth-root.clientWidth,
            main:{exists:Boolean(main),width:mr?.width||0,height:mr?.height||0},
            fixed,
          };
        });
        assert.ok(geometry.overflow<=1,`${route} ${vp.label}: horizontal overflow ${geometry.overflow}px`);
        assert.equal(geometry.main.exists,true,`${route} ${vp.label}: missing main`);
        assert.ok(geometry.main.width>0&&geometry.main.height>0,`${route} ${vp.label}: collapsed main`);
        const giant=geometry.fixed.filter(x=>x.height>vp.height*.82 && x.width>vp.width*.8);
        assert.deepEqual(giant,[],`${route} ${vp.label}: fixed/sticky UI covers almost entire viewport: ${JSON.stringify(giant)}`);

        const explore=page.locator('[data-explore-open]').first();
        if(await explore.count()){
          await explore.click();
          const dialog=page.locator('[data-explore-dialog]').first();
          await dialog.waitFor({state:'visible',timeout:3000});
          await page.waitForFunction(()=>{
            const el=document.querySelector('[data-explore-dialog]');
            if(!(el instanceof HTMLDialogElement)||!el.open)return false;
            const r=el.getBoundingClientRect();
            return r.x>=-1&&r.y>=-1&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1;
          },null,{timeout:2500});
          const rect=await dialog.boundingBox();
          assert.ok(rect,`${route} ${vp.label}: Explore dialog has no box`);
          assert.ok(rect.x>=-1&&rect.y>=-1,`${route} ${vp.label}: Explore dialog starts offscreen`);
          assert.ok(rect.x+rect.width<=vp.width+1,`${route} ${vp.label}: Explore dialog overflows horizontally`);
          assert.ok(rect.y+rect.height<=vp.height+1,`${route} ${vp.label}: Explore dialog overflows vertically`);
          const scrollable=await dialog.evaluate(el=>el.scrollHeight<=el.clientHeight+1||['auto','scroll'].includes(getComputedStyle(el).overflowY)||[...el.querySelectorAll('*')].some(n=>['auto','scroll'].includes(getComputedStyle(n).overflowY)&&n.scrollHeight>n.clientHeight));
          assert.equal(scrollable,true,`${route} ${vp.label}: tall Explore content cannot scroll`);
          await page.keyboard.press('Escape');
          await dialog.waitFor({state:'hidden',timeout:3000});
        }

        for(const selector of ['[data-editoriales-search]','[data-radar-search]','[data-radar-filter]']){
          const el=page.locator(selector).first();
          if(await el.count()){
            const box=await el.boundingBox();
            assert.ok(box&&box.width>0&&box.height>0,`${route} ${vp.label}: filter control collapsed ${selector}`);
          }
        }
        assert.deepEqual(pageErrors,[],`${route} ${vp.label}: page errors ${pageErrors.join(' | ')}`);
        report.push({route,viewport:vp.label,overflow:geometry.overflow,fixed:geometry.fixed.length});
      }catch(e){
        failures.push(String(e?.message||e));
      }finally{
        await context.close();
      }
    }
  }
}finally{
  await browser.close();
}
assert.deepEqual(failures,[],failures.join('\n'));
console.log('PASS production compact-landscape:',JSON.stringify(report));
