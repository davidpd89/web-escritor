import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {execFileSync} from 'node:child_process';

const base=process.env.RECOMMENDATIONS_BASE_URL||'http://127.0.0.1:4173';
const out=process.env.RECOMMENDATIONS_ARTIFACT_DIR||'.ci/reading-v2';
await fs.mkdir(out,{recursive:true});
execFileSync(process.env.PYTHON||'python',['qa/build-reading-scale-fixture.py',`${out}/scale.json`],{stdio:'inherit'});
const fixture=JSON.parse(await fs.readFile(`${out}/scale.json`,'utf8'));
const browser=await chromium.launch({headless:true});
const results=[];
// The newsletter has its own browser suite. Model a visitor who dismissed it
// so scrolling to pagination tests the catalogue rather than a modal overlay.
async function catalogueContext(options={}) {
  const context=await browser.newContext(options);
  await context.addInitScript(()=>localStorage.setItem('nl-popup-ts',String(Date.now())));
  return context;
}
// En móvil (≤900 px) los filtros se pliegan tras «Filtros» (#1004): abrirlos como haría el lector.
const openFilters = async page => { const toggle = page.locator('[data-catalogue-refine-toggle]'); if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click(); };
try {
  for(const count of [100,200]) {
    const context=await catalogueContext({viewport:{width:390,height:900},reducedMotion:'reduce'});
    const page=await context.newPage(), errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.clock.install({time:new Date('2026-10-21T10:00:00Z')});
    await context.route('**/recomendaciones/',r=>r.fulfill({contentType:'text/html',body:fixture.catalogues[count].html}));
    await context.route('**/assets/reading-covers/qa-*',r=>r.fulfill({contentType:'image/png',body:Buffer.from(fixture.cover,'base64')}));
    await context.route('**/assets/reading-market.json',r=>r.fulfill({json:{schema_version:1,offers:[],ratings:[]}}));
    await page.goto(`${base}/recomendaciones/`,{waitUntil:'networkidle'});
    assert.equal(await page.locator('[data-catalogue-book]').count(),count);
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(),24);
    await page.locator('.catalogue-pagination').getByRole('button',{name:'Siguiente →'}).click();
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('pagina'),'2');
    await page.reload({waitUntil:'networkidle'});
    assert.match(await page.locator('[data-catalogue-count]').innerText(),/página 2/);
    await openFilters(page);
    const ms=await page.evaluate(() => {
      const start=performance.now(), field=document.querySelector('[data-filter="q"]');
      field.value='Prueba técnica 099'; field.dispatchEvent(new Event('input',{bubbles:true}));
      return performance.now()-start;
    });
    assert(ms<500,`filter ${count} books took ${ms}ms`);
    assert.equal(await page.locator('[data-catalogue-book]:visible').count(),1);
    assert.match(await page.locator('[data-catalogue-book]:visible h3').innerText(),/099/);
    await page.getByRole('button',{name:'Restablecer',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('[data-filter="q"]').value==='');
    await page.locator('[data-filter="paginas"]').selectOption('breve');
    const pageCounts=await page.locator('[data-catalogue-book]:visible').evaluateAll(es=>es.map(e=>Number(e.dataset.pages)));
    assert(pageCounts.every(n=>n>0&&n<200));
    await page.locator('[data-filter="paginas"]').selectOption('sin-dato');
    assert((await page.locator('[data-catalogue-book]:visible').evaluateAll(es=>es.map(e=>e.dataset.pages))).every(s=>!s));
    await page.getByRole('button',{name:'Restablecer',exact:true}).click();
    await page.locator('.catalogue-quiz>summary').click();
    await page.getByRole('button',{name:'Sí, una novedad',exact:true}).click();
    await page.getByRole('button',{name:'Halloween',exact:true}).click();
    assert.equal(await page.locator('.catalogue-quiz__choices').getByRole('button',{name:'Cocina',exact:true}).count(),0,'Halloween must not offer unrelated cuisine');
    await page.getByRole('button',{name:'← Volver',exact:true}).click();
    assert.match(await page.locator('.catalogue-quiz__panel h2').innerText(),/temporada/);
    await page.getByRole('button',{name:'Halloween',exact:true}).click();
    for(let step=0;step<12;step++) {
      if(await page.getByRole('button',{name:'Ver mis resultados',exact:true}).count()) break;
      assert(!/presupuesto/.test(await page.locator('.catalogue-quiz__panel h2').innerText()),'Skip absent prices');
      assert(await page.locator('.catalogue-quiz__choices button').count()>=2);
      await page.getByRole('button',{name:'Me da igual, continuar',exact:true}).click();
    }
    await page.getByRole('button',{name:'Ver mis resultados',exact:true}).click();
    assert(await page.locator('input[data-facet="temporada"][value="halloween"]').isChecked());
    assert.equal(await page.locator('[data-filter="novedad"]').inputValue(),'15');
    assert(await page.locator('[data-catalogue-book]:visible').count()>0);
    const selected=await page.locator('[data-catalogue-book]:visible').evaluateAll(es=>es.map(e=>({cats:e.dataset.categories,date:e.dataset.published})));
    assert(selected.every(b=>b.cats.split(' ').includes('halloween')));
    await page.reload({waitUntil:'networkidle'});
    assert(await page.locator('input[data-facet="temporada"][value="halloween"]').isChecked());
    assert.deepEqual(errors,[]);
    results.push({books:count,filter_ms:Math.round(ms),quiz_results:selected.length});
    await context.close();
  }
  // Metamorphic facet contract on the existing 100-book generator fixture:
  // OR within groups, AND across group/season, dependent facet counts, empty
  // selections, serialized URL state and reload. The oracle reads source card
  // data independently of the catalogue's filtering implementation.
  {
    const context=await catalogueContext({viewport:{width:1280,height:900}});
    const page=await context.newPage(), errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.clock.install({time:new Date('2026-10-21T10:00:00Z')});
    await context.route('**/recomendaciones/',r=>r.fulfill({contentType:'text/html',body:fixture.catalogues[100].html}));
    await context.route('**/assets/reading-market.json',r=>r.fulfill({json:{schema_version:1,offers:[],ratings:[]}}));
    await page.goto(base+'/recomendaciones/',{waitUntil:'networkidle'});
    const records=await page.locator('[data-catalogue-book]').evaluateAll(cards=>cards.map(card=>({
      id:card.dataset.bookId,group:card.dataset.group,cats:card.dataset.categories.split(' '),search:card.dataset.search
    })));
    assert.equal(records.length,100);
    assert(records.some(r=>r.group==='novela')&&records.some(r=>r.group==='cocina'));
    const expected=(groups=[],seasons=[],query='')=>records.filter(r=>
      (!groups.length||groups.includes(r.group))&&
      (!seasons.length||seasons.some(s=>r.cats.includes(s)))&&
      r.search.toLocaleLowerCase('es').includes(query.toLocaleLowerCase('es'))
    ).map(r=>r.id);
    const verify=async (groups=[],seasons=[],query='')=>{
      const wanted=expected(groups,seasons,query);
      const label=await page.locator('[data-catalogue-count]').innerText();
      const count=Number(label.match(/^(\d+) libros?/)?.[1]);
      assert.equal(count,wanted.length,`Incorrect results for ${JSON.stringify({groups,seasons,query})}: ${label}`);
      const displayed=await page.locator('[data-catalogue-book]:visible').evaluateAll(cards=>cards.map(c=>c.dataset.bookId));
      assert.equal(displayed.length,Math.min(24,wanted.length));
      assert(displayed.every(id=>wanted.includes(id)),'Visible cards must all match independent filter oracle');
      assert.equal(await page.locator('[data-catalogue-empty]').isVisible(),wanted.length===0);
      return wanted.length;
    };
    const set=async (key,value,checked)=>{
      await page.locator(`details[data-facet-group="${key}"]`).evaluate(e=>e.open=true);
      await page.locator(`input[data-facet="${key}"][value="${value}"]`).setChecked(checked);
    };
    assert.equal(await verify(),100);
    await set('grupo','cocina',true); assert.equal(await verify(['cocina']),50);
    // A zero-result option is correctly disabled for new selections. A
    // previously shared URL can still contain that combination and must
    // remain recoverable; do not click an intentionally disabled checkbox.
    assert(await page.locator('input[data-facet="temporada"][value="halloween"]').isDisabled());
    await page.goto(base+'/recomendaciones/#grupo=cocina&temporada=halloween',{waitUntil:'networkidle'});
    assert(await page.locator('input[data-facet="temporada"][value="halloween"]').isChecked());
    assert.equal(await verify(['cocina'],['halloween']),0);
    const cooking=page.locator('input[data-facet="grupo"][value="cocina"]');
    assert(await cooking.isChecked()&&!await cooking.isDisabled(),'Selected zero-result facet stays removable');
    assert.equal(await cooking.locator('xpath=..').locator('[data-facet-count]').innerText(),'(0)');
    assert.equal(await page.locator('input[data-facet="grupo"][value="novela"]').locator('xpath=..').locator('[data-facet-count]').innerText(),'(25)');
    await set('grupo','novela',true); assert.equal(await verify(['cocina','novela'],['halloween']),25);
    await set('grupo','cocina',false); assert.equal(await verify(['novela'],['halloween']),25);
    await set('temporada','halloween',false); assert.equal(await verify(['novela']),50);
    await set('grupo','cocina',true); assert.equal(await verify(['novela','cocina']),100);
    await set('temporada','halloween',true); assert.equal(await verify(['novela','cocina'],['halloween']),25);
    await set('grupo','cocina',false); assert.equal(await verify(['novela'],['halloween']),25);
    await page.locator('[data-filter="q"]').fill('Prueba técnica 000');
    assert.equal(await verify(['novela'],['halloween'],'Prueba técnica 000'),1);
    const hash=new URLSearchParams(new URL(page.url()).hash.slice(1));
    assert.deepEqual(hash.getAll('grupo'),['novela']);
    assert.deepEqual(hash.getAll('temporada'),['halloween']);
    assert.equal(hash.get('q'),'Prueba técnica 000');
    await page.reload({waitUntil:'networkidle'});
    assert(await page.locator('input[data-facet="grupo"][value="novela"]').isChecked());
    assert(await page.locator('input[data-facet="temporada"][value="halloween"]').isChecked());
    assert.equal(await page.locator('[data-filter="q"]').inputValue(),'Prueba técnica 000');
    assert.equal(await verify(['novela'],['halloween'],'Prueba técnica 000'),1);
    assert.deepEqual(errors,[]);
    results.push({area:'facet-metamorphic',books:100,transitions:10,oracle:'card data'});
    await context.close();
  }
  // Civil Madrid dates, including the DST transition, without rebuilding HTML.
  for(const [time,today] of [['2026-10-21T22:30:00Z','2026-10-22'],['2026-10-25T23:30:00Z','2026-10-26']]) {
    const context=await catalogueContext(); const page=await context.newPage();
    await page.clock.install({time:new Date(time)});
    const dates=[0,14,15,16,30].map(days=>new Date(Date.parse(today+'T00:00:00Z')-days*86400000).toISOString().slice(0,10));
    await context.route('**/reading-boundary/',r=>r.fulfill({contentType:'text/html',body:'<main data-reading-catalogue>'+dates.map(date=>'<span class="catalogue-novelty" data-release-label="'+date+'" hidden>Novedad</span>').join('')+'</main><script src="/assets/reading-catalogue.js?v=8"></script>'}));
    await page.goto(base+'/reading-boundary/');
    assert.deepEqual(await page.locator('[data-release-label]').evaluateAll(es=>es.map(e=>e.hidden)),[false,false,true,true,true]);
    await page.clock.fastForward(86400000);
    assert.deepEqual(await page.locator('[data-release-label]').evaluateAll(es=>es.map(e=>e.hidden)),[false,true,true,true,true]);
    await context.close();
  }
  // Actual content: responsive layout, uniform fonts, all cards link externally.
  for(const width of [320,390,768,1024,1440]) {
    const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});
    await page.addInitScript(()=>localStorage.setItem('nl-popup-ts',String(Date.now())));
    await page.clock.install({time:new Date('2026-10-21T10:00:00Z')});
    await page.goto(base+'/recomendaciones/',{waitUntil:'networkidle'});
    await page.evaluate(()=>document.fonts.ready);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`overflow ${width}`);
    const links=await page.locator('.catalogue-card__cover,.catalogue-card h3 a,.catalogue-card__buy').evaluateAll(es=>es.map(e=>({target:e.target,rel:e.rel,href:e.href})));
    assert(links.every(a=>a.target==='_blank'&&a.rel.includes('noopener')));
    const novelty=page.locator('[data-release-label]:not([hidden])');
    if(await novelty.count()) {
      assert((await novelty.first().evaluate(e=>getComputedStyle(e).fontFamily)).includes('CatalogueNovelty'));
      assert(await page.locator('main').evaluate(e=>e.classList.contains('catalogue-fonts-ready')));
    }
    await openFilters(page);
    await page.locator('.catalogue-more-filters>summary').click();
    assert(await page.locator('[data-filter="desde"]').isVisible());
    await page.screenshot({path:`${out}/hub-${width}.png`,fullPage:true});
    await page.goto(base+'/recomendaciones/libros/coraline/',{waitUntil:'networkidle'});
    assert.equal(await page.locator('audio,.catalogue-fragment,[data-catalogue-speak]').count(),0);
    assert(await page.locator('.catalogue-book-layout > div > a.catalogue-buy-link').isVisible());
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.screenshot({path:`${out}/book-${width}.png`,fullPage:true});
    await page.close();
  }
  const staticContext=await catalogueContext({javaScriptEnabled:false});
  const staticPage=await staticContext.newPage(); await staticPage.goto(base+'/recomendaciones/');
  const published=JSON.parse(await fs.readFile('data/reading-catalogue.json','utf8')).libros.filter(b=>b.estado==='publicado').length;
  assert.equal(await staticPage.locator('[data-catalogue-book]:visible').count(),published);
  assert.equal(await staticPage.locator('.catalogue-quiz button').count(),0);
  await staticPage.locator('.catalogue-quiz>summary').click();
  assert.match(await staticPage.locator('.catalogue-quiz__panel').innerText(),/explorar todas las fichas/);
  await staticContext.close();
  const cold=await catalogueContext({viewport:{width:390,height:900}});
  const coldPage=await cold.newPage();
  await coldPage.clock.setFixedTime(new Date('2026-10-21T10:00:00Z'));
  await cold.route('**/yellowtail-normal-400-latin.woff2',route=>route.abort());
  await coldPage.goto(base+'/recomendaciones/',{waitUntil:'networkidle'});
  assert(await coldPage.locator('main').evaluate(el=>el.classList.contains('catalogue-fonts-failed')),'Font failure must preserve a stable visible badge');
  assert(await coldPage.locator('[data-release-label]:not([hidden])').first().isVisible());
  await cold.close();
  await fs.writeFile(`${out}/results.json`,JSON.stringify(results,null,2));
  console.log('PASS catalogue v2: 100/200 books, pagination, page ranges, adaptive quiz, Madrid expiry, 5 viewports, new tabs, fonts and no-JS.');
} finally { await browser.close(); }
