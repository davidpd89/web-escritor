import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const data = JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json','utf8'));
const today = data.generated_for;
const browser = await chromium.launch({headless:true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const context = await browser.newContext();
  await context.addInitScript(value=>{window.__DP_RADAR_TODAY__=value},today);
  const page = await context.newPage();
  assert.equal((await page.goto(ORIGIN+'/convocatorias-escritores/',{waitUntil:'networkidle'})).status(),200);
  const normalize = s=>s.toLocaleLowerCase('es').normalize('NFD').replace(/(?<!n)\u0303|(?<!u)\u0308|[\u0300-\u0302\u0304-\u0307\u0309-\u036f]/g,'').normalize('NFC');
  const dayDiff = x=>(Date.parse(x+'T00:00:00Z')-Date.parse(today+'T00:00:00Z'))/86400000;
  const visible = ()=>page.locator('[data-radar-item]:visible').count();
  const active = [...data.items, ...(data.watchlist || [])];
  // #1009: las opciones «familia:<id>» agrupan etiquetas de data/genre-families.json.
  const families = JSON.parse(fs.readFileSync('data/genre-families.json','utf8')).families;
  const matchesGenre = (x, genre) => {
    const family = genre.startsWith('familia:') && families.find(f => f.id === genre.slice(8));
    const wanted = family ? family.tags.map(normalize) : [normalize(genre)];
    return x.genres.some(g => wanted.includes(normalize(g)));
  };
  for (const type of await page.locator('[data-radar-type] option').evaluateAll(nodes=>nodes.map(x=>x.value).filter(Boolean))) {
    await page.locator('[data-radar-type]').selectOption(type);
    assert.equal(await visible(),active.filter(x=>normalize(x.type)===normalize(type)).length,'tipo '+type);
    await page.locator('[data-radar-clear]').click();
  }
  for (const genre of (await page.locator('[data-radar-genre] option').evaluateAll(nodes=>nodes.map(x=>x.value).filter(Boolean))).filter((v,i,all)=>v.startsWith('familia:')||all.filter(x=>!x.startsWith('familia:')).indexOf(v)<10)) {
    await page.locator('[data-radar-genre]').selectOption(genre);
    await page.locator('[data-radar-soon]').check();
    const expected=active.filter(x=>matchesGenre(x,genre)&&dayDiff(x.deadline)>=0&&dayDiff(x.deadline)<=7).length;
    assert.equal(await visible(),expected,'género y cierre: '+genre);
    assert.equal(await page.locator('[data-radar-filter-empty]').isVisible(),expected===0);
    await page.locator('[data-radar-clear]').click();
  }
  assert.equal(await visible(),data.items.length+(data.watchlist||[]).length);
  await context.close();
} finally {
  await browser.close();
}
console.log('OK: filtros pairwise del radar');
