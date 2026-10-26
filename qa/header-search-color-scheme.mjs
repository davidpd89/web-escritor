import assert from 'node:assert/strict';
import {chromium} from 'playwright';
const BASE=(process.env.QA_ORIGIN||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch();
const rgb=s=>{const m=s.match(/rgba?\(([^)]+)\)/);assert.ok(m,`Color inválido: ${s}`);return m[1].split(/[ ,/]+/).slice(0,3).map(Number)};
const L=s=>rgb(s).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
const ratio=(a,b)=>{const x=L(a),y=L(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
try{for(const scheme of ['light','dark'])for(const width of [360,1280]){const page=await browser.newPage({viewport:{width,height:900},colorScheme:scheme,reducedMotion:'reduce'});try{const response=await page.goto(BASE+'/libros/',{waitUntil:'load'});assert.ok(response?.ok(),`/libros/ ${scheme}: HTTP ${response?.status()}`);const el=page.locator('.site-header .header-search');await el.waitFor({state:'visible'});const v=await el.evaluate(e=>{const s=getComputedStyle(e);const h=getComputedStyle(e.closest('.site-header'));const body=getComputedStyle(document.body);return {fg:s.color,bg:h.backgroundColor,body:body.backgroundColor,fontSize:parseFloat(s.fontSize)}});const bg=/rgba\([^)]*,\s*0(?:\.0+)?\)/.test(v.bg)?v.body:v.bg;const c=ratio(v.fg,bg);assert.ok(c>=4.5,`/libros/ ${scheme} ${width}px: búsqueda ${c.toFixed(2)}:1, ${JSON.stringify(v)}`)}finally{await page.close()}}}finally{await browser.close()}
console.log('header-search-color-scheme: OK');