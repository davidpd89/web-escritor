import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

// Run from repository root with a local static server on port 4173.
const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve('qa-artifacts/home-map');
await fs.mkdir(OUT, { recursive: true });

const NODES = [
  ['manecillas', '/las-manecillas-del-recuerdo/'],
  ['autor', '/autor.html'],
  ['samuel', '/libros/samuel-entre-mundos/'],
  ['cuaderno', '/cuaderno/'],
  ['herramientas', '/herramientas/'],
  ['prensa', '/prensa.html'],
];
const EXPECTED = {
  manecillas: ['1', '.16', '.14'],
  autor: ['.92', '.82', '.76'],
  samuel: ['1', '.16', '.14'],
  cuaderno: ['.18', '1', '.14'],
  herramientas: ['.18', '1', '.14'],
  prensa: ['.18', '.16', '1'],
};
const VIEWPORTS = [[1440,900],[1024,900],[768,1000],[390,900],[320,900]];

// Preview copy is deliberately redundant with the six real links. Keep it
// decorative for assistive technology via CSS generated-content alt text.
const cssSource = await fs.readFile('assets/v1-home.css', 'utf8');
const decorativePreviewRules = cssSource.match(/\.map-nodes::after\{content:[^\n]+\/ ""\}/g) || [];
assert.equal(decorativePreviewRules.length, 6, 'a11y: los seis previews deben tener alternativa vacía');

const browser = await chromium.launch({
  headless: true,
  ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH }
    : {}),
});

function trapErrors(page) {
  const state = { pageErrors: [], consoleErrors: [] };
  page.on('pageerror', error => state.pageErrors.push(String(error)));
  page.on('console', msg => { if (msg.type() === 'error') state.consoleErrors.push(msg.text()); });
  return state;
}

async function open(context) {
  const page = await context.newPage();
  const errors = trapErrors(page);
  // El widget del asistente muestra un aviso una vez por sesión. Este suite
  // mide cartografía y no el widget, así que se marca su clave de sesión para
  // evitar superposición accidental durante hover/focus.
  await page.addInitScript(() => {
    try { sessionStorage.setItem('davidporto-assistant-widget-hint-v2', '1'); } catch { /* sin sessionStorage tampoco aparece el aviso */ }
    window.__homeMapCls = 0;
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__homeMapCls += entry.value;
    }).observe({ type: 'layout-shift', buffered: true });
  });
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(250);
  return { page, errors };
}

async function assertCore(page, label) {
  assert.equal(await page.locator('.map-nodes .map-node[data-map-node]').count(), 6, `${label}: seis nodos`);
  for (const [key, href] of NODES) {
    const node = page.locator(`[data-map-node="${key}"]`);
    assert.equal(await node.getAttribute('href'), href, `${label}: href ${key}`);
    assert.ok(await node.isVisible(), `${label}: ${key} visible`);
  }
  assert.equal(await page.locator('[data-map-node="jaula"]').count(), 0, `${label}: sin Jaula`);
  assert.equal(await page.locator('.map-routes').getAttribute('aria-hidden'), 'true', `${label}: SVG decorativo`);
  const paths = page.locator('.map-routes path');
  assert.equal(await paths.count(), 4, `${label}: SVG legacy conservado en DOM`);
  if ((await page.viewportSize()).width >= 900) {
    assert.notEqual(await paths.nth(0).evaluate(el => getComputedStyle(el).display), 'none', `${label}: ruta Obra visible`);
    for (let i = 1; i < 4; i++) assert.equal(await paths.nth(i).evaluate(el => getComputedStyle(el).display), 'none', `${label}: ruta legacy ${i + 1} no visible`);
  }
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 1, `${label}: overflow horizontal ${overflow}px`);
}

async function routeState(page) {
  return page.locator('.map-stage').evaluate(el => {
    const cs = getComputedStyle(el);
    return ['--route-work-opacity','--route-process-opacity','--route-public-opacity'].map(name => cs.getPropertyValue(name).trim());
  });
}

async function assertState(page, key, label) {
  assert.deepEqual(await routeState(page), EXPECTED[key], `${label}: rutas de ${key}`);
}

async function assertNodesRemainVisible(page, activeKey, label) {
  for (const [key] of NODES) {
    const node = page.locator(`[data-map-node="${key}"]`);
    assert.ok(await node.isVisible(), `${label}: ${key} sigue visible`);
    const opacity = Number(await node.evaluate(el => getComputedStyle(el).opacity));
    assert.ok(opacity >= .8, `${label}: ${key} no desaparece (${opacity})`);
    if (key === activeKey) assert.ok(opacity >= .99, `${label}: ${key} activo reforzado`);
  }
}

async function preview(page) {
  return page.locator('.map-nodes').evaluate(el => ({
    text: getComputedStyle(el, '::after').content,
    textOpacity: Number(getComputedStyle(el, '::after').opacity),
    mediaOpacity: Number(getComputedStyle(el, '::before').opacity),
    media: getComputedStyle(el, '::before').backgroundImage,
    textDuration: getComputedStyle(el, '::after').transitionDuration,
    mediaDuration: getComputedStyle(el, '::before').transitionDuration,
  }));
}

// Spacious desktop: all hover states + keyboard focus + stable preview.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const { page, errors } = await open(context);
  await assertCore(page, '1440');
  await page.locator('.cartography').scrollIntoViewIfNeeded();
  await page.screenshot({ path: path.join(OUT, '1440-rest.png') });
  assert.equal((await preview(page)).textOpacity, 0, '1440: preview oculto en reposo');

  for (const [key] of NODES) {
    await page.locator(`[data-map-node="${key}"]`).hover();
    await page.waitForTimeout(220);
    await assertState(page, key, `hover ${key}`);
    await assertNodesRemainVisible(page, key, `hover ${key}`);
    const p = await preview(page);
    assert.ok(p.textOpacity > .9, `hover ${key}: preview contextual visible`);
    if (key === 'manecillas') {
      assert.ok(p.mediaOpacity > .9, 'Manecillas: portada visible');
      assert.match(p.media, /portada-las-manecillas-del-recuerdo-512\.webp/, 'Manecillas: portada oficial');
      await page.screenshot({ path: path.join(OUT, '1440-manecillas-active.png') });
    } else if (key === 'samuel') {
      assert.ok(p.mediaOpacity > .9, 'Samuel: portada visible');
      assert.match(p.media, /samuel-entre-mundos\.webp/, 'Samuel: portada oficial');
    } else {
      assert.ok(p.mediaOpacity < .1, `${key}: preview tipográfico sin media inventada`);
    }
    if (key === 'autor') await page.screenshot({ path: path.join(OUT, '1440-autor-active.png') });
  }

  // Caso mixto: foco y puntero en nodos distintos. El foco debe dominar.
  await page.locator('body').focus();
  let tabFocused = '';
  for (let i = 0; i < 60 && tabFocused !== 'manecillas'; i++) {
    await page.keyboard.press('Tab');
    tabFocused = await page.evaluate(() => document.activeElement?.getAttribute?.('data-map-node') || '');
  }
  assert.equal(tabFocused, 'manecillas', 'teclado alcanza manecillas para caso mixto');
  await page.waitForTimeout(220);
  await page.locator('[data-map-node="prensa"]').hover();
  await page.waitForTimeout(220);
  await assertState(page, 'manecillas', 'focus domina sobre hover inicial');

  await page.locator('body').focus();
  const seen = [];
  for (let i = 0; i < 100 && seen.length < 6; i++) {
    await page.keyboard.press('Tab');
    const key = await page.evaluate(() => document.activeElement?.getAttribute?.('data-map-node') || '');
    if (key && !seen.includes(key)) {
      seen.push(key);
      // La rama de hover espera 220 ms y esta no esperaba nada. .map-node
      // transiciona la opacidad, asi que medir en el mismo tick que el Tab
      // devuelve un valor intermedio y "activo reforzado" (>=.99) fallaba
      // aunque el estado final sea 1. Misma espera que en hover.
      await page.waitForTimeout(220);
      await assertState(page, key, `focus ${key}`);
      await assertNodesRemainVisible(page, key, `focus ${key}`);
      assert.ok((await preview(page)).textOpacity > .9, `focus ${key}: preview contextual`);

      // Aunque el ratón entre en otro nodo, el foco debe conservar el resalte.
      if (key !== 'prensa') {
        await page.locator('[data-map-node="prensa"]').hover();
        await page.waitForTimeout(220);
        await assertState(page, key, `focus ${key} mantiene prioridad tras hover prensa`);
      }
    }
  }
  const expectedOrder = NODES.map(([key]) => key);
  const start = expectedOrder.indexOf(seen[0]);
  const rotated = expectedOrder.slice(start).concat(expectedOrder.slice(0, start));
  assert.deepEqual(seen, rotated, '1440: Tab recorre los seis nodos en orden cíclico');
  assert.ok((await page.evaluate(() => window.__homeMapCls || 0)) <= .1, '1440: CLS <= 0.1');
  assert.deepEqual(errors.pageErrors, [], `1440 pageerror: ${errors.pageErrors.join(' | ')}`);
  assert.deepEqual(errors.consoleErrors, [], `1440 console: ${errors.consoleErrors.join(' | ')}`);
  await context.close();
}

// 1024, 768, 390, 320: responsive and no large preview.
for (const [width, height] of VIEWPORTS.slice(1)) {
  const context = await browser.newContext({ viewport: { width, height } });
  const { page, errors } = await open(context);
  await assertCore(page, String(width));
  await page.locator('.cartography').scrollIntoViewIfNeeded();
  const p = await preview(page);
  assert.equal(p.text, 'none', `${width}: preview grande no existe`);
  if (width <= 767) {
    for (const [key] of NODES) {
      const box = await page.locator(`[data-map-node="${key}"]`).boundingBox();
      assert.ok(box && box.height >= 44, `${width}: target ${key} >= 44px`);
    }
  }
  assert.ok((await page.evaluate(() => window.__homeMapCls || 0)) <= .1, `${width}: CLS <= 0.1`);
  assert.deepEqual(errors.pageErrors, [], `${width}: pageerror`);
  assert.deepEqual(errors.consoleErrors, [], `${width}: console error`);
  if (width === 390) await page.screenshot({ path: path.join(OUT, '390-mobile.png') });
  await context.close();
}

// No-JS: links, base routes and CSS interaction remain usable.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
  const { page, errors } = await open(context);
  await assertCore(page, 'no-js');
  assert.equal(await page.locator('.map-nodes').evaluate(el => getComputedStyle(el, '::after').position), 'absolute', 'no-js: preview fuera del flujo');
  await page.locator('[data-map-node="manecillas"]').hover();
  await page.waitForTimeout(220);
  await assertState(page, 'manecillas', 'no-js hover Manecillas');
  assert.ok((await preview(page)).textOpacity > .9, 'no-js: interacción CSS disponible');
  assert.deepEqual(errors.pageErrors, [], 'no-js: pageerror');
  assert.deepEqual(errors.consoleErrors, [], 'no-js: console error');
  await context.close();
}

// Reduced motion: states remain but preview/routes/nodes do not transition.
{
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
  const { page } = await open(context);
  await page.locator('.cartography').scrollIntoViewIfNeeded();
  await page.locator('[data-map-node="autor"]').hover();
  await assertState(page, 'autor', 'reduced motion Autor');
  // El umbral no es 0 exacto. La receta de reduced motion del sitio, en
  // v1-base.css, es transition-duration:.01ms!important, no 0s, y eso es
  // deliberado: a 0s el navegador no dispara transitionend y cualquier JS que
  // lo espere se queda colgado. .01ms es 1e-05 s, imperceptible pero distinto
  // de cero, asi que exigir === 0 hacia fallar la suite contra el propio
  // sistema del sitio. Lo que hay que comprobar es que no queda animacion
  // perceptible; 1 ms cumple eso con margen de sobra.
  const IMPERCEPTIBLE_S = 0.001;
  const p = await preview(page);
  assert.ok(parseFloat(p.textDuration) <= IMPERCEPTIBLE_S, `reduced motion preview text: ${p.textDuration}`);
  assert.ok(parseFloat(p.mediaDuration) <= IMPERCEPTIBLE_S, `reduced motion preview media: ${p.mediaDuration}`);
  const nodeDuration = await page.locator('[data-map-node="autor"]').evaluate(el => getComputedStyle(el).transitionDuration);
  assert.ok(nodeDuration.split(',').every(v => parseFloat(v) <= IMPERCEPTIBLE_S), `reduced motion node: ${nodeDuration}`);
  await context.close();
}

await browser.close();
console.log('HOME MAP INTERACTION QA PASS');
