import assert from 'node:assert/strict';
import {chromium} from 'playwright';

const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true});
const snapshot=page=>page.evaluate(()=>[...document.querySelectorAll('[data-catalogue-book]')].filter(c=>!c.hidden).map(c=>({id:c.dataset.bookId,cover:c.querySelector('img')?.getAttribute('src')||''})));
try {
  const context=await browser.newContext();
  const first=await context.newPage();
  await first.goto(BASE+route,{waitUntil:'domcontentloaded'});
  await first.waitForFunction(()=>document.querySelector('[data-catalogue-pagination] button:not([disabled])'));
  const initial=await snapshot(first);
  const next=first.locator('[data-catalogue-pagination] button').filter({hasText:'Siguiente'});
  await next.click();
  await first.waitForFunction(()=>new URLSearchParams(location.hash.slice(1)).get('pagina')==='2');
  const expected=await snapshot(first);
  assert.ok(expected.length>0,`${route}: segunda página vacía`);
  assert.ok(expected.every(x=>x.id&&x.cover),`${route}: segunda página con identificadores o portadas ausentes`);
  assert.ok(!expected.some(x=>initial.some(y=>y.id===x.id)),`${route}: libros repetidos entre páginas`);
  const shared=first.url();
  const second=await context.newPage();
  await second.goto(shared,{waitUntil:'domcontentloaded'});
  await second.waitForFunction(()=>document.querySelector('[data-catalogue-pagination]')?.textContent?.includes('Página 2'));
  assert.deepEqual(await snapshot(second),expected,`${route}: URL ${shared} no recupera las mismas cubiertas`);

  // Páginas fuera de rango: la URL debe quedar igual que la vista (página limitada), sin historial nuevo.
  const state=page=>page.evaluate(()=>({pagina:new URLSearchParams(location.hash.slice(1)).get('pagina'),hash:location.hash,count:document.querySelector('[data-catalogue-count]')?.textContent||'',nav:document.querySelector('[data-catalogue-pagination]')?.textContent||'',length:history.length}));
  const pageCount=async page=>{const m=(await state(page)).count.match(/página (\d+) de (\d+)/);return m?Number(m[2]):1;};
  const open=async hash=>{const page=await context.newPage();await page.goto(BASE+route+hash,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>/libros?/.test(document.querySelector('[data-catalogue-count]')?.textContent||''));return page;};
  const total=await pageCount(second);
  assert.ok(total>=3,`${route}: se esperaban al menos 3 páginas para probar la normalización (hay ${total})`);
  for (const [hash,expected] of [['#pagina=99',String(total)],['#pagina=100000',String(total)],[`#pagina=${total}`,String(total)],['#pagina=2','2'],['#pagina=1',null],['#pagina=0',null],['#pagina=-3',null],['#pagina=abc',null],['#pagina=',null]]) {
    const page=await open(hash);
    const s=await state(page);
    assert.equal(s.pagina,expected,`${route}${hash}: la URL dice pagina=${s.pagina} y la vista muestra «${s.count}»`);
    assert.ok(s.nav.includes(`Página ${expected||1} de ${total}`),`${route}${hash}: paginación «${s.nav}» no coincide con la URL`);
    const before=await snapshot(page);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>/libros?/.test(document.querySelector('[data-catalogue-count]')?.textContent||''));
    assert.deepEqual(await snapshot(page),before,`${route}${hash}: recargar la URL normalizada no reproduce la vista`);
    await page.close();
  }

  // Filtros múltiples: se conservan y la página se limita a las coincidencias filtradas.
  const facet=await second.evaluate(()=>{const boxes=[...document.querySelectorAll('input[data-facet]')];const by={};for(const b of boxes)(by[b.dataset.facet]??=[]).push(b.value);const [k,vals]=Object.entries(by).find(([,v])=>v.length>=2)||[];return k?{k,vals:vals.slice(0,2)}:null;});
  assert.ok(facet,`${route}: no hay una faceta con dos valores para probar filtros múltiples`);
  const filtered=await open(`#${facet.k}=${encodeURIComponent(facet.vals[0])}&${facet.k}=${encodeURIComponent(facet.vals[1])}&pagina=99`);
  const fs=await state(filtered), fp=await pageCount(filtered), fhash=new URLSearchParams(fs.hash.slice(1));
  assert.deepEqual(fhash.getAll(facet.k),facet.vals,`${route}: la normalización perdió filtros repetidos (${fs.hash})`);
  assert.equal(fs.pagina,fp>1?String(fp):null,`${route}: con filtros, pagina=${fs.pagina} y la vista «${fs.count}»`);
  await filtered.close();

  // Cero resultados: sin página en la URL, búsqueda conservada.
  const empty=await open('#q=zzqxjw-sin-resultados&pagina=5');
  const es=await state(empty);
  assert.equal(es.pagina,null,`${route}: cero resultados con pagina=${es.pagina}`);
  assert.equal(new URLSearchParams(es.hash.slice(1)).get('q'),'zzqxjw-sin-resultados',`${route}: se perdió la búsqueda (${es.hash})`);
  assert.equal(await empty.locator('[data-catalogue-empty]').isVisible(),true,`${route}: sin aviso de catálogo vacío`);
  await empty.close();

  // Hash cambiado en la misma página: una sola entrada de historial, sin bucles, y Atrás vuelve.
  const nav=await open('');
  const length=(await state(nav)).length;
  await nav.evaluate(()=>{location.hash='#pagina=99';});
  await nav.waitForFunction(t=>new URLSearchParams(location.hash.slice(1)).get('pagina')===t,String(total));
  await nav.waitForTimeout(300);
  const ns=await state(nav);
  assert.equal(ns.length,length+1,`${route}: la normalización añadió entradas al historial (${length} → ${ns.length})`);
  assert.equal(ns.pagina,String(total));
  await nav.goBack();
  await nav.waitForFunction(()=>!location.hash);
  await nav.waitForFunction(()=>document.querySelector('[data-catalogue-pagination]')?.textContent?.includes('Página 1 de'));
  await nav.close();
  await context.close();
} finally {await browser.close();}
console.log('PASS catalogue-pagination-shareable-url');