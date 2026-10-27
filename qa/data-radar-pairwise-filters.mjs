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
  for (const type of await page.locator('[data-radar-type] option').evaluateAll(nodes=>nodes.map(x=>x.value).filter(Boolean))) {
    await page.locator('[data-radar-type]').selectOption(type);
    assert.equal(await visible(),active.filter(x=>normalize(x.type)===normalize(type)).length,'tipo '+type);
    await page.locator('[data-radar-clear]').click();
  }
  for (const genre of (await page.locator('[data-radar-genre] option').evaluateAll(nodes=>nodes.map(x=>x.value).filter(Boolean))).slice(0,10)) {
    await page.locator('[data-radar-genre]').selectOption(genre);
    await page.locator('[data-radar-soon]').check();
    const expected=active.filter(x=>x.genres.some(g=>normalize(g)===normalize(genre))&&dayDiff(x.deadline)>=0&&dayDiff(x.deadline)<=7).length;
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
