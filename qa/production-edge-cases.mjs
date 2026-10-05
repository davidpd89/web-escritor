import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ORIGIN=(process.env.SITE_BASE_URL||'https://davidportodiaz.com').replace(/\/$/,'');
const ROUTES=[
  '/',
  '/las-manecillas-del-recuerdo/',
  '/cuaderno/',
  '/herramientas/',
  '/editoriales/',
  '/convocatorias-escritores/',
  '/metodologia-editorial/',
  '/mapa-del-sitio/',
];
const VIEWPORTS=[
  {width:360,height:640,label:'phone-360'},
  {width:320,height:568,label:'phone-320-text-200',textScale:true},
];

async function fetchFollow(url){
  let last;
  for(let i=0;i<3;i++){
    try{
      const r=await fetch(url,{
        redirect:'follow',
        headers:{'cache-control':'no-cache','user-agent':'david-porto-production-edge-audit/1.0'},
        signal:AbortSignal.timeout(15000),
      });
      if(r.status!==429&&(r.status<500||r.status>599)) return r;
      last=new Error('transient HTTP '+r.status+' '+url);
    }catch(e){last=e}
    if(i<2) await new Promise(r=>setTimeout(r,700*(i+1)));
  }
  throw last;
}

for(const url of [
  'http://davidportodiaz.com/',
  'http://www.davidportodiaz.com/',
  'https://www.davidportodiaz.com/',
]){
  const r=await fetchFollow(url);
  assert.equal(r.status,200,url+' final HTTP status');
  const final=new URL(r.url);
  assert.equal(final.protocol,'https:',url+' must end on HTTPS');
  assert.equal(final.hostname,'davidportodiaz.com',url+' must end on canonical host');
}

const browser=await chromium.launch({headless:true});
const failures=[];
const report=[];

function msg(route,vp,text){return route+' '+vp.label+': '+text}

try{
  for(const vp of VIEWPORTS){
    for(const route of ROUTES){
      const context=await browser.newContext({
        viewport:{width:vp.width,height:vp.height},
        reducedMotion:'reduce',
      });
      const page=await context.newPage();
      const pageErrors=[];
      page.on('pageerror',e=>pageErrors.push(String(e)));
      await page.route(/(?:gc\.zgo\.at|goatcounter\.com|metricool\.com|clarity\.ms|c\.bing\.com)/,r=>r.abort());
      try{
        const response=await page.goto(ORIGIN+route+'?qa_edge=1',{waitUntil:'domcontentloaded',timeout:25000});
        assert.equal(response?.status(),200,msg(route,vp,'HTTP '+response?.status()));

        const enter=page.locator('[data-intro-enter]').first();
        if(await enter.count()){
          if(await enter.isVisible().catch(()=>false)) await enter.click();
          else await page.evaluate(()=>document.querySelector('[data-intro-enter]')?.click());
          await page.waitForTimeout(250);
        }

        if(vp.textScale){
          await page.addStyleTag({content:'html{font-size:200% !important;} body{min-width:0 !important;}'});
          await page.waitForTimeout(250);
        }

        const structural=await page.evaluate(()=>{
          const ids=[...document.querySelectorAll('[id]')].map(el=>el.id).filter(Boolean);
          const counts=new Map();
          for(const id of ids) counts.set(id,(counts.get(id)||0)+1);
          const duplicates=[...counts].filter(([,n])=>n>1).map(([id,n])=>({id,n}));

          const missingAriaControls=[...document.querySelectorAll('[aria-controls]')]
            .flatMap(el=>String(el.getAttribute('aria-controls')||'').trim().split(/\s+/).filter(Boolean).map(id=>({id,tag:el.tagName.toLowerCase()})))
            .filter(x=>!document.getElementById(x.id));

          const brokenLabels=[...document.querySelectorAll('label[for]')]
            .map(el=>el.getAttribute('for'))
            .filter(Boolean)
            .filter(id=>!document.getElementById(id));

          const brokenHashes=[...document.querySelectorAll('a[href^="#"]')]
            .map(a=>a.getAttribute('href'))
            .filter(h=>h&&h!=='#'&&h.length>1)
            .filter(h=>{
              try{return !document.getElementById(decodeURIComponent(h.slice(1)))}catch{return true}
            });

          const nested=[...document.querySelectorAll('a button, button a, a a, button button')].slice(0,10).map(el=>el.outerHTML.slice(0,180));
          const main=document.querySelectorAll('main').length;
          const h1=[...document.querySelectorAll('h1')].filter(el=>getComputedStyle(el).display!=='none'&&el.getBoundingClientRect().width>0).length;
          const overflow=Math.max(document.documentElement.scrollWidth,document.body?.scrollWidth||0)-window.innerWidth;
          const fixed=[...document.querySelectorAll('body *')].filter(el=>{
            const s=getComputedStyle(el),r=el.getBoundingClientRect();
            return (s.position==='fixed'||s.position==='sticky')&&s.display!=='none'&&s.visibility!=='hidden'&&r.width>window.innerWidth*.85&&r.height>window.innerHeight*.85;
          }).map(el=>({tag:el.tagName.toLowerCase(),id:el.id,cls:String(el.className||'').slice(0,80)}));

          return {duplicates,missingAriaControls,brokenLabels,brokenHashes,nested,main,h1,overflow,fixed};
        });

        assert.equal(structural.main,1,msg(route,vp,'must have exactly one main'));
        assert.ok(structural.h1>=1,msg(route,vp,'visible h1 missing'));
        assert.ok(structural.overflow<=2,msg(route,vp,'horizontal overflow '+structural.overflow+'px'));
        assert.deepEqual(structural.duplicates,[],msg(route,vp,'duplicate ids '+JSON.stringify(structural.duplicates)));
        assert.deepEqual(structural.missingAriaControls,[],msg(route,vp,'broken aria-controls '+JSON.stringify(structural.missingAriaControls)));
        assert.deepEqual(structural.brokenLabels,[],msg(route,vp,'labels point to missing controls '+JSON.stringify(structural.brokenLabels)));
        assert.deepEqual(structural.brokenHashes,[],msg(route,vp,'hash links point to missing ids '+JSON.stringify(structural.brokenHashes)));
        assert.deepEqual(structural.nested,[],msg(route,vp,'nested interactive elements '+JSON.stringify(structural.nested)));
        assert.deepEqual(structural.fixed,[],msg(route,vp,'fixed/sticky UI covers viewport '+JSON.stringify(structural.fixed)));

        const trigger=page.locator('[data-explore-open]').first();
        if(await trigger.count()){
          await trigger.focus();
          await page.keyboard.press('Enter');
          const dialog=page.locator('[data-explore-dialog]').first();
          await dialog.waitFor({state:'visible',timeout:3000});
          assert.equal(await dialog.evaluate(el=>Boolean(el.open)),true,msg(route,vp,'Explore did not open from keyboard'));
          assert.equal(await page.evaluate(()=>Boolean(document.activeElement?.closest('[data-explore-dialog]'))),true,msg(route,vp,'focus did not enter Explore'));
          await page.keyboard.press('Escape');
          await dialog.waitFor({state:'hidden',timeout:3000});
          const focusReturned=await page.evaluate(()=>document.activeElement?.matches?.('[data-explore-open]')||Boolean(document.activeElement?.closest?.('[data-explore-open]')));
          assert.equal(focusReturned,true,msg(route,vp,'focus did not return to Explore trigger after Escape'));
        }

        const focusSamples=[];
        for(let i=0;i<24;i++){
          await page.keyboard.press('Tab');
          const state=await page.evaluate(()=>{
            const el=document.activeElement;
            if(!el||el===document.body||el===document.documentElement) return null;
            const r=el.getBoundingClientRect();
            const s=getComputedStyle(el);
            return {
              tag:el.tagName.toLowerCase(),
              id:el.id||'',
              text:(el.getAttribute('aria-label')||el.textContent||'').trim().slice(0,80),
              hidden:el.closest('[aria-hidden="true"]')!==null||s.visibility==='hidden'||s.display==='none',
              intersects:r.bottom>0&&r.right>0&&r.top<innerHeight&&r.left<innerWidth,
            };
          });
          if(state) focusSamples.push(state);
        }
        assert.ok(focusSamples.length>=3,msg(route,vp,'too few keyboard-focusable controls'));
        assert.equal(focusSamples.some(x=>x.hidden),false,msg(route,vp,'keyboard focus entered hidden/aria-hidden content'));
        assert.equal(focusSamples.some(x=>!x.intersects),false,msg(route,vp,'keyboard focus landed outside viewport'));

        assert.deepEqual(pageErrors,[],msg(route,vp,'page errors '+pageErrors.join(' | ')));
        report.push({route,viewport:vp.label,focusSamples:focusSamples.length});
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
console.log('PASS production edge audit:',JSON.stringify(report));
