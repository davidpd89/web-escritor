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
const radarWatch=radarPublic.watchlist||[];
const radarAll=[...radarItems,...radarWatch];
const fixedToday=radarPublic.generated_for;
const sizes=[[320,900],[390,900],[768,1000],[1024,900],[1440,1000],[1728,1000],[844,390]];

const norm=(value='')=>String(value).toLocaleLowerCase('es').normalize('NFD').replace(/(?<!n)\u0303|(?<!u)\u0308|[\u0300-\u0302\u0304-\u0307\u0309-\u036f]/g,'').normalize('NFC').trim();
const genreCount=genre=>editorialData.filter(x=>(x.genres||[]).some(g=>norm(g)===norm(genre))).length;
const statusCount=status=>editorialData.filter(x=>x.status===status).length;
const closedFantasy=editorialData.filter(x=>x.status==='closed'&&(x.genres||[]).some(g=>norm(g)==='fantasia')).length;
const directCount=editorialData.filter(x=>x.direct_submission===true).length;
const chileCount=editorialData.filter(x=>x.country==='Chile').length;
const radarGenreCount=genre=>radarAll.filter(x=>(x.genres||[]).some(g=>norm(g)===norm(genre))).length;
const daysUntil=(deadline,base)=>Math.round((new Date(deadline+'T00:00:00Z')-new Date(base+'T00:00:00Z'))/86400000);
const offsetDate=(base,days)=>{
  const value=new Date(base+'T00:00:00Z');
  value.setUTCDate(value.getUTCDate()+days);
  return value.toISOString().slice(0,10);
};
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
  for(const [term,n] of [['MINOTAURO',1],['zzzz-sin-resultados',0],['  Minotauro  ',1]]){
    await q.fill(term);assert.equal(await visible(p,'[data-editorial-card]'),n);
  }
  await q.fill('fantasia');
  assert.ok(await visible(p,'[data-editorial-card]')>=genreCount('fantasía'),'la búsqueda libre debe incluir al menos todas las fichas etiquetadas como fantasía');
  await p.locator('[data-editoriales-reset]').click();
  assert.equal(await p.locator('[data-editoriales-sort]').count(),1);
  await p.locator('[data-editoriales-sort]').selectOption('name');
  const sortedNames=await p.locator('[data-editorial-card]').evaluateAll(nodes=>nodes.map(n=>n.dataset.name));
  assert.deepEqual(sortedNames,[...sortedNames].sort((a,b)=>a.localeCompare(b,'es',{sensitivity:'base'})));
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
  await p.goto(origin+'/editoriales/#estado=invalid&genero=invalid&pais=invalid&orden=invalid&directo=9',{waitUntil:'networkidle'});
  assert.equal(await p.locator('[data-editoriales-status]').inputValue(),'');
  assert.equal(await p.locator('[data-editoriales-genre]').inputValue(),'');
  assert.equal(await p.locator('[data-editoriales-sort]').inputValue(),'availability');
  assert.equal(await p.locator('[data-editoriales-direct]').isChecked(),false);
  await p.locator('[data-editoriales-direct]').check();
  assert.equal(await visible(p,'[data-editorial-card]'),directCount);
  await noOverflow(p,'editoriales filters');await c.close();
}
{
  const[c,p]=await open('/convocatorias-escritores/',{fixed:true});
  assert.equal(await visible(p,'[data-radar-item]'),radarAll.length);
  const probeDates={
    today:fixedToday,
    tomorrow:offsetDate(fixedToday,1),
    plus7:offsetDate(fixedToday,7),
    plus8:offsetDate(fixedToday,8),
    yesterday:offsetDate(fixedToday,-1)
  };
  const d=await p.evaluate(dates=>({
    today:DPRadarDates.daysUntil(dates.today,dates.today),
    tomorrow:DPRadarDates.daysUntil(dates.tomorrow,dates.today),
    plus7:DPRadarDates.daysUntil(dates.plus7,dates.today),
    plus8:DPRadarDates.daysUntil(dates.plus8,dates.today),
    yesterday:DPRadarDates.daysUntil(dates.yesterday,dates.today)
  }),probeDates);
  assert.deepEqual(d,{today:0,tomorrow:1,plus7:7,plus8:8,yesterday:-1});
  const rel=await p.locator('[data-radar-relative]').allTextContents();assert.ok(rel.every(t=>/^(?: · )?(?:hoy|mañana|faltan \d+ días)$/.test(t.trim())));
  await p.locator('[data-radar-search]').fill('ALFAGUARA');assert.equal(await visible(p,'[data-radar-item]'),1);
  await p.locator('[data-radar-clear]').click();
  await p.locator('[data-radar-kind]').selectOption('active');assert.equal(await visible(p,'[data-radar-item]'),radarItems.length);
  await p.locator('[data-radar-kind]').selectOption('watch');assert.equal(await visible(p,'[data-radar-item]'),radarWatch.length);
  await p.locator('[data-radar-clear]').click();
  await p.locator('[data-radar-genre]').selectOption('novela');assert.equal(await visible(p,'[data-radar-item]'),radarGenreCount('novela'));
  await p.locator('[data-radar-clear]').click();
  await p.locator('[data-radar-soon]').check();assert.equal(await visible(p,'[data-radar-item]'),soonCount);
  assert.equal(await p.locator('[data-radar-filter-empty]').isVisible(),soonCount===0);
  await p.locator('[data-radar-clear]').click();assert.equal(await visible(p,'[data-radar-item]'),radarAll.length);
  assert.equal(await p.locator('[data-radar-calendar]').getAttribute('href'),'/convocatorias-escritores/deadlines.ics');
  await noOverflow(p,'radar filters');await c.close();
}
for(const route of ['/editoriales/','/convocatorias-escritores/']){
  const[c,p]=await open(route,{js:false});
  assert.equal(await p.locator(route.startsWith('/editoriales')?'[data-editorial-card]':'[data-radar-item]').count(),route.startsWith('/editoriales')?editorialData.length:radarAll.length);
  if(route.includes('convocatorias')){
    const txt=await p.locator('[data-radar-item] time').allTextContents();
    const expectedDates=radarItems.map(item=>item.deadline.split('-').reverse().join('/'));
    assert.ok(expectedDates.every(date=>txt.includes(date)),'no-js: faltan deadlines activos del dataset');
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
console.log(`OK professional resources browser QA (${editorialData.length} editoriales, ${radarItems.length} abiertas, ${radarWatch.length} próximas)`);
