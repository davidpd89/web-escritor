import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';

const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const out=process.env.QA_OUT||'qa-artifacts';
await fs.mkdir(out,{recursive:true});

const editorialData=JSON.parse(await fs.readFile('editoriales/editoriales-data.json','utf8')).publishers;
const radarPublic=JSON.parse(await fs.readFile('convocatorias-escritores/opportunities.json','utf8'));
const radarItems=radarPublic.items;
const fixedToday=radarPublic.generated_for;
const sizes=[[320,900],[390,900],[768,1000],[1024,900],[1440,1000],[1728,1000],[844,390]];

const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const genreCount=genre=>editorialData.filter(x=>(x.genres||[]).some(g=>norm(g)===norm(genre))).length;
const statusCount=status=>editorialData.filter(x=>x.status===status).length;
const closedFantasy=editorialData.filter(x=>x.status==='closed'&&(x.genres||[]).some(g=>norm(g)==='fantasia')).length;
const directCount=editorialData.filter(x=>x.direct_submission===true).length;
const chileCount=editorialData.filter(x=>x.country==='Chile').length;
const radarGenreCount=genre=>radarItems.filter(x=>(x.genres||[]).some(g=>norm(g)===norm(genre))).length;
const daysUntil=(deadline,base)=>Math.round((new Date(deadline+'T00:00:00Z')-new Date(base+'T00:00:00Z'))/86400000);
const soonCount=radarItems.filter(x=>{const d=daysUntil(x.deadline,fixedToday);return d>=0&&d<=7}).length;

const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[];
async function open(route,{w=1440,h=1000,js=true,fixed=false}={}){
  const c=await browser.newContext({viewport:{width:w,height:h},javaScriptEnabled:js,reducedMotion:'reduce'});
  const p=await c.newPage();
  p.on('pageerror',e=>errors.push(`${route}: ${e.message}`));
  p.on('console',m=>{if(m.type()==='error')errors.push(`${route}: ${m.text()}`)});
  if(fixed&&js)await p.addInitScript(t=>{window.__DP_RADAR_TODAY__=t},fixedToday);
  const r=await p.goto(origin+route,{waitUntil:js?'networkidle':'load'});
  assert.equal(r.status(),200,route);
  return[c,p];
}
// These pages ship a strict CSP (style-src 'self'), so addStyleTag's inline
// sheet is refused. Inject WCAG stress styles through DevTools instead.
async function applyInspectorStyles(c,p,cssText){
  const cdp=await c.newCDPSession(p);await cdp.send('Page.enable');await cdp.send('DOM.enable');await cdp.send('CSS.enable');
  const{frameTree}=await cdp.send('Page.getFrameTree');
  const{styleSheetId}=await cdp.send('CSS.createStyleSheet',{frameId:frameTree.frame.id});
  await cdp.send('CSS.setStyleSheetText',{styleSheetId,text:cssText});
}
const visible=(p,s)=>p.locator(`${s}:visible`).count();
async function noOverflow(p,label){const x=await p.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);assert.ok(x<=1,`${label} overflow ${x}px`)}

{
  const[c,p]=await open('/editoriales/');
  assert.equal(await visible(p,'[data-editorial-card]'),editorialData.length);
  const q=p.locator('[data-editoriales-search]');
  for(const [term,n] of [['MINOTAURO',1],['fantasia',genreCount('fantasía')],['zzzz-sin-resultados',0],['  Minotauro  ',1]]){
    await q.fill(term);assert.equal(await visible(p,'[data-editorial-card]'),n);
  }
  await p.locator('[data-editoriales-reset]').click();
  await p.locator('[data-editoriales-country]').selectOption('Chile');
  assert.equal(await visible(p,'[data-editorial-card]'),chileCount);
  await p.locator('[data-editoriales-reset]').click();
  await p.locator('[data-editoriales-status]').selectOption('closed');
  assert.equal(await visible(p,'[data-editorial-card]'),statusCount('closed'));
  await p.locator('[data-editoriales-genre]').selectOption('fantasía');
  assert.equal(await visible(p,'[data-editorial-card]'),closedFantasy);
  await p.goBack();assert.equal(await p.locator('[data-editoriales-genre]').inputValue(),'');assert.equal(await p.locator('[data-editoriales-country]').inputValue(),'');
  await p.goForward();assert.equal(await p.locator('[data-editoriales-genre]').inputValue(),'fantasía');
  await p.reload({waitUntil:'networkidle'});assert.equal(await p.locator('[data-editoriales-status]').inputValue(),'closed');
  await p.goto(origin+'/editoriales/#estado=invalid&genero=invalid&pais=invalid&directo=9',{waitUntil:'networkidle'});
  assert.equal(await p.locator('[data-editoriales-status]').inputValue(),'');
  assert.equal(await p.locator('[data-editoriales-genre]').inputValue(),'');
  assert.equal(await p.locator('[data-editoriales-direct]').isChecked(),false);
  await p.locator('[data-editoriales-direct]').check();
  assert.equal(await visible(p,'[data-editorial-card]'),directCount);
  await noOverflow(p,'editoriales filters');await c.close();
}
{
  const[c,p]=await open('/convocatorias-escritores/',{fixed:true});
  assert.equal(await visible(p,'[data-radar-item]'),radarItems.length);
  const d=await p.evaluate(today=>({
    a:DPRadarDates.daysUntil(today,today),
    b:DPRadarDates.daysUntil('2026-10-03',today),
    c:DPRadarDates.daysUntil('2026-10-09',today),
    d:DPRadarDates.daysUntil('2026-10-10',today),
    e:DPRadarDates.daysUntil('2026-10-01',today)
  }),fixedToday);
  assert.deepEqual(d,{a:0,b:1,c:7,d:8,e:-1});
  const rel=await p.locator('[data-radar-relative]').allTextContents();assert.ok(rel.every(t=>t.includes('faltan')));
  await p.locator('[data-radar-search]').fill('KUTXA');assert.equal(await visible(p,'[data-radar-item]'),1);
  await p.locator('[data-radar-clear]').click();
  await p.locator('[data-radar-genre]').selectOption('novela');assert.equal(await visible(p,'[data-radar-item]'),radarGenreCount('novela'));
  await p.locator('[data-radar-clear]').click();
  await p.locator('[data-radar-soon]').check();assert.equal(await visible(p,'[data-radar-item]'),soonCount);
  assert.equal(await p.locator('[data-radar-filter-empty]').isVisible(),soonCount===0);
  await p.locator('[data-radar-clear]').click();assert.equal(await visible(p,'[data-radar-item]'),radarItems.length);
  assert.equal(await p.locator('[data-radar-calendar]').getAttribute('href'),'/convocatorias-escritores/deadlines.ics');
  await noOverflow(p,'radar filters');await c.close();
}
for(const route of ['/editoriales/','/convocatorias-escritores/']){
  const[c,p]=await open(route,{js:false});
  assert.equal(await p.locator(route.startsWith('/editoriales')?'[data-editorial-card]':'[data-radar-item]').count(),route.startsWith('/editoriales')?editorialData.length:radarItems.length);
  if(route.includes('convocatorias')){
    const txt=await p.locator('[data-radar-item] time').allTextContents();
    assert.ok(txt.includes('21/11/2026')&&txt.includes('09/10/2026'));
    assert.equal(await p.locator('[data-radar-calendar]').getAttribute('href'),'/convocatorias-escritores/deadlines.ics');
  }
  await c.close();
}
for(const slug of ['minotauro','nocturna-ediciones','duermevela-ediciones','harpercollins-iberica','editorial-cerbero','suseya-ediciones','nova','ediciones-raven']){
  const[c,p]=await open(`/editoriales/${slug}/`);
  assert.equal(await p.locator('h1').count(),1);
  assert.ok(await p.locator('a[target="_blank"][rel*="noopener"]').count()>=1);
  await noOverflow(p,slug);await c.close();
}
for(const [w,h] of sizes)for(const route of ['/editoriales/','/convocatorias-escritores/']){
  const[c,p]=await open(route,{w,h,fixed:route.includes('convocatorias')});await noOverflow(p,`${route} ${w}x${h}`);
  if(w===390||w===1440)await p.screenshot({path:path.join(out,`${route.includes('editoriales')?'editoriales':'convocatorias'}-${w}.png`),fullPage:true});
  await c.close();
}
for(const w of [390,1440]){
  const[c,p]=await open('/editoriales/minotauro/',{w,h:w===390?900:1000});
  await p.screenshot({path:path.join(out,`minotauro-${w}.png`),fullPage:true});await c.close();
}
{
  const[c,p]=await open('/editoriales/',{w:390,h:900});await p.locator('[data-editoriales-search]').fill('zzzz-sin-resultados');
  assert.equal(await p.locator('[data-editoriales-empty]').isVisible(),true);
  await p.screenshot({path:path.join(out,'editoriales-empty-390.png'),fullPage:true});await c.close();
}
{
  const[c,p]=await open('/convocatorias-escritores/',{w:390,h:900,fixed:true});
  await applyInspectorStyles(c,p,'*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');
  await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  await noOverflow(p,'text spacing');await p.evaluate(()=>document.documentElement.style.zoom='2');await noOverflow(p,'zoom 200%');
  await p.keyboard.press('Tab');assert.notEqual(await p.evaluate(()=>document.activeElement?.tagName),'BODY');await c.close();
}
assert.deepEqual(errors,[],`Browser errors:\n${errors.join('\n')}`);
await browser.close();
console.log(`OK professional resources browser QA (${editorialData.length} editoriales, ${radarItems.length} oportunidades)`);
