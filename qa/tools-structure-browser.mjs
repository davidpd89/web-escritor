import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const BASE_ORIGIN = new URL(BASE).origin;
const OUT = path.resolve('qa-artifacts/tools-structure');
const SENTINEL = 'LOCAL_QA_SENTINEL_582931';

const routes = {
  personajes: '/herramientas/personajes/',
  nombres: '/herramientas/nombres-personajes/',
  pov: '/herramientas/distribucion-pov/',
};

const metadata = {
  personajes: {
    title: 'Mapa de relaciones de personajes | Herramientas',
    description: 'Crea un mapa visual de relaciones entre personajes en tu navegador. Sin cuenta ni servidor.',
    canonical: 'https://davidportodiaz.com/herramientas/personajes/',
    h1: 'Mapa de relaciones de personajes',
  },
  nombres: {
    title: 'Comprobador de nombres | Herramientas',
    description: 'Detecta nombres de personajes parecidos que pueden confundir al lector. Análisis local en el navegador.',
    canonical: 'https://davidportodiaz.com/herramientas/nombres-personajes/',
    h1: 'Comprobador de nombres de personaje',
  },
  pov: {
    title: 'Distribución de POV por escenas | Herramientas',
    description: 'Visualiza cómo se reparten los puntos de vista de una novela por escenas: secuencia, carriles, porcentaje, rachas y huecos. Sin subir el manuscrito.',
    canonical: 'https://davidportodiaz.com/herramientas/distribucion-pov/',
    h1: 'Ve cómo se reparten tus POV a lo largo de la novela.',
  },
};

const viewports = [
  { width: 320, height: 900 },
  { width: 390, height: 900 },
  { width: 768, height: 900 },
  { width: 1024, height: 900 },
  { width: 1440, height: 1000 },
  { width: 844, height: 390 },
];

const exfil = new Map(Object.keys(routes).map(key => [key, []]));
const external = new Map(Object.keys(routes).map(key => [key, []]));

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

function isExternalNetworkUrl(rawUrl) {
  try {
    const url = new URL(rawUrl);
    return ['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol) && url.origin !== BASE_ORIGIN;
  } catch {
    return false;
  }
}

function track(page, key) {
  page.on('request', request => {
    const raw = `${request.url()}\n${request.postData() || ''}`;
    if (raw.includes(SENTINEL)) {
      exfil.get(key).push(`request:${request.method()}:${request.url()}`);
    }
    if (isExternalNetworkUrl(request.url())) {
      external.get(key).push(`request:${request.method()}:${request.url()}`);
    }
  });
  page.on('websocket', socket => {
    if (socket.url().includes(SENTINEL)) exfil.get(key).push(`websocket:${socket.url()}`);
    if (isExternalNetworkUrl(socket.url())) external.get(key).push(`websocket:${socket.url()}`);
  });
  page.on('framenavigated', frame => {
    if (frame !== page.mainFrame()) return;
    const url = frame.url();
    if (url && !url.startsWith(BASE) && url !== 'about:blank') {
      external.get(key).push(`navigation:${url}`);
      if (url.includes(SENTINEL)) exfil.get(key).push(`navigation:${url}`);
    }
  });
}

async function open(key, viewport = { width: 1440, height: 1000 }, javaScriptEnabled = true) {
  const context = await browser.newContext({ viewport, javaScriptEnabled, reducedMotion: 'reduce' });
  await context.addInitScript(() => {
    window.__qaCLS = 0;
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) window.__qaCLS += entry.value;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  });
  const page = await context.newPage();
  track(page, key);
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', error => pageErrors.push(error.message));
  const response = await page.goto(BASE + routes[key], { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, `${key}: HTTP`);
  if (javaScriptEnabled) {
    assert.deepEqual(pageErrors, [], `${key}: excepciones JS`);
    assert.deepEqual(consoleErrors, [], `${key}: consola`);
  }
  return { context, page };
}

async function checkMetadata(page, key) {
  const got = await page.evaluate(() => ({
    title: document.title,
    description: document.querySelector('meta[name="description"]')?.content,
    canonical: document.querySelector('link[rel="canonical"]')?.href,
    h1: document.querySelector('h1')?.textContent.trim(),
    robots: document.querySelector('meta[name="robots"]')?.content,
    csp: document.querySelector('meta[http-equiv="Content-Security-Policy"]')?.content,
  }));
  assert.equal(got.title, metadata[key].title);
  assert.equal(got.description, metadata[key].description);
  assert.equal(got.canonical, metadata[key].canonical);
  assert.equal(got.h1, metadata[key].h1);
  assert.equal(got.robots, 'index,follow,max-image-preview:large');
  assert.match(got.csp || '', /connect-src 'none'/);
}

async function resizeViewport(page, viewport) {
  await page.setViewportSize(viewport);
  // Chromium can serve one stale layout pass for aspect-ratio boxes inside
  // overflow:auto + scrollbar-gutter:stable containers right after a
  // viewport resize (min-width from the resized media query not applied
  // yet). Two rAF ticks reliably let it settle before we measure.
  await page.evaluate(() => new Promise(resolve => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));
}

async function noOverflow(page, label) {
  const bad = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
  assert.equal(bad, false, `${label}: overflow horizontal de página`);
}

async function noBadNumbers(page, label) {
  const text = (await page.locator('main').innerText()).toLowerCase();
  assert.equal(/\b(?:nan|infinity|undefined)\b/.test(text), false, `${label}: valor inválido visible`);
}

async function checkCls(page, label) {
  await page.waitForTimeout(80);
  const value = await page.evaluate(() => window.__qaCLS || 0);
  assert.ok(value <= 0.1, `${label}: CLS ${value}`);
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: true });
}

async function minTarget(page, selector, label) {
  const box = await page.locator(selector).first().boundingBox();
  assert.ok(box, `${label}: target inexistente`);
  assert.ok(box.width >= 44 && box.height >= 44, `${label}: target ${box.width}×${box.height}`);
}

async function applyInspectorStyles(context, page, cssText) {
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { frameTree } = await cdp.send('Page.getFrameTree');
  const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
  await cdp.send('CSS.setStyleSheetText', { styleSheetId, text: cssText });
}

async function qaPersonajes() {
  const { context, page } = await open('personajes');
  await checkMetadata(page, 'personajes');
  await checkCls(page, 'personajes carga inicial');
  await minTarget(page, '#add-character', 'personajes: añadir personaje');

  const add = async name => {
    await page.fill('#character-name', name);
    await page.click('#add-character');
  };
  for (const name of ['Ana', 'Bruno', 'Clara', 'Diego']) await add(name);
  assert.equal(await page.locator('#relation-from option').count(), 5);
  await add('Ana');
  assert.match(await page.locator('[data-character-error]').innerText(), /ya está/i);

  const rel = async (from, to, type, label = '', directed = false) => {
    await page.selectOption('#relation-from', { label: from });
    await page.selectOption('#relation-to', { label: to });
    await page.selectOption('#relation-type', type);
    await page.fill('#relation-label', label);
    await page.locator('#relation-directed').setChecked(directed);
    await page.click('#add-relation');
  };

  await rel('Ana', 'Bruno', 'amistad', 'confianza');
  await rel('Bruno', 'Clara', 'rivalidad', 'competencia');
  await rel('Clara', 'Diego', 'familia', 'hermanos');
  await rel('Ana', 'Diego', 'mentoria', 'aprendizaje', true);
  assert.equal(await page.locator('#relation-list li').count(), 4);
  assert.equal(await page.locator('.map-edge').count(), 4);
  assert.equal(await page.locator('.map-node').count(), 4);
  assert.match(await page.locator('#relation-list').innerText(), /Ana\s+→\s+Diego/);
  await minTarget(page, '#add-relation', 'personajes: añadir relación');

  const ana = page.locator('.map-node[data-id="ana"]');
  const anaCircle = ana.locator('circle');
  const connectedLine = page.locator('.map-edge[data-from="ana"] line').first();
  await anaCircle.scrollIntoViewIfNeeded();
  await anaCircle.hover();
  const anaBox = await anaCircle.boundingBox();
  assert.ok(anaBox, 'personajes: círculo de Ana no visible');
  const startX = anaBox.x + anaBox.width / 2;
  const startY = anaBox.y + anaBox.height / 2;
  const hitId = await page.evaluate(({ x, y }) => document.elementFromPoint(x, y)?.closest('.map-node')?.dataset.id || '', { x: startX, y: startY });
  assert.equal(hitId, 'ana', `personajes: el punto de drag impacta en ${hitId || 'ningún nodo'}`);
  const transformBefore = await ana.getAttribute('transform');
  const lineBefore = await connectedLine.evaluate(line => `${line.getAttribute('x1')},${line.getAttribute('y1')},${line.getAttribute('x2')},${line.getAttribute('y2')}`);
  await page.mouse.move(startX, startY);
  await page.mouse.down({ button: 'left' });
  await page.mouse.move(startX + 90, startY + 55, { steps: 8 });
  await page.mouse.up({ button: 'left' });
  await page.waitForTimeout(30);
  const transformAfter = await ana.getAttribute('transform');
  const lineAfter = await connectedLine.evaluate(line => `${line.getAttribute('x1')},${line.getAttribute('y1')},${line.getAttribute('x2')},${line.getAttribute('y2')}`);
  assert.notEqual(transformAfter, transformBefore, 'personajes: el drag no mueve el nodo');
  assert.notEqual(lineAfter, lineBefore, 'personajes: el drag no actualiza las aristas');

  await rel('Ana', 'Diego', 'mentoria', 'aprendizaje', true);
  assert.match(await page.locator('[data-relation-error]').innerText(), /ya está declarada/i);
  await page.getByRole('button', { name: 'Eliminar relación Ana y Diego' }).click();
  assert.equal((await page.locator('[data-relation-error]').innerText()).trim(), '', 'personajes: error obsoleto tras eliminar');
  assert.equal(await page.locator('#relation-list li').count(), 3);
  await rel('Ana', 'Diego', 'mentoria', 'aprendizaje', true);

  await page.selectOption('#relation-from', { label: 'Ana' });
  await page.selectOption('#relation-to', { label: 'Ana' });
  await page.click('#add-relation');
  assert.match(await page.locator('[data-relation-error]').innerText(), /distintos/i);

  const edges = await page.locator('.map-edge').count();
  await page.locator('[data-relation-filter][value="rivalidad"]').uncheck();
  assert.ok((await page.locator('.map-edge').count()) < edges);
  assert.match(await page.locator('#map-stats').innerText(), /visibles/i);
  await page.locator('[data-relation-filter][value="rivalidad"]').check();
  await page.selectOption('#map-focus', { label: 'Ana' });
  assert.ok((await page.locator('.map-node').count()) < 4);
  assert.match(await page.locator('#map-stats').innerText(), /visibles/i);
  await page.selectOption('#map-focus', '');

  const jsonDownload = page.waitForEvent('download');
  await page.click('#export-json');
  const jsonFile = await jsonDownload;
  const jsonText = await fs.readFile(await jsonFile.path(), 'utf8');
  const saved = JSON.parse(jsonText);
  assert.equal(saved.characters.length, 4);
  assert.equal(saved.relations.length, 4);
  assert.equal(saved.relations.filter(relation => relation.directed).length, 1);

  const svgDownload = page.waitForEvent('download');
  await page.click('#export-svg');
  const svgFile = await svgDownload;
  const svgText = await fs.readFile(await svgFile.path(), 'utf8');
  assert.match(svgText, /<svg/);
  assert.match(svgText, /<title>Ana<\/title>/);

  await page.click('#clear-map');
  assert.equal(await page.locator('#relation-list li').count(), 0);
  await page.setInputFiles('#import-file', { name: 'mapa.json', mimeType: 'application/json', buffer: Buffer.from(jsonText) });
  await page.waitForTimeout(40);
  assert.equal(await page.locator('#relation-list li').count(), 4);
  await page.setInputFiles('#import-file', { name: 'mal.json', mimeType: 'application/json', buffer: Buffer.from('{malformed') });
  await page.waitForTimeout(40);
  assert.match(await page.locator('#map-status').innerText(), /no se ha podido/i);

  const chars = Array.from({ length: 7 }, (_, i) => ({
    id: `p${i + 1}`,
    name: i === 0 ? 'Personaje con un nombre deliberadamente muy largo de cuarenta caracteres' : `Personaje ${i + 2}`,
  }));
  const types = ['familia', 'amistad', 'romance', 'rivalidad', 'alianza', 'mentoria', 'secreto'];
  const relations = [];
  let relationIndex = 0;
  for (let i = 0; i < chars.length; i += 1) {
    for (let j = i + 1; j < chars.length; j += 1) {
      relationIndex += 1;
      relations.push({
        from: chars[i].id,
        to: chars[j].id,
        type: types[(relationIndex - 1) % types.length],
        label: `relación editorial ${relationIndex}`,
        evolution: 'Contexto de prueba',
        directed: relationIndex % 4 === 0,
      });
    }
  }
  await page.setInputFiles('#import-file', {
    name: 'grande.json',
    mimeType: 'application/json',
    buffer: Buffer.from(JSON.stringify({ version: 1, title: 'Mapa grande', characters: chars, relations })),
  });
  await page.waitForTimeout(80);
  assert.equal(await page.locator('#relation-list li').count(), 21);
  assert.equal(await page.locator('.map-edge').count(), 21);

  await page.fill('#character-name', SENTINEL);
  await page.click('#add-character');
  await page.selectOption('#relation-from', 'p1');
  await page.selectOption('#relation-to', 'p2');
  await page.selectOption('#relation-type', 'otro');
  await page.fill('#relation-label', SENTINEL);
  await page.click('#add-relation');
  await page.waitForTimeout(80);

  await noOverflow(page, 'personajes 1440');
  await noBadNumbers(page, 'personajes');
  await screenshot(page, 'personajes-1440-result.png');
  await resizeViewport(page, { width: 390, height: 900 });
  await noOverflow(page, 'personajes 390');
  const localScroll = await page.locator('.map-viewport').evaluate(el => el.scrollWidth > el.clientWidth + 1);
  assert.equal(localScroll, true, 'personajes: el mapa móvil no conserva scroll local');
  await screenshot(page, 'personajes-390-result.png');
  await minTarget(page, '#relation-list button', 'personajes: eliminar relación');
  await context.close();
}

async function qaNombres() {
  const { context, page } = await open('nombres');
  await checkMetadata(page, 'nombres');
  await checkCls(page, 'nombres carga inicial');
  await minTarget(page, 'main button[type="submit"]', 'nombres: analizar');
  assert.equal(await page.locator('[data-results]').isHidden(), true, 'nombres: resultados deben iniciar ocultos');

  const analyze = async text => {
    await page.fill('[data-names-input]', text);
    await page.locator('form:not(#newsletter-form-explore)').first().evaluate(form => form.requestSubmit());
    await page.waitForTimeout(30);
  };

  await analyze('Álvaro\nAlvaro\nBruno\nXimena');
  assert.ok((await page.locator('.namecheck-pair').count()) >= 1);
  assert.match(await page.locator('[data-results]').innerText(), /Motivo:/);
  await page.fill('[data-names-input]', 'Álvaro\nAlvaro\nBruno\nXimena\nZoe');
  assert.equal(await page.locator('[data-results]').isHidden(), true, 'nombres: editar debe ocultar resultado obsoleto');

  await analyze('Beatriz, Gonzalo, Ximena');
  assert.equal(await page.locator('.namecheck-pair').count(), 0);
  assert.match(await page.locator('[data-results]').innerText(), /No aparecen parejas/);
  await analyze('Álvaro; Alvaro\nBruno');
  assert.ok((await page.locator('.namecheck-pair').count()) >= 1);
  await analyze('Noa\nnoa\nNOA\nBruno');
  assert.match(await page.locator('[data-summary]').innerText(), /^2 nombres/);
  await analyze('');
  assert.equal(await page.locator('[data-names-input]').getAttribute('aria-invalid'), 'true');
  assert.equal(await page.locator('[data-results]').isHidden(), true);
  await analyze('Único');
  assert.equal(await page.locator('[data-names-input]').getAttribute('aria-invalid'), 'true');

  const longList = Array.from({ length: 30 }, (_, i) => `NombreEditorialMuyLargo${String(i).padStart(2, '0')}XYZ`).join('\n');
  await analyze(longList);
  assert.match(await page.locator('[data-summary]').innerText(), /^30 nombres/);
  await noBadNumbers(page, 'nombres');
  await analyze('Álvaro\nAlvaro\nBruno\nXimena');
  await screenshot(page, 'nombres-1440-result.png');
  await analyze(`${SENTINEL}\nSentinela`);
  await page.waitForTimeout(80);
  await noOverflow(page, 'nombres 1440');
  await context.close();
}

async function qaPov() {
  const { context, page } = await open('pov');
  await checkMetadata(page, 'pov');
  await checkCls(page, 'pov carga inicial');
  await minTarget(page, '[data-pov-run]', 'pov: analizar distribución');

  const controlled = [
    '1.1 | Ana | 1420',
    '1.2 | Ana | 980',
    '2.1 | Bruno | 1310',
    '2.2 | Clara | 1200',
    '3.1 | Ana | 1550',
    '3.2 | Bruno | 1180',
    '4.1 | Bruno | 990',
    '5.1 | Clara | 1300',
  ].join('\n');

  const analyze = async text => {
    await page.fill('[data-pov-input]', text);
    await page.locator('[data-pov-form]').evaluate(form => form.requestSubmit());
    await page.waitForTimeout(30);
  };

  await analyze(controlled);
  assert.equal(await page.locator('.pov-scene').count(), 8);
  assert.equal(await page.locator('.pov-lane-row').count(), 3);
  assert.equal(await page.locator('[data-pov-summary] tr').count(), 3);
  const model = await page.evaluate(() => {
    const parsed = window.PovDistribution.parse(document.querySelector('[data-pov-input]').value);
    return window.PovDistribution.analyze(parsed.scenes);
  });
  assert.equal(model.totalScenes, 8);
  assert.equal(model.totalWords, 9930);
  const ana = model.povs.find(item => item.pov === 'Ana');
  assert.equal(ana.sceneCount, 3);
  assert.equal(ana.longestRun, 2);
  assert.equal(ana.maxInternalGap, 2);
  await noBadNumbers(page, 'pov control');
  await screenshot(page, 'pov-1440-result.png');

  await resizeViewport(page, { width: 390, height: 900 });
  await noOverflow(page, 'pov 390 result');
  const lanesScroll = await page.locator('.pov-lanes').evaluate(el => el.scrollWidth > el.clientWidth + 1);
  const tableScroll = await page.locator('.pov-table-wrap').evaluate(el => el.scrollWidth > el.clientWidth + 1);
  assert.equal(lanesScroll, true, 'pov: carriles sin scroll local en móvil');
  assert.equal(tableScroll, true, 'pov: tabla sin scroll local en móvil');
  await screenshot(page, 'pov-390-result.png');
  await resizeViewport(page, { width: 1440, height: 1000 });

  await analyze('1.1 | Ana\n1.2 | Bruno\n2.1 | Ana');
  assert.match(await page.locator('[data-pov-metrics]').innerText(), /Opcionales/);
  await analyze('1.1\tAna\t1000\n1.2\tBruno\t1200');
  assert.equal(await page.locator('.pov-scene').count(), 2);
  await analyze('1.1 | Ana\nlínea inválida');
  assert.equal(await page.locator('[data-pov-input]').getAttribute('aria-invalid'), 'true');
  assert.ok(await page.locator('[data-pov-results]').isHidden());
  await analyze('');
  assert.equal(await page.locator('[data-pov-input]').getAttribute('aria-invalid'), 'true');
  await analyze('1 | POV con nombre deliberadamente largo de cuarenta caracteres | 100000\n2 | POV con nombre deliberadamente largo de cuarenta caracteres | 99999');
  assert.equal(await page.locator('[data-pov-summary] tr').count(), 1);
  assert.match(await page.locator('[data-pov-summary]').innerText(), /2\s+100 %/);
  await analyze(`1 | ${SENTINEL} | 1000\n2 | Ana | 900`);
  await page.waitForTimeout(80);
  await noOverflow(page, 'pov 1440');
  await context.close();
}

async function responsiveAndA11y() {
  for (const key of Object.keys(routes)) {
    for (const viewport of viewports) {
      const { context, page } = await open(key, viewport);
      await noOverflow(page, `${key} ${viewport.width}x${viewport.height}`);
      const positive = await page.locator('[tabindex]').evaluateAll(elements => elements.filter(el => Number(el.getAttribute('tabindex')) > 0).length);
      assert.equal(positive, 0, `${key}: tabindex positivo`);
      await context.close();
    }

    const zoomed = await open(key, { width: 640, height: 900 });
    const cdp = await zoomed.context.newCDPSession(zoomed.page);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
    const scale = await zoomed.page.evaluate(() => window.visualViewport?.scale || 1);
    assert.ok(scale >= 1.9, `${key}: zoom 200%`);
    await noOverflow(zoomed.page, `${key} zoom 200%`);
    await zoomed.context.close();

    const spaced = await open(key, { width: 320, height: 900 });
    await applyInspectorStyles(
      spaced.context,
      spaced.page,
      'p,li,label,input,textarea,button,select,a,th,td{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}',
    );
    await noOverflow(spaced.page, `${key} text-spacing`);
    await spaced.context.close();

    const nojs = await open(key, { width: 390, height: 900 }, false);
    assert.ok(await nojs.page.locator('h1').isVisible());
    assert.ok(await nojs.page.locator('main noscript').isVisible());
    assert.ok(await nojs.page.locator('main').getByText(/Privacidad|Privado por diseño/).first().isVisible());
    assert.ok(await nojs.page.locator('main').getByRole('heading', { name: /Qué|Cómo|Qué no hace/ }).first().isVisible());
    await noOverflow(nojs.page, `${key} no-js`);
    await nojs.context.close();
  }
}

try {
  await qaPersonajes();
  await qaNombres();
  await qaPov();
  await responsiveAndA11y();

  for (const key of Object.keys(routes)) {
    assert.deepEqual(exfil.get(key), [], `${key}: INPUT EXFILTRATION ${exfil.get(key).join(', ')}`);
    assert.deepEqual(external.get(key), [], `${key}: tráfico externo ${external.get(key).join(', ')}`);
  }

  const report = {
    inputExfiltration: '0/3',
    externalNetworkRequests: '0/3',
    routes: Object.fromEntries([...exfil].map(([key, value]) => [key, value.length])),
    externalRoutes: Object.fromEntries([...external].map(([key, value]) => [key, value.length])),
    viewports,
    metadataPreserved: true,
    textSpacingUnderCsp: true,
    dragHitTested: true,
  };
  await fs.writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log('TOOLS STRUCTURE QA PASS', report);
} catch (error) {
  await fs.writeFile(path.join(OUT, 'failure.txt'), error.stack || String(error));
  console.error(error);
  process.exitCode = 1;
} finally {
  await browser.close();
}
