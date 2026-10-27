import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';
const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const today=JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json','utf8')).generated_for;
const controls=['[data-radar-search]','[data-radar-type]','[data-radar-genre]','[data-radar-kind]','.tool-check:has([data-radar-soon])','.tool-check:has([data-radar-expired])','[data-radar-clear]','[data-radar-calendar]','[data-radar-source]'];
const browser=await chromium.launch({headless:true});
try{for(const width of [320,390,520,768,1280]){const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});await context.addInitScript(t=>{window.__DP_RADAR_TODAY__=t;localStorage.setItem('nl-popup-ts',String(Date.now()));},today);const page=await context.newPage();await page.goto(origin+'/convocatorias-escritores/',{waitUntil:'networkidle'});
for(const selector of controls){const el=page.locator(selector).first();assert.equal(await el.count(),1,selector);await el.scrollIntoViewIfNeeded();const hit=await el.evaluate(node=>{const r=node.getBoundingClientRect();const x=r.left+r.width/2,y=r.top+r.height/2;const target=document.elementFromPoint(x,y);return{width:r.width,height:r.height,inViewport:x>=0&&x<innerWidth&&y>=0&&y<innerHeight,hit:!!target&&(node===target||node.contains(target))};});assert.ok(hit.inViewport&&hit.hit,`${width}px ${selector}: ${JSON.stringify(hit)}`);assert.ok(hit.width>=24&&hit.height>=24,`${width}px ${selector}: objetivo menor de 24px`);await el.click({trial:true,timeout:3000});}
await context.close();}console.log('PASS geometric hit testing');}finally{await browser.close();}