import assert from 'node:assert/strict';
import {chromium} from 'playwright';

// Facetas dependientes: en cada estado base (ofertas, precio, extensión…) toda opción activa promete un número de
// libros; al añadirla sola a ese estado, el contador tiene que cumplir la promesa. Antes, con «Ofertas 5 %» el
// Kindle prometía 1226 libros y daba 581, y el audiolibro 198 y daba 0 (descuento contado en otra edición).
const BASE=(process.env.QA_ORIGIN||process.env.SITE_BASE_URL||'http://127.0.0.1:4173').replace(/\/$/,'');
const STATES=(process.env.FACET_STATES||'descuento=5;descuento=25;precio_max=10;precio_min=20&precio_max=30;descuento=10&precio_formato=ebook;paginas=breve;estado=todos&descuento=1').split(';');
const browser=await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH?{executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH}:{})});
const errors=[];
const ready=page=>page.waitForFunction(()=>document.querySelector('[data-reading-catalogue]')?.dataset.catalogueReady==='true',null,{timeout:90000});
const count=async page=>Number.parseInt((await page.locator('[data-catalogue-count]').innerText()).replace(/\./g,''),10)||0;
try {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  await page.addInitScript(()=>{try{localStorage.setItem('nl-popup-ts',String(Date.now()));}catch{}});
  page.on('pageerror',e=>errors.push(e.message));
  let checked=0;
  for (const state of STATES) {
    await page.goto(`${BASE}/recomendaciones/#${state}`,{waitUntil:'networkidle'});
    await page.reload({waitUntil:'networkidle'});
    await ready(page); await page.waitForTimeout(500);
    const options=await page.$$eval('[data-catalogue-filters] input[data-facet]',boxes=>boxes
      .filter(b=>!b.closest('label').hidden&&!b.disabled&&!b.checked&&Number(b.closest('label').dataset.count)>0)
      .map(b=>({facet:b.dataset.facet,value:b.value,count:Number(b.closest('label').dataset.count)})));
    for (const o of options) {
      // Mismo documento: el cambio de hash restaura el estado sin recargar (rápido y es lo que hace el enlace compartido).
      await page.evaluate(h=>{location.hash=h;},`${state}&${o.facet}=${encodeURIComponent(o.value)}`);
      await page.waitForTimeout(60);
      const real=await count(page);
      assert.equal(real,o.count,`estado «${state}» + ${o.facet}=${o.value}: la etiqueta promete ${o.count} y el contador da ${real}`);
      checked++;
    }
    await page.evaluate(h=>{location.hash=h;},state);
  }
  assert.ok(checked>=40,`solo se comprobaron ${checked} opciones`);
  assert.deepEqual(errors,[],'errores de página: '+errors.join(' | '));
  console.log(`PASS catalogue-facet-count-dependent (${STATES.length} estados, ${checked} opciones)`);
} finally { await browser.close(); }
