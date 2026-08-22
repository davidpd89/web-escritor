import { chromium } from 'playwright';
const b=await chromium.launch({headless:true});
const COND={offline:false,downloadThroughput:400*1024/8,uploadThroughput:400*1024/8,latency:300};
for(const wu of ['domcontentloaded','load']){
  const res=[];
  for(let i=0;i<4;i++){
    const c=await b.newContext({viewport:{width:390,height:844},javaScriptEnabled:false});
    const p=await c.newPage();
    const cdp=await c.newCDPSession(p);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions',COND);
    await p.goto('http://127.0.0.1:4173/ai/',{waitUntil:wu});
    const r=await p.evaluate(()=>({over:document.documentElement.scrollWidth-document.documentElement.clientWidth,
      sheets:document.styleSheets.length,
      applied:getComputedStyle(document.body).fontFamily.slice(0,20)}));
    res.push(r); await c.close();
  }
  console.log(`waitUntil=${wu}: `+res.map(r=>`over=${r.over}/hojas=${r.sheets}`).join('  '));
}
await b.close();
