import assert from 'node:assert/strict';
import {chromium} from 'playwright';

// Cada opción de filtro publicada promete un número de libros en su etiqueta: al elegirla sola,
// el contador, las tarjetas visibles y el enlace compartible tienen que cumplir esa promesa.
const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const route='/recomendaciones/';
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[];
try {
  const page=await browser.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  const response=await page.goto(BASE+route,{waitUntil:'networkidle'});
  assert.equal(response?.status(),200,`${route}: HTTP incorrecto`);
  const options=await page.$$eval('[data-catalogue-filters] input[data-facet]',boxes=>boxes
    .filter(b=>!b.closest('label').hidden&&Number(b.closest('label').dataset.count)>0)
    .map(b=>({facet:b.dataset.facet,value:b.value,count:Number(b.closest('label').dataset.count)})));
  assert.ok(options.length>=20,`${route}: solo ${options.length} opciones de filtro con libros`);
  for (const option of options) {
    await page.goto(BASE+route+'#'+option.facet+'='+encodeURIComponent(option.value),{waitUntil:'networkidle'});
    const result=await page.evaluate(({facet,value})=>{
      const visible=[...document.querySelectorAll('[data-catalogue-book]')].filter(c=>!c.hidden);
      const has=card=>facet==='grupo'?card.dataset.group===value:facet==='formato'?true:card.dataset.categories.split(' ').includes(value);
      const box=document.querySelector(`input[data-facet="${facet}"][value="${CSS.escape(value)}"]`);
      return {status:document.querySelector('[data-catalogue-count]').textContent,visible:visible.length,wrong:visible.filter(c=>!has(c)).map(c=>c.dataset.title),checked:box.checked};
    },option);
    const label=`${option.facet}=${option.value}`;
    assert.ok(result.checked,`${label}: el enlace no marca la opción`);
    assert.equal(Number.parseInt(result.status,10),option.count,`${label}: la etiqueta promete ${option.count} y el contador dice «${result.status}»`);
    assert.ok(result.visible>0&&result.visible<=option.count,`${label}: ${result.visible} tarjetas visibles para ${option.count}`);
    assert.deepEqual(result.wrong,[],`${label}: tarjetas que no cumplen el filtro`);
  }
  await page.goto(BASE+route,{waitUntil:'networkidle'});
  const first=options.find(o=>o.facet==='edad')||options[0];
  const box=page.locator(`[data-catalogue-filters] input[data-facet="${first.facet}"][value="${first.value}"]`);
  await box.evaluate(b=>{const d=b.closest('details'); if (d) d.open=true;});
  await box.check({force:true});
  await page.waitForFunction(({facet,value})=>new URLSearchParams(location.hash.slice(1)).getAll(facet).includes(value),first);
  await page.fill('[data-catalogue-filters] [data-filter="q"]','zzqxwyv');
  await page.waitForFunction(()=>!document.querySelector('[data-catalogue-empty]').hidden&&document.querySelector('[data-catalogue-count]').textContent.startsWith('0'));
  assert.deepEqual(errors,[],`${route}: errores de JavaScript`);
  console.log(`PASS catalogue-facet-count-parity (${options.length} opciones)`);
} finally {await browser.close();}
