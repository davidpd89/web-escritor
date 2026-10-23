// Real cross-document journeys, including Back/Forward and restored menus.
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import {createServer} from 'node:http';
import {execFileSync} from 'node:child_process';

const root=process.cwd(),out=process.env.QA_ARTIFACT_DIR||'.ci/navigation-roundtrips';
fs.mkdirSync(out,{recursive:true});
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const registry=new Map(read('data/content-registry.json').entries.map(e=>[e.id,e]));
const nav=read('data/navigation.json');
const menu=nav.menu['recommendations-hub'].map(item=>({label:item.label,href:registry.get(item.targetId).url}));
const footer=[...new Set([...nav.menu['recommendations-hub'].map(item=>item.targetId),'reading-index-editoriales'])].map(id=>({label:registry.get(id).label,href:registry.get(id).url}));
const books=read('data/reading-catalogue.json').libros.filter(b=>b.estado==='publicado'&&b.isbn13);
const book=books.find(b=>b.id.startsWith('isbn-'))||books[0];
assert(book,'A real published ISBN is required for these journeys.');
const authors=read('data/reading-authors.json').autores;
const author=authors.find(a=>book.autores.includes(a.nombre))||authors[0];
assert(book&&author,'Real book and author are required for the representative journeys.');
const sources=['/cuaderno/','/recomendaciones/','/recomendaciones/autores/','/recomendaciones/editoriales/',`/recomendaciones/libros/${book.slug}/`,`/recomendaciones/autores/${author.slug}/`];
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.woff2':'font/woff2','.webp':'image/webp','.avif':'image/avif','.png':'image/png','.jpg':'image/jpeg','.ico':'image/x-icon','.xml':'application/xml','.webmanifest':'application/manifest+json'};
const server=createServer((req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    let file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
    if(file!==root&&!file.startsWith(root+path.sep))throw new Error('Outside checkout');
    if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
    if(!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end('Not found');return;}
    res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});
    res.end(fs.readFileSync(file));
  }catch{res.writeHead(400);res.end('Bad request');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
const sha=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
const browser=await chromium.launch({headless:true});
const results=[];
const plan=[];
for(const width of [390,1280])for(const source of(width<768?sources:['/',...sources]))for(const target of(source==='/'?menu:footer)){
  if(source!==target.href)plan.push({width,source,target});
}
const norm=text=>text.replace(/\s+/g,' ').trim();
const submenu='#masthead-submenu-recommendations-hub';
const trigger='[aria-controls="masthead-submenu-recommendations-hub"]';

function saveResults(){
  fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({sha,planned:plan.length,completed:results.length,coverageComplete:results.length===plan.length,results},null,2)+'\n');
  fs.writeFileSync(path.join(out,'report.md'),['# Navigation round trips','',`Source commit: ${sha}`,`Journeys completed: ${results.length}/${plan.length}`,'',...results.map(r=>`- **${r.status.toUpperCase()}** ${r.width}px ${r.source} → ${r.target} (${r.surface})${r.phase?' / '+r.phase+': '+r.error.split('\n')[0]:''}`),''].join('\n'));
}

async function loaded(page){
  await page.waitForLoadState('networkidle');
  assert(norm(await page.locator('main h1').first().innerText()),'Destination must have a readable main heading');
}
async function catalogueState(page){
  return page.evaluate(()=>({q:document.querySelector('[data-filter="q"]')?.value,order:document.querySelector('[data-filter="orden"]')?.value,visible:[...document.querySelectorAll('[data-catalogue-book]')].filter(e=>!e.hidden).map(e=>e.dataset.bookId)}));
}
async function openSubmenu(page){
  const button=page.locator(trigger).first();
  if(await button.getAttribute('aria-expanded')==='true'){await button.focus();await page.keyboard.press('Escape');}
  await button.click();
  assert.equal(await button.getAttribute('aria-expanded'),'true','Submenu opens after one real click');
  assert(await page.locator(submenu).isVisible(),'Submenu links are visible');
}

async function journey(width,source,target){
  // Only Home has the masthead. Interior templates use the shared footer/Explore.
  const surface=source==='/'&&width>=768?'masthead':'footer';
  const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce',serviceWorkers:'block'});
  await context.route('**/*',route=>new URL(route.request().url()).origin===origin?route.continue():route.abort());
  await context.addInitScript(()=>{sessionStorage.setItem('dp-intro-seen','1');localStorage.setItem('nl-popup-ts',String(Date.now()));});
  const page=await context.newPage();page.setDefaultTimeout(8000);page.setDefaultNavigationTimeout(20000);
  const errors=[],badDocuments=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('response',response=>{if(response.request().isNavigationRequest()&&response.status()>=400)badDocuments.push({url:response.url(),status:response.status()});});
  const result={width,source,target:target.href,surface,status:'pass'};
  let phase='initial document';
  try{
    await page.goto(origin+source+'?utm_source=navigation-qa');await loaded(page);
    let selectedState;
    if(source==='/recomendaciones/'){
      await page.waitForFunction(()=>document.querySelector('[data-catalogue-filters] fieldset')?.disabled===false);
      await page.locator('[data-filter="q"]').fill(book.isbn13);
      await page.locator('[data-filter="orden"]').selectOption('titulo_desc');
      selectedState=await catalogueState(page);
      assert.deepEqual(selectedState.visible,[book.id],'Initial search is exercised on a real book');
    }
    const before=page.url();
    phase='menu and link';
    let link;
    if(surface==='masthead'){
      await openSubmenu(page);
      const actual=await page.locator(submenu+' a').evaluateAll(es=>es.map(e=>({href:e.getAttribute('href'),label:e.textContent.replace(/\s+/g,' ').trim()})));
      assert.deepEqual(actual,menu,'Live menu matches the shared navigation registry on this template');
      link=page.locator(`${submenu} a[href="${target.href}"]`);
    }else{
      link=page.locator(`footer.site-footer a[href="${target.href}"]`).first();
    }
    assert.equal(await link.count(),1,'The intended navigation entry exists');
    result.linkText=norm(await link.innerText());assert(result.linkText,'Link must have a readable label');
    await link.click();await loaded(page);
    phase='destination';
    assert.equal(new URL(page.url()).pathname,target.href,'Click reaches the intended document');
    result.heading=norm(await page.locator('main h1').first().innerText());
    phase='back';
    await page.goBack();await loaded(page);
    assert.equal(page.url(),before,'Back restores the original URL, including filters and source');
    if(selectedState)assert.deepEqual(await catalogueState(page),selectedState,'Back restores catalogue controls and results');
    phase='forward';
    await page.goForward();await loaded(page);
    assert.equal(new URL(page.url()).pathname,target.href,'Forward returns to the intended destination');
    phase='second back';
    await page.goBack();await loaded(page);
    assert.equal(page.url(),before,'Repeated Back still restores the source');
    if(selectedState)assert.deepEqual(await catalogueState(page),selectedState,'Repeated Back keeps selected filters');
    phase='menu recovery after history';
    await page.evaluate(()=>scrollTo(0,0));
    if(surface==='masthead'){
      await openSubmenu(page);await page.keyboard.press('Escape');
      assert.equal(await page.locator(trigger).first().getAttribute('aria-expanded'),'false','Restored menu closes with Escape');
    }
    const opener=page.locator('[data-explore-open]').first();
    await opener.click();
    await page.waitForFunction(()=>document.querySelector('[data-explore-dialog]')?.open);
    await page.keyboard.press('Escape');
    await page.waitForFunction(()=>!document.querySelector('[data-explore-dialog]')?.open);
    assert(await opener.evaluate(e=>e===document.activeElement),'Restored menu returns focus to its opener');
    assert.deepEqual(badDocuments,[],'No HTTP error on a document in the journey');
    assert.deepEqual(errors,[],'No uncaught first-party errors during navigation/history');
  }catch(error){
    result.status='fail';result.phase=phase;result.error=error.stack||String(error);
    result.url=page.url();result.pageErrors=errors;result.badDocuments=badDocuments;
    result.controls=await page.locator('[data-filter]').evaluateAll(es=>es.map(e=>({name:e.dataset.filter,value:e.value}))).catch(()=>[]);
    const name=`${width}-${results.length}.png`;result.screenshot=name;
    await page.screenshot({path:path.join(out,name),fullPage:true}).catch(()=>{});
  }finally{await context.close();}
  results.push(result);
  saveResults();
  console.log(`${result.status.toUpperCase()} ${width} ${source} -> ${target.href}${result.phase?' ['+result.phase+'] '+result.error.split('\n')[0]:''}`);
}
try{
  for(const item of plan)await journey(item.width,item.source,item.target);
}finally{
  await browser.close();await new Promise(resolve=>server.close(resolve));
  saveResults();
}
assert(plan.length>0,'No journeys planned');
assert.equal(results.length,plan.length,'Every planned journey must have a result');
assert.equal(results.filter(r=>r.status==='fail').length,0,`See ${out}/results.json and screenshots for reproduction.`);
