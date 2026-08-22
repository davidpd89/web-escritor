import { chromium } from 'playwright';
const b=await chromium.launch({headless:true});
for(const wu of ['domcontentloaded','load']){
  const res=[];
  for(let i=0;i<6;i++){
    const c=await b.newContext({viewport:{width:390,height:844},javaScriptEnabled:false});
    const p=await c.newPage();
    await p.goto('http://127.0.0.1:4173/ai/',{waitUntil:wu});
    const r=await p.evaluate(()=>{
      const de=document.documentElement;
      const row=document.querySelector('.site-footer .social-row');
      return {over:de.scrollWidth-de.clientWidth,
              sheets:document.styleSheets.length,
              rowDisplay:row?getComputedStyle(row).display:'-'};
    });
    res.push(r); await c.close();
  }
  console.log(`waitUntil=${wu}`);
  res.forEach((r,i)=>console.log(`   run${i}: overflow=${r.over} hojas=${r.sheets} social-row=${r.rowDisplay}`));
}
await b.close();
