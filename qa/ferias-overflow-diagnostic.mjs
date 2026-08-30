import { chromium } from 'playwright';

const ORIGIN=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:390,height:900},reducedMotion:'reduce'});
const page=await context.newPage();
await page.goto(`${ORIGIN}/ferias.html`,{waitUntil:'load'});
await page.evaluate(()=>document.fonts?.ready);
await page.evaluate(()=>document.documentElement.style.zoom='2');
await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
const report=await page.evaluate(()=>{
  const viewport=document.documentElement.clientWidth;
  const scroll=document.documentElement.scrollWidth;
  const items=[];
  for(const el of document.querySelectorAll('body *')){
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden') continue;
    const r=el.getBoundingClientRect();
    if(!Number.isFinite(r.left)||!Number.isFinite(r.right)||r.width<=0||r.height<=0) continue;
    if(r.right>viewport+1||r.left<-1||el.scrollWidth>el.clientWidth+1){
      items.push({
        tag:el.tagName.toLowerCase(),
        id:el.id||null,
        class:[...el.classList].join('.')||null,
        text:(el.textContent||'').replace(/\s+/g,' ').trim().slice(0,120),
        left:+r.left.toFixed(2),right:+r.right.toFixed(2),width:+r.width.toFixed(2),
        clientWidth:el.clientWidth,scrollWidth:el.scrollWidth,
        display:cs.display,position:cs.position,
        gridTemplateColumns:cs.gridTemplateColumns,
        whiteSpace:cs.whiteSpace,
        overflowWrap:cs.overflowWrap,
        minWidth:cs.minWidth,maxWidth:cs.maxWidth
      });
    }
  }
  return {viewport,scroll,overflow:scroll-viewport,items:items.sort((a,b)=>Math.max(b.right-viewport,b.scrollWidth-b.clientWidth)-Math.max(a.right-viewport,a.scrollWidth-a.clientWidth)).slice(0,40)};
});
console.log(JSON.stringify(report,null,2));
await browser.close();
