import assert from 'node:assert/strict';
import {chromium} from 'playwright';

// Matriz de filtros del catálogo real (David, 09/11: «tests de cada opción y combinación»).
// Cada opción de cada control, y combinaciones de dos y tres, se comprueban contra una reimplementación
// independiente de las reglas leída de los data-* de las fichas: el recuento anunciado tiene que coincidir con los
// libros que cumplen, ninguna ficha visible puede incumplir, añadir un filtro nunca suma libros, cada filtro activo
// tiene su etiqueta con × y «Eliminar todos» deja el catálogo como al cargar.
const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[];
try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.addInitScript(()=>localStorage.setItem('nl-popup-ts',String(Date.now())));
  page.on('pageerror',e=>errors.push(e.message));
  assert.equal((await page.goto(BASE+'/recomendaciones/',{waitUntil:'networkidle'}))?.status(),200);
  await page.waitForFunction(()=>{const root=document.querySelector('[data-reading-catalogue]');if(root?.dataset.catalogueReady)return true;window.dispatchEvent(new HashChangeEvent('hashchange'));return false;},null,{timeout:120000,polling:500});
  await page.waitForFunction(()=>!document.querySelector('[data-reading-catalogue]').dataset.facetsPending,null,{timeout:60000});
  // Orden lógico de los controles: tipo → género → edad → formato → precio → extensión → fechas → ofertas.
  const order=await page.$$eval('[data-catalogue-filters] [data-facet-group], [data-catalogue-filters] [data-filter]',els=>els.map(e=>e.dataset.facetGroup||e.dataset.filter));
  const at=k=>order.indexOf(k);
  for (const [a,b] of [['grupo','genero'],['genero','edad'],['edad','formato'],['formato','precio_min'],['precio_min','paginas'],['paginas','desde'],['desde','hasta'],['hasta','descuento']]) assert.ok(at(a)>=0&&at(a)<at(b),`orden de filtros: ${a} debe ir antes que ${b} (${order.join(' ')})`);
  assert.equal(await page.locator('[data-filter="novedad"], .catalogue-more-filters').count(),0,'«Novedades» y «Más filtros» ya no existen');

  const scenarios=await page.evaluate(()=>{
    const pick=(sel)=>[...document.querySelectorAll(sel)];
    const boxes=pick('[data-catalogue-filters] input[data-facet]').filter(b=>!b.closest('label').hidden&&Number(b.closest('label').dataset.count)>0);
    const byFacet={};for(const b of boxes)(byFacet[b.dataset.facet]??=[]).push(b.value);
    const opts=k=>pick(`[data-filter="${k}"] option`).map(o=>o.value).filter(Boolean);
    const today=new Date().toISOString().slice(0,10), ago=d=>new Date(Date.now()-d*864e5).toISOString().slice(0,10), ahead=d=>new Date(Date.now()+d*864e5).toISOString().slice(0,10);
    const single=[];
    for(const [k,vs] of Object.entries(byFacet)) for(const v of vs) single.push({estado:'todos',[k]:[v]});
    for(const v of opts('paginas')) single.push({paginas:v},{estado:'todos',paginas:v});
    for(const v of opts('estado')) single.push({estado:v});
    for(const v of opts('descuento')) single.push({descuento:v});
    single.push({desde:ago(30)},{hasta:ago(365)},{desde:ago(400),hasta:ago(30)},{estado:'proximos',desde:today,hasta:ahead(60)},{estado:'todos',desde:ago(7),hasta:ahead(7)});
    single.push({precio_max:'10'},{precio_min:'20'},{precio_min:'10',precio_max:'15'});
    for(const f of opts('precio_formato')) single.push({precio_formato:f,precio_max:'12'});
    const combos=[];
    const firsts=Object.fromEntries(Object.entries(byFacet).map(([k,vs])=>[k,vs.slice(0,3)]));
    const facets=Object.keys(firsts);
    for(let i=0;i<facets.length;i++)for(let j=i+1;j<facets.length;j++)for(const a of firsts[facets[i]])for(const b of firsts[facets[j]].slice(0,2))combos.push({estado:'todos',[facets[i]]:[a],[facets[j]]:[b]});
    for(const k of facets)if(firsts[k].length>1)combos.push({estado:'todos',[k]:firsts[k].slice(0,2)}); // dentro de una faceta: O
    for(const p of opts('paginas'))for(const k of facets)combos.push({estado:'todos',paginas:p,[k]:[firsts[k][0]]});
    for(const k of facets)combos.push({precio_max:'15',desde:ago(365),[k]:[firsts[k][0]]},{descuento:'5',[k]:[firsts[k][0]]});
    combos.push({estado:'proximos',paginas:'media',precio_max:'25'},{descuento:'10',paginas:'larga',desde:ago(720)});
    return {single,combos,facets};
  });
  assert.ok(scenarios.single.length>=40,`solo ${scenarios.single.length} opciones`);

  const run=state=>page.evaluate(state=>{
    const root=document.querySelector('[data-reading-catalogue]'), form=document.querySelector('[data-catalogue-filters]');
    const fields=[...document.querySelectorAll('[data-filter]')].filter(f=>f.form===form||form.contains(f)||f.getAttribute('form')===form.id);
    for(const f of fields) if(f.dataset.filter!=='orden') f.value='';
    for(const b of form.querySelectorAll('input[data-facet]')) b.checked=false;
    for(const [k,v] of Object.entries(state)){
      if(Array.isArray(v)) for(const x of v) form.querySelector(`input[data-facet="${k}"][value="${CSS.escape(x)}"]`).checked=true;
      else document.querySelector(`[data-filter="${k}"]`).value=v;
    }
    document.querySelector('[data-filter="q"]').dispatchEvent(new Event('input',{bubbles:true}));
    // Reglas independientes, solo con los data-* publicados. Sin «precio en», el precio se mira en los formatos marcados.
    const today=new Date().toISOString().slice(0,10);
    const bounds=c=>{const p=c.dataset.published,m=c.dataset.publishedMonth,y=c.dataset.year;
      if(p)return[p,p];if(m){const e=new Date(Date.UTC(+m.slice(0,4),+m.slice(5,7),0)).toISOString().slice(0,10);return[m+'-01',e];}if(y)return[y+'-01-01',y+'-12-31'];return['',''];};
    const range=c=>{const n=Number(c.dataset.pages);return !n?'':n<200?'breve':n<400?'media':n<600?'larga':'muy-larga';};
    const prices=c=>(c.dataset.formatPrices||'').split(' ').filter(Boolean).map(x=>x.split(':')).map(([f,v])=>[f,Number(v)]);
    const ok=c=>{
      const [lo,up]=bounds(c);
      if(state.estado==='proximos'?!(lo&&lo>today):state.estado!=='todos'&&lo&&lo>today)return false;
      if(state.desde&&!(up&&up>=state.desde))return false;
      if(state.hasta&&!(lo&&lo<=state.hasta))return false;
      if(state.paginas&&range(c)!==state.paginas)return false;
      if(state.precio_min||state.precio_max){const min=state.precio_min?Math.round(state.precio_min*100):0,max=state.precio_max?Math.round(state.precio_max*100):Infinity;
        if(!prices(c).some(([f,v])=>(state.precio_formato?f===state.precio_formato:!state.formato||state.formato.includes(f))&&v>=min&&v<=max))return false;}
      for(const k of ['grupo','genero','edad','formato']){const want=state[k];if(!want)continue;
        const have=k==='grupo'?[c.dataset.group]:k==='formato'?(c.dataset.formats||'').split(' '):(c.dataset.categories||'').split(' ');
        if(!want.some(w=>have.includes(w)))return false;}
      return true;
    };
    // El día de hoy y los descuentos (precios del día en el navegador) quedan fuera de la comprobación estricta.
    const edge=c=>bounds(c)[0]===today;
    const cards=[...root.querySelectorAll('[data-catalogue-book]')];
    const expected=cards.filter(ok), visible=cards.filter(c=>!c.hidden);
    const announced=Number((root.querySelector('[data-catalogue-count]').textContent.match(/\d+/)||[0])[0]);
    const chips=root.querySelectorAll('.catalogue-chip').length;
    const active=Object.entries(state).filter(([k,v])=>!(k==='precio_formato'&&!state.precio_min&&!state.precio_max)).reduce((n,[k,v])=>n+(Array.isArray(v)?v.length:v?1:0),0);
    return {announced,expected:expected.length,edges:cards.filter(edge).length,wrong:visible.filter(c=>!ok(c)&&!edge(c)).map(c=>c.dataset.title).slice(0,3),
      // Las fichas traídas por la hidratación se rellenan al mostrarse: ninguna visible puede quedar vacía ni con «Novedad» desfasada.
      hollow:visible.filter(c=>!c.querySelector('img.catalogue-book-cover')||!c.querySelector('.catalogue-card__ficha')).map(c=>c.dataset.title).slice(0,3),
      badNovelty:visible.filter(c=>{const l=c.querySelector('[data-release-label]');if(!l||l.dataset.releaseFallback!==undefined)return false;const d=(Date.parse(today)-Date.parse(l.dataset.releaseLabel))/864e5;return l.hidden===((d>=0&&d<=30)||d<0);}).map(c=>c.dataset.title).slice(0,3),
      chips,active,clearShown:!root.querySelector('[data-catalogue-clear]').hidden,overflow:document.documentElement.scrollWidth>innerWidth+1};
  },state);

  const baseline=await run({});
  assert.equal(baseline.chips,0); assert.equal(baseline.clearShown,false);
  let checked=0;
  const verify=async(state,parentCount)=>{
    const r=await run(state), label=JSON.stringify(state);
    assert.deepEqual(r.wrong,[],`${label}: fichas visibles que no cumplen`);
    assert.deepEqual(r.hollow,[],`${label}: fichas visibles sin contenido`);
    assert.deepEqual(r.badNovelty,[],`${label}: etiqueta Novedad/Próximamente desfasada`);
    if(!state.descuento) assert.ok(Math.abs(r.announced-r.expected)<=r.edges,`${label}: anuncia ${r.announced}, cumplen ${r.expected}`);
    if(parentCount!=null) assert.ok(r.announced<=parentCount,`${label}: un filtro más no puede sumar libros (${r.announced} > ${parentCount})`);
    // «Publicado y próximos» también es un filtro con etiqueta; «Ya publicados» (por defecto) no.
    assert.equal(r.chips,r.active,`${label}: ${r.chips} etiquetas para ${r.active} filtros`);
    assert.equal(r.clearShown,r.active>0,`${label}: «Eliminar filtros» debe verse solo con filtros`);
    assert.equal(r.overflow,false,`${label}: desborde horizontal`);
    checked++;
    return r.announced;
  };
  const all=(await run({estado:'todos'})).announced;
  for(const s of scenarios.single) await verify(s);
  for(const s of scenarios.combos) await verify(s);
  // Monotonía: cada filtro añadido sobre otro nunca suma.
  for(const k of scenarios.facets){const s={estado:'todos'};const a=await verify(s,all);s.paginas='media';const b=await verify({...s},a);await verify({...s,precio_max:'15'},b);}
  const steps=['1','5','10','25','50'];let prev=all;for(const d of steps)prev=await verify({estado:'todos',descuento:d},prev);
  // «Eliminar todos» deja el catálogo como al cargar.
  await run({estado:'todos',paginas:'media',precio_max:'20',[scenarios.facets[0]]:[]});
  await page.getByRole('button',{name:'Eliminar todos',exact:true}).click();
  const reset=await page.evaluate(()=>{const root=document.querySelector('[data-reading-catalogue]');
    return {announced:Number((root.querySelector('[data-catalogue-count]').textContent.match(/\d+/)||[0])[0]),chips:root.querySelectorAll('.catalogue-chip').length,
      dirty:[...document.querySelectorAll('[data-catalogue-filters] input[data-facet]:checked')].length+[...document.querySelectorAll('[data-filter]')].filter(f=>f.dataset.filter!=='orden'&&f.value).length};});
  assert.deepEqual(reset,{announced:baseline.announced,chips:0,dirty:0},'«Eliminar todos» no dejó el catálogo como al cargar');
  assert.deepEqual(errors,[],'errores de JavaScript');
  console.log(`PASS matriz de filtros: ${checked} combinaciones (${scenarios.single.length} opciones sueltas), orden lógico, etiquetas y «Eliminar todos».`);
} finally { await browser.close(); }
