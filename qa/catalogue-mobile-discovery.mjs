import assert from 'node:assert/strict';
import { chromium } from 'playwright';

// Descubrimiento móvil del catálogo (#1004): en ≤900 px la búsqueda queda a la vista y el
// resto de filtros se pliega tras «Filtros», para que la primera tarjeta aparezca tras un
// scroll corto. En main, a 390×844 la primera tarjeta empezaba a 1.985 px tras 1.228 px de filtros.
const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const url = `${origin}/recomendaciones/`;
const CARD_BUDGET = 1000; // px desde el inicio a 390×844 (presupuesto del encargo)
const browser = await chromium.launch({ headless: true });

async function open(width, options = {}) {
  const context = await browser.newContext({ viewport: { width, height: 844 }, reducedMotion: 'reduce', ...options });
  await context.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  const page = await context.newPage();
  await page.goto(options.hash ? url + options.hash : url, { waitUntil: 'load' });
  return { context, page };
}
const top = (page, selector) => page.locator(selector).first().evaluate(e => Math.round(e.getBoundingClientRect().top + scrollY));

try {
  for (const width of [320, 390, 768]) {
    const { context, page } = await open(width);
    const card = await top(page, '.catalogue-card:not([hidden])');
    assert.ok(card <= CARD_BUDGET, `${width}px: la primera tarjeta empieza a ${card} px (presupuesto ${CARD_BUDGET})`);
    const search = page.locator('[data-filter="q"]');
    assert.equal(await search.isVisible(), true, `${width}px: la búsqueda no está a la vista`);
    assert.ok(await top(page, '[data-filter="q"]') < 844, `${width}px: la búsqueda queda fuera de la primera pantalla`);
    const toggle = page.locator('[data-catalogue-refine-toggle]');
    assert.equal(await toggle.isVisible(), true, `${width}px: falta el acceso a Filtros`);
    assert.equal(await toggle.isEnabled(), true, `${width}px: Filtros sigue deshabilitado con JS`);
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    assert.equal(await page.locator('[data-catalogue-refine]').isVisible(), false, `${width}px: los filtros no se pliegan`);
    assert.equal(await page.locator('[data-filter="orden"]').isVisible(), true, `${width}px: el orden no está accesible`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 0, `${width}px: scroll horizontal de ${overflow} px`);
    console.log(`${width}px: primera tarjeta a ${card} px`);
    await context.close();
  }

  // Recorrido de teclado a 390 px: abrir, filtrar, Escape, restablecer.
  {
    const { context, page } = await open(390);
    const toggle = page.locator('[data-catalogue-refine-toggle]');
    const count = page.locator('[data-catalogue-count]');
    const total = await count.innerText();
    const searchTop = await top(page, '[data-filter="q"]');
    await toggle.focus();
    await page.keyboard.press('Enter');
    assert.equal(await toggle.getAttribute('aria-expanded'), 'true', 'Enter no abre Filtros');
    assert.equal(await page.locator('[data-catalogue-refine]').isVisible(), true);
    assert.equal(await top(page, '[data-filter="q"]'), searchTop, 'abrir Filtros desplaza la búsqueda');
    const box = page.locator('[data-facet-group="grupo"] input[data-facet]').first();
    await box.focus();
    await page.keyboard.press('Space');
    assert.equal(await box.isChecked(), true);
    assert.match(await toggle.innerText(), /1 activo\b/, 'el botón no resume el filtro activo');
    assert.notEqual(await count.innerText(), total, 'el filtro no cambia el recuento');
    assert.match(page.url(), /#grupo=/, 'el filtro no llega a la URL compartible');
    await page.keyboard.press('Escape');
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false', 'Escape no cierra Filtros');
    assert.equal(await page.locator('[data-catalogue-refine]').isVisible(), false);
    assert.equal(await toggle.evaluate(e => e === document.activeElement), true, 'Escape no devuelve el foco a Filtros');
    assert.match(await toggle.innerText(), /1 activo\b/, 'el resumen se pierde al cerrar');
    await page.keyboard.press('Enter');
    await page.locator('[data-catalogue-refine] button[type="reset"]').click();
    await page.waitForFunction(() => !location.hash.includes('grupo='));
    assert.doesNotMatch(await toggle.innerText(), /activo/, 'Restablecer no limpia el resumen');
    assert.equal(await count.innerText(), total, 'Restablecer no recupera el recuento');
    // El orden sigue en la cabecera de resultados y abrir ficha no depende de los filtros.
    await page.selectOption('[data-filter="orden"]', 'titulo');
    assert.match(page.url(), /orden=titulo/);
    assert.ok(await page.locator('.catalogue-card:not([hidden]) h3 a').first().getAttribute('href'));
    await context.close();
  }

  // URL compartida con filtros: el panel sigue plegado pero el resumen los cuenta.
  {
    const { context, page } = await open(390, { hash: '#formato=tapa-blanda&paginas=media' });
    const toggle = page.locator('[data-catalogue-refine-toggle]');
    assert.match(await toggle.innerText(), /2 activos/, 'los filtros de la URL no se resumen');
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    await context.close();
  }

  // Escritorio: panel siempre visible, sin botón de plegado.
  {
    const { context, page } = await open(1280);
    assert.equal(await page.locator('[data-catalogue-refine-toggle]').isVisible(), false, '1280px: el botón Filtros aparece en escritorio');
    assert.equal(await page.locator('[data-catalogue-refine]').isVisible(), true, '1280px: los filtros no se ven en escritorio');
    assert.ok(await top(page, '.catalogue-card:not([hidden])') <= 700, '1280px: la primera tarjeta baja');
    await context.close();
  }

  // Sin JS: libros y enlaces disponibles; Filtros no es una acción falsa.
  {
    const { context, page } = await open(390, { javaScriptEnabled: false });
    assert.ok(await page.locator('.catalogue-card h3 a[href]').count() > 0, 'sin JS no hay fichas enlazadas');
    // La cabecera sin JS del sitio añade ~64 px; lo que importa es que los filtros (inútiles sin JS) no se interpongan.
    assert.equal(await page.locator('[data-catalogue-refine]').isVisible(), false, 'sin JS los filtros deshabilitados ocupan la pantalla');
    assert.ok(await top(page, '.catalogue-card') <= CARD_BUDGET + 100, 'sin JS la primera tarjeta queda lejos');
    assert.equal(await page.locator('[data-catalogue-refine-toggle]').isDisabled(), true, 'sin JS Filtros parece utilizable');
    await context.close();
  }
} finally {
  await browser.close();
}
console.log('PASS catalogue mobile discovery');
