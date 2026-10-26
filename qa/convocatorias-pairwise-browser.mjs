import assert from 'node:assert/strict';
import fs from 'node:fs';
import {chromium} from 'playwright';

const origin=process.env.QA_ORIGIN||'http://127.0.0.1:4173';
const data=JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json','utf8'));
const records=[...data.items.map(x=>({...x,kind:'active'})),...data.watchlist.map(x=>({...x,kind:'watch'})),...data.expired.map(x=>({...x,kind:'expired'}))];
const types=[...new Set(records.map(x=>x.type))].sort();
const genres=[...new Set(records.flatMap(x=>x.genres))].sort();
const dimensions=[['type',['',...types.slice(0,2)]],['genre',['',...genres.slice(0,2)]],['kind',['','active','watch']],['soon',[false,true]],['expired',[false,true]],['query',['','zzzz_ninguna_convocatoria_987654']]];
const product=dimensions.reduce((rows,[name,values])=>rows.flatMap(row=>values.map(value=>({...row,[name]:value}))),[{}]);
const pairs=row=>{const result=[];for(let i=0;i<dimensions.length;i++)for(let j=i+1;j<dimensions.length;j++){const a=dimensions[i][0],b=dimensions[j][0];result.push(JSON.stringify([a,row[a],b,row[b]]));}return result;};
const uncovered=new Set(product.flatMap(pairs));
const cases=[];
while(uncovered.size){let best=null,score=-1;for(const row of product){const n=pairs(row).filter(x=>uncovered.has(x)).length;if(n>score){best=row;score=n;}}assert.ok(score>0);cases.push(best);for(const pair of pairs(best))uncovered.delete(pair);}
const dayGap=value=>Math.round((Date.parse(value+'T00:00:00Z')-Date.parse(data.generated_for+'T00:00:00Z'))/86400000);
const model=c=>records.filter(x=>(x.kind!=='expired'||c.expired)&&(!c.type||x.type===c.type)&&(!c.genre||x.genres.includes(c.genre))&&(!c.kind||x.kind===c.kind)&&(!c.soon||(x.kind==='active'&&dayGap(x.deadline)>=0&&dayGap(x.deadline)<=7))&&(!c.query)).map(x=>x.title.toLocaleLowerCase('es')).sort();
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
try{const context=await browser.newContext({reducedMotion:'reduce'});await context.addInitScript(today=>{window.__DP_RADAR_TODAY__=today;localStorage.setItem('nl-popup-ts',String(Date.now()));},data.generated_for);const page=await context.newPage();const response=await page.goto(origin+'/convocatorias-escritores/',{waitUntil:'networkidle'});assert.equal(response.status(),200);
for(const [index,c] of cases.entries()){await page.locator('[data-radar-search]').fill(c.query);await page.locator('[data-radar-type]').selectOption(c.type);await page.locator('[data-radar-genre]').selectOption(c.genre);await page.locator('select[data-radar-kind]').selectOption(c.kind);await page.locator('[data-radar-soon]').setChecked(c.soon);await page.locator('[data-radar-expired]').setChecked(c.expired);const actual=(await page.locator('[data-radar-item]:visible').evaluateAll(nodes=>nodes.map(x=>x.dataset.title))).sort();const expected=model(c);assert.deepEqual(actual,expected,'pairwise '+index+': '+JSON.stringify(c));assert.equal(await page.locator('[data-radar-filter-empty]').isVisible(),expected.length===0);assert.equal((await page.locator('[data-radar-count]').textContent()).trim(),expected.length+' '+(expected.length===1?'convocatoria visible':'convocatorias visibles'));}
await context.close();console.log('PASS pairwise: '+cases.length+' escenarios, '+product.length+' combinaciones candidatas');}finally{await browser.close();}