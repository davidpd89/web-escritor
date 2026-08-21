import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts';
const SENTINEL = 'LOCAL_QA_SENTINEL_582931';

const tools = [
  { key: 'manuscrito', path: '/herramientas/manuscrito/', input: '[data-chapter-paste]', result: '[data-chapter-results]' },
  { key: 'dialogo', path: '/herramientas/dialogo/', input: '#dialogue-text', result: '[data-dialogue-results]' },
  { key: 'legibilidad', path: '/herramientas/legibilidad/', input: '[data-readability-input]', result: '[data-readability-results]' },
  { key: 'repeticiones', path: '/herramientas/repeticiones/', input: '[data-repetition-input]', result: '[data-repetition-results]' },
  { key: 'variedad-lexica', path: '/herramientas/variedad-lexica/', input: '[data-lexical-input]', result: '[data-lexical-results]' },
];

const viewports = [
  { name: '320', width: 320, height: 760 },
  { name: '390', width: 390, height: 844 },
  { name: '768', width: 768, height: 1024 },
  { name: '1024', width: 1024, height: 900 },
  { name: '1440', width: 1440, height: 1000 },
  { name: 'landscape', width: 844, height: 390 },
];

function repeatedWords(count = 150) {
  const vocab = ['puerta','sombra','reloj','memoria','calle','lluvia','pasillo','voz','luz','noche','carta','ventana','piedra','nombre','silencio','viaje','casa','mano','tiempo','recuerdo'];
  return Array.from({ length: count }, (_, i) => vocab[i % vocab.length]).join(' ');
}

function sampleFor(key) {
  if (key === 'manuscrito') return `Capítulo 1\n${SENTINEL}. Ana abrió la puerta. La puerta seguía abierta.\n\n—No pienso entrar —dijo Ana—. Todavía no.\n\n***\n\n${repeatedWords(70)}\n\nCapítulo 2\nBruno miró el reloj. ${repeatedWords(90)}`;
  if (key === 'dialogo') return `${SENTINEL}. Ana miró la puerta y respiró.\n\n—No sé si debería entrar —dijo Ana—, pero voy a hacerlo.\n\nLa casa estaba vacía.\n\n—Entonces entra —respondió Bruno.`;
  if (key === 'legibilidad') return `${SENTINEL}. Esta es una frase breve. ${Array.from({length: 10}, (_, i) => `Este párrafo número ${i + 1} contiene palabras distintas y algunas oraciones más largas para comparar la densidad formal de la muestra sin enviar nada fuera del navegador. Otra frase cierra el bloque.`).join('\n\n')}`;
  if (key === 'repeticiones') return `${SENTINEL}. La puerta estaba abierta. La puerta seguía abierta. Ana dio un paso. Ana dio otro paso. Esto esto quedó duplicado. Entonces miró la puerta y entonces recordó que la puerta siempre chirriaba. Parecía tranquila. Parecía tranquila.`;
  return `${SENTINEL} ${repeatedWords(170)} ${Array.from({length: 40}, (_, i) => `termino${i}`).join(' ')}`;
}

function submitSelector(key) {
  return key === 'manuscrito' ? '[data-chapter-analyzer] button[type="submit"]'
    : key === 'dialogo' ? '[data-dialogue-tool] button[type="submit"]'
    : key === 'legibilidad' ? '[data-readability-form] button[type="submit"]'
    : key === 'repeticiones' ? '[data-repetition-form] button[type="submit"]'
    : '[data-lexical-form] button[type="submit"]';
}

async function waitForResult(page, tool) {
  await page.locator(tool.result).waitFor({ state: 'visible', timeout: 8000 });
}

async function assertNoBodyOverflow(page, label) {
  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    bodyWidth: document.body?.scrollWidth || 0,
  }));
  assert(metrics.scrollWidth <= metrics.clientWidth + 1, `${label}: overflow horizontal document ${JSON.stringify(metrics)}`);
  assert(metrics.bodyWidth <= metrics.clientWidth + 1, `${label}: overflow horizontal body ${JSON.stringify(metrics)}`);
}

async function runPrivacy(browser, report) {
  for (const tool of tools) {
    const context = await browser.newContext({ viewport: { width: 1024, height: 900 } });
    const page = await context.newPage();
    const requests = [];
    const sockets = [];
    let tracking = false;
    page.on('request', req => {
      if (!tracking) return;
      requests.push({ url: req.url(), method: req.method(), postData: req.postData() || '', type: req.resourceType() });
    });
    page.on('websocket', ws => { if (tracking) sockets.push(ws.url()); });
    const pageErrors = [];
    page.on('pageerror', err => pageErrors.push(String(err)));

    await page.goto(`${ORIGIN}${tool.path}`, { waitUntil: 'networkidle' });
    tracking = true;
    await page.locator(tool.input).fill(sampleFor(tool.key));
    await page.locator(submitSelector(tool.key)).click();
    await waitForResult(page, tool);
    await page.waitForTimeout(300);

    const external = requests.filter(r => {
      try { return new URL(r.url).origin !== ORIGIN; } catch { return true; }
    });
    const leaks = requests.filter(r => r.url.includes(SENTINEL) || r.postData.includes(SENTINEL));
    assert.equal(leaks.length, 0, `${tool.key}: el sentinel aparece en una request: ${JSON.stringify(leaks)}`);
    assert.equal(external.length, 0, `${tool.key}: request externa durante el análisis: ${JSON.stringify(external)}`);
    assert.equal(sockets.length, 0, `${tool.key}: websocket durante el análisis: ${JSON.stringify(sockets)}`);
    assert.deepEqual(pageErrors, [], `${tool.key}: errores JS: ${pageErrors.join(' | ')}`);

    report.privacy[tool.key] = { pass: true, requestsAfterInput: requests.map(r => ({ url: r.url, method: r.method, type: r.type })), sentinelLeaked: false, externalRequests: 0, websockets: 0 };
    await context.close();
  }
  console.log(`INPUT EXFILTRATION: 0/${tools.length}`);
}

async function runResponsive(browser, report) {
  for (const vp of viewports) {
    report.responsive[vp.name] = {};
    for (const tool of tools) {
      const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', err => errors.push(String(err)));
      await page.goto(`${ORIGIN}${tool.path}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(150);
      await assertNoBodyOverflow(page, `${tool.key}@${vp.name}`);
      assert.deepEqual(errors, [], `${tool.key}@${vp.name}: pageerror ${errors.join(' | ')}`);
      report.responsive[vp.name][tool.key] = { pass: true };
      await context.close();
    }
  }
}

async function runNoJs(browser, report) {
  for (const tool of tools) {
    const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${tool.path}`, { waitUntil: 'domcontentloaded' });
    const notice = page.getByText('JavaScript está desactivado.', { exact: false });
    await notice.waitFor({ state: 'visible', timeout: 3000 });
    assert(await page.locator('h1').isVisible(), `${tool.key}: H1 no visible sin JS`);
    assert(await page.locator('form').isVisible(), `${tool.key}: el formulario debe conservar su espacio desde el parseo inicial`);
    await assertNoBodyOverflow(page, `${tool.key}@no-js`);
    report.noJs[tool.key] = { pass: true, semanticNoscript: true };
    await context.close();
  }
}

async function runManuscriptFiles(browser, report) {
  const context = await browser.newContext({ viewport: { width: 1024, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', err => errors.push(String(err)));
  await page.goto(`${ORIGIN}/herramientas/manuscrito/`, { waitUntil: 'networkidle' });
  const fileInput = page.locator('[data-chapter-files]');
  const submit = page.locator('[data-chapter-analyzer] button[type="submit"]');
  const status = page.locator('[data-chapter-status]');
  const result = page.locator('[data-chapter-results]');
  const clear = page.locator('[data-chapter-clear]');

  await fileInput.setInputFiles({ name: 'capitulo-01.txt', mimeType: 'text/plain', buffer: Buffer.from(`Capítulo 1\n${SENTINEL} abrió la puerta.\n\n—Hola —dijo Ana—.\n\n***\n\n${repeatedWords(80)}`) });
  await submit.click();
  await result.waitFor({ state: 'visible', timeout: 8000 });
  assert.match(await status.textContent(), /capítulos analizados/i, 'manuscrito válido: falta estado de resultado');
  report.manuscript.valid = { pass: true, status: (await status.textContent())?.trim() };

  await clear.click();
  await fileInput.setInputFiles({ name: 'archivo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-invalid-for-tool') });
  await submit.click();
  await page.waitForFunction(() => !document.querySelector('[data-chapter-status]')?.textContent?.includes('Analizando…'));
  assert.match(await status.textContent(), /Añade archivos \.txt\/\.md o pega un manuscrito/i, 'manuscrito inválido: no se informa correctamente');
  assert(await result.isHidden(), 'manuscrito inválido: no debe mostrar un resultado anterior');
  report.manuscript.invalid = { pass: true, status: (await status.textContent())?.trim() };

  await clear.click();
  await fileInput.setInputFiles({ name: 'vacio.txt', mimeType: 'text/plain', buffer: Buffer.alloc(0) });
  await submit.click();
  await page.waitForFunction(() => !document.querySelector('[data-chapter-status]')?.textContent?.includes('Analizando…'), null, { timeout: 8000 });
  const emptyStatus = (await status.textContent())?.trim() || '';
  assert(emptyStatus.length > 0, 'manuscrito vacío: el estado no puede quedar vacío');
  assert(!/Analizando/.test(emptyStatus), 'manuscrito vacío: estado bloqueado en Analizando');
  report.manuscript.empty = { pass: true, status: emptyStatus, resultVisible: await result.isVisible() };
  assert.deepEqual(errors, [], `manuscrito FileReader: pageerror ${errors.join(' | ')}`);
  await context.close();
}

async function runAccessibility(browser, report) {
  for (const tool of tools) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${tool.path}`, { waitUntil: 'domcontentloaded' });

    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement?.classList.contains('skip-link')), true, `${tool.key}: primer Tab no llega al skip-link`);

    let foundFormFocus = false;
    let focusIndicator = false;
    for (let i = 0; i < 30; i += 1) {
      await page.keyboard.press('Tab');
      const state = await page.evaluate(() => {
        const el = document.activeElement;
        if (!(el instanceof HTMLElement)) return null;
        const cs = getComputedStyle(el);
        return {
          tag: el.tagName,
          inForm: Boolean(el.closest('form')),
          outline: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth || '0') > 0,
          shadow: cs.boxShadow !== 'none',
        };
      });
      if (state?.inForm) {
        foundFormFocus = true;
        focusIndicator = state.outline || state.shadow;
        break;
      }
    }
    assert(foundFormFocus, `${tool.key}: no se alcanza el formulario por teclado`);
    assert(focusIndicator, `${tool.key}: el control enfocado no muestra indicador visible`);

    await page.addStyleTag({ content: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important} p,li,dd,dt{margin-bottom:2em!important}' });
    await assertNoBodyOverflow(page, `${tool.key}@text-spacing`);

    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
    await page.waitForTimeout(100);
    assert(await page.locator('h1').isVisible(), `${tool.key}: H1 deja de ser visible a pageScaleFactor 2`);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 });

    report.accessibility[tool.key] = { keyboard: true, focusVisible: true, textSpacing: true, reducedMotion: true, zoom200Scale: true };
    await context.close();
  }
}

async function runCls(browser, report) {
  const context = await browser.newContext({ viewport: { width: 1350, height: 940 } });
  const page = await context.newPage();
  await page.addInitScript(() => {
    window.__qaCls = 0;
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) window.__qaCls += entry.value;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  });
  await page.goto(`${ORIGIN}/herramientas/manuscrito/`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  const cls = await page.evaluate(() => window.__qaCls || 0);
  assert(cls <= 0.10, `Manuscrito CLS ${cls} > 0.10`);
  report.cls = { manuscript: cls, pass: true, threshold: 0.10 };
  await context.close();
}

async function analyzeAndScreenshot(browser, toolKey, width, height, filename) {
  const tool = tools.find(t => t.key === toolKey);
  const context = await browser.newContext({ viewport: { width, height } });
  const page = await context.newPage();
  await page.goto(`${ORIGIN}${tool.path}`, { waitUntil: 'networkidle' });

  if (toolKey === 'manuscrito') {
    await page.locator('[data-chapter-files]').setInputFiles({ name: 'capitulos-qa.txt', mimeType: 'text/plain', buffer: Buffer.from(`Capítulo 1\n${SENTINEL}. Ana abrió la puerta.\n\n${repeatedWords(70)}\n\nCapítulo 2\n${repeatedWords(90)}`) });
  } else {
    await page.locator(tool.input).fill(sampleFor(toolKey));
  }
  await page.locator(submitSelector(toolKey)).click();
  await waitForResult(page, tool);
  await page.locator(tool.result).scrollIntoViewIfNeeded();
  await page.waitForTimeout(100);
  await page.screenshot({ path: path.join(OUT, filename), fullPage: false });
  await context.close();
}

async function runScreenshots(browser, report) {
  const shots = [
    ['manuscrito', 390, 844, 'manuscrito-390-result.png'],
    ['manuscrito', 1440, 1000, 'manuscrito-1440-result.png'],
    ['repeticiones', 390, 844, 'repeticiones-390-result.png'],
    ['repeticiones', 1440, 1000, 'repeticiones-1440-result.png'],
    ['variedad-lexica', 1440, 1000, 'variedad-lexica-1440-result.png'],
  ];
  for (const [key, width, height, file] of shots) await analyzeAndScreenshot(browser, key, width, height, file);
  report.screenshots = shots.map(([key, width, height, file]) => ({ tool: key, width, height, file, state: 'RESULT' }));
}

await fs.mkdir(OUT, { recursive: true });
const report = { privacy: {}, responsive: {}, noJs: {}, manuscript: {}, accessibility: {}, cls: {}, screenshots: [] };
const browser = await chromium.launch({ headless: true });
try {
  await runCls(browser, report);
  await runPrivacy(browser, report);
  await runResponsive(browser, report);
  await runNoJs(browser, report);
  await runManuscriptFiles(browser, report);
  await runAccessibility(browser, report);
  await runScreenshots(browser, report);
  await fs.writeFile(path.join(OUT, 'browser-qa-report.json'), JSON.stringify(report, null, 2));
  console.log('TOOLS BROWSER QA: OK');
} finally {
  await browser.close();
}
