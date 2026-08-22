import { chromium } from 'playwright';
const b=await chromium.launch({headless:true});
for(const js of [true,false]){
  for(const w of [320,360,390,768,1280]){
    const c=await b.newContext({viewport:{width:w,height:900},javaScriptEnabled:js});
    const p=await c.newPage();
    await p.goto('http://127.0.0.1:4173/ai/',{waitUntil:'load'});
    const r=await p.evaluate(()=>{
      const de=document.documentElement;const lim=de.clientWidth;
      let culprit=null;
      for(const el of document.querySelectorAll('body *')){
        const bb=el.getBoundingClientRect();
        if(bb.right>lim+1&&bb.width>0){culprit=`${el.tagName}.${(typeof el.className==='string'?el.className:'').split(' ')[0]} w=${Math.round(bb.width)} right=${Math.round(bb.right)}`;break;}
      }
      const row=document.querySelector('.site-footer .social-row');
      return {over:de.scrollWidth-de.clientWidth,culprit,rowDisplay:row?getComputedStyle(row).display:'(sin row)'};
    }).catch(e=>({err:String(e).slice(0,80)}));
    if(r.over>1||r.err) console.log(`js=${js} @${w}`,JSON.stringify(r));
    await c.close();
  }
}
console.log('done');
await b.close();
