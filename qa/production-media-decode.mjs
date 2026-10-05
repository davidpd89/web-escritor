import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/autor.html',
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
if(S){
  const r=await fetch(`${O}/_release/${S}.json?qa_media_release=1`,{signal:AbortSignal.timeout(15000)});
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}

const browser=await chromium.launch({headless:true});
const failures=[],stats=[];
try{
  for(const route of ROUTES){
    const context=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
    try{
      const response=await page.goto(`${O}${route}?qa_media=1`,{waitUntil:'domcontentloaded',timeout:25000});
      assert.equal(response?.status(),200,`${route}: HTTP ${response?.status()}`);
      const enter=page.locator('[data-intro-enter]').first();
      if(await enter.count()) await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
      await page.waitForTimeout(300);

      // Exercise lazy loading by walking the document instead of only checking
      // whatever happened to be inside the first viewport.
      const height=await page.evaluate(()=>Math.max(document.body?.scrollHeight||0,document.documentElement.scrollHeight));
      for(let y=0;y<height;y+=700){
        await page.evaluate(v=>window.scrollTo(0,v),y);
        await page.waitForTimeout(25);
      }
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.waitForTimeout(250);

      const result=await page.evaluate(async origin=>{
        const images=[...document.images];
        const candidates=[];
        for(const img of images){
          const s=getComputedStyle(img),r=img.getBoundingClientRect();
          const rendered=s.display!=='none'&&s.visibility!=='hidden'&&Number(s.opacity)!==0&&(r.width>0||r.height>0);
          if(!rendered) continue;
          const src=img.currentSrc||img.src;
          if(!src) continue;
          const u=new URL(src,location.href);
          if(u.origin!==origin) continue;
          candidates.push({
            src:u.pathname+u.search,
            complete:img.complete,
            width:img.naturalWidth,
            height:img.naturalHeight,
            alt:img.getAttribute('alt'),
          });
        }
        const og=document.querySelector('meta[property="og:image"]')?.content||'';
        let ogResult=null;
        if(og){
          ogResult=await new Promise(resolve=>{
            const im=new Image();
            const timer=setTimeout(()=>resolve({src:og,ok:false,width:0,height:0,reason:'timeout'}),10000);
            im.onload=()=>{clearTimeout(timer);resolve({src:og,ok:true,width:im.naturalWidth,height:im.naturalHeight})};
            im.onerror=()=>{clearTimeout(timer);resolve({src:og,ok:false,width:0,height:0,reason:'decode-error'})};
            im.src=og+(og.includes('?')?'&':'?')+'qa_og_decode=1';
          });
        }
        return {candidates,ogResult};
      },O);

      const bad=result.candidates.filter(x=>!x.complete||x.width<1||x.height<1);
      assert.deepEqual(bad,[],`${route}: rendered same-origin image decode failures ${JSON.stringify(bad)}`);
      if(result.ogResult){
        assert.equal(result.ogResult.ok,true,`${route}: og:image failed to decode: ${JSON.stringify(result.ogResult)}`);
        assert.ok(result.ogResult.width>=200&&result.ogResult.height>=200,`${route}: og:image suspiciously small`);
      }
      assert.deepEqual(errors,[],`${route}: page errors ${errors.join(' | ')}`);
      stats.push({route,renderedImages:result.candidates.length,og:Boolean(result.ogResult)});
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
console.log('PASS production media decode:',JSON.stringify(stats));
