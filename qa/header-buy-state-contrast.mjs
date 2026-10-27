import assert from 'node:assert/strict';
import { chromium } from 'playwright';
const BASE=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch();
const rgb=s=>{const m=s.match(/rgba?\(([^)]+)\)/);assert.ok(m,`Color no RGB: ${s}`);return m[1].split(/[ ,/]+/).slice(0,3).map(Number)};
const lum=c=>c.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
const contrast=(a,b)=>{const x=lum(rgb(a)),y=lum(rgb(b));return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
try{for(const route of ['/libros/','/las-manecillas-del-recuerdo/'])for(const width of [360,768,1280]){const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});try{const response=await page.goto(BASE+route,{waitUntil:'load'});assert.ok(response?.ok(),`${route} ${width}: HTTP ${response?.status()}`);const link=page.locator('.site-header .header-buy');await link.waitFor({state:'visible'});for(const state of ['normal','hover']){if(state==='hover')await link.hover();const v=await link.evaluate(el=>{const s=getComputedStyle(el);return {fg:s.color,bg:s.backgroundColor,text:el.innerText.trim()}});assert.ok(v.text,`${route} ${width}: CTA sin texto`);const ratio=contrast(v.fg,v.bg);assert.ok(ratio>=4.5,`${route} ${width} ${state}: contraste ${ratio.toFixed(2)}:1, ${JSON.stringify(v)}`)}}finally{await page.close()}}}finally{await browser.close()}
console.log('header-buy-state-contrast: OK');