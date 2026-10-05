import assert from 'node:assert/strict';
import { chromium, firefox, webkit } from 'playwright';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const ROUTES=[
  '/',
  '/las-manecillas-del-recuerdo/',
  '/libros/samuel-entre-mundos/',
  '/cuaderno/',
  '/herramientas/',
  '/asistente/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
  '/prensa.html',
  '/mapa-del-sitio/',
];
const ENGINES={chromium,firefox,webkit};
const failures=[];

if(S){
  const r=await fetch(`${O}/_release/${S}.json?qa_cross_engine=1`,{signal:AbortSignal.timeout(15000)});
  assert.equal(r.status,200,'release marker missing');
  assert.deepEqual(await r.json(),{schemaVersion:1,sha:S},'release marker mismatch');
}

async function blockNoise(page){
  await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
}

async function audit(engineName,browser,route){
  const context=await browser.newContext({viewport:{width:1280,height:800},reducedMotion:'reduce'});
  const page=await context.newPage();
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  await blockNoise(page);
  try{
    const u=`${O}${route}${route.includes('?')?'&':'?'}qa_prod_engine=${engineName}`;
    const response=await page.goto(u,{waitUntil:'domcontentloaded',timeout:25000});
    assert.equal(response?.status(),200,`${engineName} ${route}: HTTP ${response?.status()}`);
    assert.ok((await page.locator('main').count())===1,`${engineName} ${route}: main landmark`);
    assert.ok((await page.locator('h1').first().innerText()).trim(),`${engineName} ${route}: empty h1`);

    const enter=page.locator('[data-intro-enter]').first();
    if(await enter.count()){
      if(await enter.isVisible().catch(()=>false)) await enter.click();
      else await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
      await page.waitForTimeout(350);
    }

    const trigger=page.locator('[data-explore-open]').first();
    assert.ok(await trigger.count(),`${engineName} ${route}: Explore trigger missing`);
    if(!(await trigger.isVisible().catch(()=>false))){
      await page.evaluate(()=>window.scrollTo(0,400));
      await page.waitForTimeout(250);
    }
    assert.ok(await trigger.isVisible().catch(()=>false),`${engineName} ${route}: Explore trigger invisible`);
    await trigger.click();
    const dialog=page.locator('[data-explore-dialog]').first();
    await page.waitForTimeout(120);
    assert.equal(await dialog.evaluate(el=>Boolean(el.open)),true,`${engineName} ${route}: Explore did not open`);
    assert.equal(await page.evaluate(()=>Boolean(document.activeElement?.closest('[data-explore-dialog]'))),true,`${engineName} ${route}: focus did not enter Explore`);
    const close=page.locator('[data-explore-close]').first();
    if(await close.count()) await close.click();

    await page.setViewportSize({width:375,height:667});
    await page.waitForTimeout(100);
    const geometry=await page.evaluate(()=>({
      scrollWidth:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0),
      innerWidth:window.innerWidth,
      h1Visible:Boolean(document.querySelector('h1')?.getBoundingClientRect().width),
    }));
    assert.ok(geometry.scrollWidth<=geometry.innerWidth+1,`${engineName} ${route}: mobile overflow ${geometry.scrollWidth}>${geometry.innerWidth}`);
    assert.equal(geometry.h1Visible,true,`${engineName} ${route}: h1 not rendered after resize`);
    assert.deepEqual(pageErrors,[],`${engineName} ${route}: page errors: ${pageErrors.join(' | ')}`);
    console.log(`PASS [${engineName}] ${route}`);
  }catch(e){
    failures.push(`[${engineName}] ${route}: ${e.message}`);
    console.error(`FAIL [${engineName}] ${route}: ${e.message}`);
  }finally{
    await context.close();
  }
}

for(const [name,launcher] of Object.entries(ENGINES)){
  const browser=await launcher.launch({headless:true});
  try{
    for(const route of ROUTES) await audit(name,browser,route);
  }finally{
    await browser.close();
  }
}

assert.deepEqual(failures,[],failures.join('\n'));
console.log(`PASS production cross-engine smoke: ${ROUTES.length} routes x ${Object.keys(ENGINES).length} engines`);
