/**
 * Browser gate for research demo. Not wired to GitHub Actions.
 * Start a server at repo root: python -m http.server 4173
 * Execute: node docs/research/catalogo-filtros/qa-demo.mjs
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
const base=process.env.FACET_DEMO_BASE||'http://127.0.0.1:4173';
const path='/docs/research/catalogo-filtros/demo-multifiltro.html';
const browser=await chromium.launch({headless:true});
try {
  for (const width of [320,390,768,1440]) {
    const page=await browser.newPage({viewport:{width,height:900}});
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(base+path,{waitUntil:'networkidle'});
    await page.waitForFunction(()=>{
      const text=document.querySelector('#count')?.textContent||'';
      const hit=text.match(/^(\d+) de (\d+) libros/);
      return hit && Number(hit[1])===Number(hit[2]) && Number(hit[2])>24;
    });
    const total=Number((await page.locator('#count').innerText()).match(/ de (\d+) libros/)[1]);
    assert.equal(await page.locator('#results li').count(),24);
    assert.equal(await page.locator('.choices').count(),3);
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no horizontal overflow '+width);
    await page.getByRole('button',{name:'Siguiente',exact:true}).click();
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('pagina'),'2');
    assert.equal(await page.locator('#results li').count(),Math.min(24,total-24));
    await page.getByRole('button',{name:'Anterior',exact:true}).click();
    assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('pagina'),null);
    async function choose(facetIndex,value) {
      const widget=page.locator('.choices').nth(facetIndex);
      const dropdown=widget.locator('.choices__list--dropdown');
      // En multiselección el menú puede seguir abierto; un segundo clic
      // en .choices__inner lo cerraría, dando un falso fallo del test.
      if (!(await dropdown.isVisible())) await widget.locator('.choices__inner').click();
      // Choices v11.2.4 genera data-value en templates.ts: evita
      // confundir Fantasía con Fantasía juvenil u otras etiquetas.
      await dropdown.locator('[data-choice][data-value="'+value+'"]:not([aria-disabled="true"])').click();
    }
    await choose(0,'tapa-blanda');
    await choose(0,'tapa-dura');
    await page.waitForFunction(()=>{
      const formats=new URLSearchParams(location.hash.slice(1)).getAll('formato');
      return formats.includes('tapa-blanda') && formats.includes('tapa-dura');
    });
    let selected=await page.locator('#formato').evaluate(el=>[...el.selectedOptions].map(o=>o.value).sort());
    assert.deepEqual(selected,['tapa-blanda','tapa-dura']);
    await choose(1,'fantasia');
    await page.waitForFunction(()=>new URLSearchParams(location.hash.slice(1)).getAll('genero').includes('fantasia'));
    selected=await page.locator('#formato').evaluate(el=>[...el.selectedOptions].map(o=>o.value).sort());
    assert.deepEqual(selected,['tapa-blanda','tapa-dura'],'facet change must preserve formats');
    await page.evaluate(()=>{ location.hash='formato=ebook&genero=terror&paginas=breve&precio_max=20'; });
    await page.waitForFunction((expectedTotal)=>{
      const p=new URLSearchParams(location.hash.slice(1));
      return p.get('formato')==='ebook' && p.get('genero')==='terror' && [...document.querySelector('#formato').selectedOptions].some(o=>o.value==='ebook') && document.querySelector('#count').textContent.includes(' de '+expectedTotal+' libros');
    }, total);
    const restored=await page.locator('#formato').evaluate(el=>[...el.selectedOptions].map(o=>o.value));
    assert.deepEqual(restored,['ebook'],'hashchange restores widget state');
    let params=new URLSearchParams(new URL(page.url()).hash.slice(1));
    assert.equal(params.get('paginas'),'breve');
    assert.equal(params.get('precio_max'),'20');
    await page.getByRole('button',{name:'Quitar todos los filtros'}).click();
    params=new URLSearchParams(new URL(page.url()).hash.slice(1));
    assert.deepEqual(params.getAll('formato'),[]);
    assert.equal(params.size,0,'restablecer elimina también precios, páginas y otros filtros no visibles');
    assert.match(await page.locator('#count').innerText(),new RegExp('^'+total+' de '+total+' libros'));
    assert.equal(await page.locator('#results li').count(),24);
    assert.equal(await page.locator('#formato').evaluate(el=>el.selectedOptions.length),0);
    // El laboratorio no puede aplicar filtros sin interfaz para eliminarlos.
    // Estos parámetros sí se conservan, pero las 3 facetas visibles mandan.
    await page.evaluate(()=>new Promise(resolve=>{
      window.addEventListener('hashchange',()=>requestAnimationFrame(resolve),{once:true});
      location.hash='q=LIBRO_INEXISTENTE&grupo=desconocido&temporada=imposible';
    }));
    assert.match(await page.locator('#count').innerText(),new RegExp('^'+total+' de '+total+' libros'));
    await page.evaluate(()=>{ location.hash='formato=no-existe&genero=descatalogado'; });
    await page.waitForFunction(()=>{
      const p=new URLSearchParams(location.hash.slice(1));
      return p.getAll('formato').length===0 && p.getAll('genero').length===0
        && [...document.querySelector('#formato').selectedOptions].length===0;
    });
    assert.match(await page.locator('#count').innerText(),new RegExp('^'+total+' de '+total+' libros'));
    assert.deepEqual(errors,[],'no JS errors '+width);
    await page.close();
  }
  console.log('PASS: Choices UI, multiselect, hashchange, pagination and 4 viewports');
} finally { await browser.close(); }
