import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import { chromium } from 'playwright';
import { assertProductionRelease } from './production-release-marker.mjs';

const O=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const S=(process.env.EXPECTED_RELEASE_SHA||'').trim();
const day=(process.env.QA_SAMPLE_DAY||new Date().toISOString().slice(0,10));
const seed=(process.env.QA_SAMPLE_SEED||`${S||'live'}:${day}`).trim();
const registry=JSON.parse(fs.readFileSync('data/content-registry.json','utf8'));
const defs=registry.defaults||{};

const all=[...new Map(registry.entries
  .map(x=>({...defs,...x}))
  .filter(x=>x.status==='public'&&String(x.sourceFile||'').endsWith('.html'))
  .filter(x=>!String(x.url||'').includes('#'))
  .map(x=>[x.url,x])).values()];

const mandatory=[
  '/', '/libros/', '/las-manecillas-del-recuerdo/', '/libros/samuel-entre-mundos/',
  '/cuaderno/', '/herramientas/', '/editoriales/', '/convocatorias-escritores/',
  '/metodologia-editorial/', '/prensa.html', '/mapa-del-sitio/'
];

function score(route){
  return crypto.createHash('sha256').update(seed+'\n'+route).digest('hex');
}
function pick(items,n){
  return items.slice().sort((a,b)=>score(a.url).localeCompare(score(b.url))).slice(0,n).map(x=>x.url);
}
const buckets={
  editoriales:all.filter(x=>x.url.startsWith('/editoriales/')&&x.url!=='/editoriales/'),
  tools:all.filter(x=>x.url.startsWith('/herramientas/')&&x.url!=='/herramientas/'),
  notebook:all.filter(x=>(x.url.startsWith('/cuaderno/')&&x.url!=='/cuaderno/')||x.url.startsWith('/recomendaciones/')),
  works:all.filter(x=>/^\/(?:libros\/|las-manecillas-del-recuerdo\/|fragmento\/|universo\/|clubes-de-lectura\/)/.test(x.url)&&!mandatory.includes(x.url)),
};
const already=new Set([...mandatory,...Object.values(buckets).flat().map(x=>x.url)]);
const other=all.filter(x=>!already.has(x.url));
const routes=[...new Set([
  ...mandatory,
  ...pick(buckets.editoriales,5),
  ...pick(buckets.tools,4),
  ...pick(buckets.notebook,3),
  ...pick(buckets.works,3),
  ...pick(other,3),
])];

const scenarios=[
  {label:'phone-320-dark-dpr3',viewport:{width:320,height:568},isMobile:true,hasTouch:true,deviceScaleFactor:3,colorScheme:'dark'},
  {label:'tablet-landscape-touch',viewport:{width:1024,height:768},isMobile:false,hasTouch:true,deviceScaleFactor:2,colorScheme:'light'},
  {label:'desktop-keyboard',viewport:{width:1440,height:900},isMobile:false,hasTouch:false,deviceScaleFactor:1,colorScheme:'light',keyboard:true},
];

await assertProductionRelease({origin:O,sha:S,label:'rotating-device'});
const browser=await chromium.launch({headless:true});
const failures=[];
const report=[];
fs.mkdirSync('artifacts/rotating-device',{recursive:true});

async function gotoRetry(page,route,label){
  let last=null;
  for(let attempt=0;attempt<3;attempt++){
    last=await page.goto(`${O}${route}?qa_rotating=${encodeURIComponent(label)}&sample=${encodeURIComponent(day)}&attempt=${attempt}`,{
      waitUntil:'domcontentloaded',timeout:25000
    }).catch(()=>null);
    if(last&&last.status()!==429&&(last.status()<500||last.status()>599)) return last;
    await page.waitForTimeout(650*(attempt+1));
  }
  return last;
}

async function dismissIntro(page){
  const enter=page.locator('[data-intro-enter]').first();
  if(await enter.count()){
    if(await enter.isVisible().catch(()=>false)) await enter.click().catch(()=>{});
    else await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
    const intro=page.locator('[data-intro]').first();
    if(await intro.count()) await intro.waitFor({state:'hidden',timeout:3000}).catch(()=>{});
  }
}

async function headerCollisionProbe(page,route){
  const header=page.locator('.site-header').first();
  if(!(await header.count())) return {applicable:false};
  const state=await header.evaluate(el=>{
    const controls=[...el.querySelectorAll('a,button')].filter(node=>{
      const s=getComputedStyle(node),r=node.getBoundingClientRect();
      return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;
    }).map(node=>{
      const r=node.getBoundingClientRect();
      return {
        key:node.getAttribute('aria-label')||node.textContent?.trim()||node.tagName,
        left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,
      };
    });
    const collisions=[];
    for(let i=0;i<controls.length;i++) for(let j=i+1;j<controls.length;j++){
      const a=controls[i],b=controls[j];
      const x=Math.min(a.right,b.right)-Math.max(a.left,b.left);
      const y=Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
      if(x>1&&y>1) collisions.push({a:a.key,b:b.key,x:Math.round(x),y:Math.round(y)});
    }
    return {
      controls,
      collisions,
      clipped:controls.filter(x=>x.left<-1||x.right>innerWidth+1||x.top<-1),
      headerRect:(()=>{const r=el.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom}})(),
    };
  });
  assert.deepEqual(state.collisions,[],`${route}: header controls overlap ${JSON.stringify(state.collisions)}`);
  assert.deepEqual(state.clipped,[],`${route}: header controls clipped ${JSON.stringify(state.clipped)}`);
  return {applicable:true,controls:state.controls.length};
}

async function skipLinkProbe(page,route){
  const shell=await page.locator('.site-header').count();
  if(!shell) return {applicable:false};
  const skip=page.locator('a.skip-link').first();
  assert.equal(await skip.count(),1,`${route}: shell page missing unique skip link`);
  await page.evaluate(()=>{window.scrollTo(0,0); if(document.activeElement instanceof HTMLElement) document.activeElement.blur()});
  await page.locator('body').click({position:{x:2,y:2}}).catch(()=>{});
  await page.keyboard.press('Tab');
  assert.equal(await skip.evaluate(el=>el===document.activeElement),true,`${route}: first Tab does not focus skip link`);
  const visible=await skip.evaluate(el=>{
    const r=el.getBoundingClientRect(),s=getComputedStyle(el);
    return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight;
  });
  assert.equal(visible,true,`${route}: skip link focused but not visible`);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(80);
  const target=await page.evaluate(()=>{
    const main=document.querySelector('main');
    const active=document.activeElement;
    const r=main?.getBoundingClientRect();
    const header=document.querySelector('.site-header');
    const hr=header?.getBoundingClientRect();
    return {
      active:Boolean(main&&active===main),
      hash:location.hash,
      top:r?.top??null,
      headerBottom:hr?.bottom??0,
    };
  });
  assert.equal(target.active,true,`${route}: skip link did not move focus to main`);
  assert.ok(target.hash==='#contenido'||target.hash==='',`${route}: unexpected skip-link hash ${target.hash}`);
  if(target.top!==null) assert.ok(target.top>=target.headerBottom-2,`${route}: focused main is obscured by header (${target.top}<${target.headerBottom})`);
  return {applicable:true};
}

async function keyboardProbe(page,route){
  const expected=await page.locator('a[href]:visible,button:visible,input:not([type="hidden"]):visible,select:visible,textarea:visible,[tabindex]:not([tabindex="-1"]):visible').count();
  if(expected===0) return {expected,unique:0};
  const seen=new Set();
  const probes=Math.min(14,Math.max(4,expected));
  for(let i=0;i<probes;i++){
    await page.keyboard.press('Tab');
    const state=await page.evaluate(()=>{
      const el=document.activeElement;
      if(!el||el===document.body) return {key:'BODY',ok:false,reason:'focus on body'};
      const r=el.getBoundingClientRect();
      const s=getComputedStyle(el);
      const hidden=el.closest('[aria-hidden="true"],[inert]');
      const key=el.id||el.getAttribute('href')||el.getAttribute('name')||el.getAttribute('aria-label')||el.textContent?.trim().slice(0,60)||el.tagName;
      return {
        key:String(key),
        ok:!hidden&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth,
        reason:hidden?'inside aria-hidden/inert':`rect ${Math.round(r.left)},${Math.round(r.top)} ${Math.round(r.width)}x${Math.round(r.height)}`,
      };
    });
    seen.add(state.key);
    assert.equal(state.ok,true,`${route}: Tab focus unusable (${state.key}; ${state.reason})`);
  }
  if(expected>=3) assert.ok(seen.size>=3,`${route}: keyboard focus appears trapped; only ${seen.size} targets reached`);
  return {expected,unique:seen.size};
}

try{
  for(const scenario of scenarios){
    for(const route of routes){
      const context=await browser.newContext({
        viewport:scenario.viewport,
        isMobile:scenario.isMobile,
        hasTouch:scenario.hasTouch,
        deviceScaleFactor:scenario.deviceScaleFactor,
        colorScheme:scenario.colorScheme,
        reducedMotion:'reduce',
      });
      const page=await context.newPage();
      const pageErrors=[];
      const badResponses=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      page.on('response',r=>{
        try{
          const u=new URL(r.url());
          const t=r.request().resourceType();
          if(u.origin===O&&r.status()>=400&&['document','script','stylesheet','image','font'].includes(t)){
            badResponses.push(`${r.status()} ${t} ${u.pathname}`);
          }
        }catch{}
      });
      await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
      try{
        const nav=await gotoRetry(page,route,scenario.label);
        assert.equal(nav?.status(),200,`${scenario.label} ${route}: HTTP ${nav?.status()}`);
        await dismissIntro(page);
        await page.waitForTimeout(180);

        const state=await page.evaluate(()=>({
          h1:[...document.querySelectorAll('h1')].filter(el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0}).length,
          mainText:(document.querySelector('main')?.innerText||'').replace(/\s+/g,' ').trim().length,
          overflow:Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0)-document.documentElement.clientWidth,
          giant:[...document.querySelectorAll('body *')].filter(el=>{
            const s=getComputedStyle(el),r=el.getBoundingClientRect();
            return ['fixed','sticky'].includes(s.position)&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>innerWidth*.9&&r.height>innerHeight*.86;
          }).map(el=>el.id||String(el.className||'').slice(0,80)||el.tagName),
          collapsed:[...document.querySelectorAll('main a[href],main button,main input:not([type="hidden"]),main select,main textarea')].filter(el=>{
            const s=getComputedStyle(el); if(s.display==='none'||s.visibility==='hidden') return false;
            const r=el.getBoundingClientRect(); return r.width<=0||r.height<=0;
          }).slice(0,8).map(el=>el.outerHTML.slice(0,180)),
        }));
        assert.equal(state.h1,1,`${scenario.label} ${route}: expected one visible H1, got ${state.h1}`);
        assert.ok(state.mainText>80,`${scenario.label} ${route}: critical main content too small (${state.mainText})`);
        assert.ok(state.overflow<=1,`${scenario.label} ${route}: horizontal overflow ${state.overflow}px`);
        assert.deepEqual(state.giant,[],`${scenario.label} ${route}: giant fixed/sticky overlay ${JSON.stringify(state.giant)}`);
        assert.deepEqual(state.collapsed,[],`${scenario.label} ${route}: collapsed visible controls ${JSON.stringify(state.collapsed)}`);

        const header=await headerCollisionProbe(page,route);
        let keyboard=null,skipLink=null;
        if(scenario.keyboard){
          skipLink=await skipLinkProbe(page,route);
          keyboard=await keyboardProbe(page,route);
        }
        assert.deepEqual(pageErrors,[],`${scenario.label} ${route}: page errors ${pageErrors.join(' | ')}`);
        assert.deepEqual([...new Set(badResponses)],[],`${scenario.label} ${route}: same-origin resource failures ${[...new Set(badResponses)].join(' | ')}`);
        report.push({route,scenario:scenario.label,header,keyboard,skipLink});
      }catch(e){
        const safe=(scenario.label+'-'+route).replace(/[^a-z0-9_-]+/gi,'-').replace(/^-+|-+$/g,'').slice(0,140);
        await page.screenshot({path:`artifacts/rotating-device/${safe||'failure'}.png`,fullPage:true}).catch(()=>{});
        failures.push(String(e?.message||e));
      }finally{
        await context.close();
      }
    }
  }
}finally{
  await browser.close();
}

console.log('ROTATING SAMPLE',JSON.stringify({seed,day,routes},null,2));
assert.deepEqual(failures,[],failures.slice(0,80).join('\n'));
console.log(`PASS rotating production device audit: ${routes.length} routes x ${scenarios.length} scenarios (${report.length} checks)`);
