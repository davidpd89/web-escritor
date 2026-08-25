import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const SITE = 'https://davidportodiaz.com';
const OUT = path.resolve(process.env.QA_OUT || 'qa-artifacts/cuaderno-topics');

const routes = [
  { key: 'topics-index', route: '/cuaderno/temas/', kind: 'index' },
  { key: 'portal-collection', route: '/cuaderno/temas/fantasia-de-portales/', kind: 'collection' },
];

const expectedItems = [
  {
    position: 1,
    href: '/cuaderno/que-es-el-portal-fantasy/',
    title: 'Qué es el portal fantasy: guía para lectores en español',
  },
  {
    position: 2,
    href: '/cuaderno/portal-fantasy-vs-fantasia-epica/',
    title: 'Portal fantasy vs. fantasía épica: ¿cuál es la diferencia?',
  },
  {
    position: 3,
    href: '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/',
    title: 'Fantasía juvenil española con portales y magia con coste',
  },
];

const viewports = [
  { width: 320, height: 900 },
  { width: 390, height: 900 },
  { width: 768, height: 1024 },
  { width: 1024, height: 900 },
  { width: 1440, height: 900 },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const report = { core: {}, responsive: {}, noJs: {}, zoom: {}, textSpacing: {}, reducedMotion: {} };

const norm = value => String(value || '').replace(/\s+/g, ' ').trim();

function flattenNodes(value, out = []) {
  if (Array.isArray(value)) {
    value.forEach(item => flattenNodes(item, out));
    return out;
  }
  if (!value || typeof value !== 'object') return out;
  out.push(value);
  if (Array.isArray(value['@graph'])) value['@graph'].forEach(item => flattenNodes(item, out));
  return out;
}

async function makeContext({ viewport = { width: 1440, height: 900 }, javaScriptEnabled = true, reducedMotion = 'no-preference' } = {}) {
  return browser.newContext({ viewport, javaScriptEnabled, reducedMotion });
}

async function open(spec, options = {}) {
  const context = await makeContext(options);
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', message => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', error => pageErrors.push(error.message));
  const response = await page.goto(BASE + spec.route, { waitUntil: 'networkidle' });
  assert.equal(response?.status(), 200, `${spec.key}: HTTP ${response?.status()}`);
  if (options.javaScriptEnabled !== false) {
    assert.deepEqual(pageErrors, [], `${spec.key}: pageerror`);
    assert.deepEqual(consoleErrors, [], `${spec.key}: console errors`);
  }
  return { context, page };
}

async function noOverflow(page, label) {
  const dims = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  assert.ok(dims.scrollWidth <= dims.clientWidth + 1, `${label}: overflow ${dims.scrollWidth}/${dims.clientWidth}`);
}

async function jsonLd(page) {
  return page.locator('script[type="application/ld+json"]').evaluateAll(nodes => nodes.map(node => JSON.parse(node.textContent)));
}

async function assertCore(spec, page) {
  assert.equal(await page.locator('h1').count(), 1, `${spec.key}: H1 único`);
  assert.equal(await page.locator('main[data-family="cuaderno-topics"]').count(), 1, `${spec.key}: family root`);
  assert.equal(await page.locator('link[href="/assets/v1-cuaderno-topics.css"]').count(), 1, `${spec.key}: CSS family`);
  assert.equal(await page.locator('link[href$="/v1-tools.css"]').count(), 0, `${spec.key}: no v1-tools.css`);

  const badClasses = await page.locator('[class]').evaluateAll(nodes => [...new Set(nodes.flatMap(node => [...node.classList]).filter(cls => cls.startsWith('tool-') || cls === 'id-card' || cls === 'id-cards'))]);
  assert.deepEqual(badClasses, [], `${spec.key}: clases de Herramientas/ID cards residuales`);

  const cuadernoExplore = page.locator('.explore-row[href="/cuaderno/"][data-preview="notebook-hub"]');
  assert.equal(await cuadernoExplore.count(), 1, `${spec.key}: Cuaderno accesible desde Explorar`);
  assert.equal(norm(await page.locator('[data-preview-label]').textContent()), 'Cuaderno', `${spec.key}: preview label`);
  assert.equal(norm(await page.locator('[data-preview-copy]').textContent()), 'Artículos, crónicas y piezas editoriales.', `${spec.key}: preview copy`);

  const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute('content');
  assert.ok(csp?.includes("connect-src 'none'"), `${spec.key}: CSP connect-src`);
  assert.ok(csp?.includes("style-src 'self'"), `${spec.key}: CSP style-src`);
  assert.ok(csp?.includes("script-src 'self'"), `${spec.key}: CSP script-src`);
  assert.ok(!csp?.includes('unsafe-inline'), `${spec.key}: CSP no unsafe-inline`);
  assert.equal(await page.locator('[style]').count(), 0, `${spec.key}: no style inline`);

  const inlineScripts = await page.locator('script:not([src])').evaluateAll(nodes => nodes.map(node => node.getAttribute('type') || ''));
  assert.deepEqual(inlineScripts, ['application/ld+json'], `${spec.key}: solo JSON-LD inline`);

  const breadcrumb = page.locator('.cuaderno-topics-breadcrumb');
  assert.equal(await breadcrumb.count(), 1, `${spec.key}: breadcrumb`);
  assert.equal(await breadcrumb.locator('li[aria-current="page"]').count(), 1, `${spec.key}: breadcrumb current`);

  const mainHeadings = await page.locator('main h1, main h2, main h3').evaluateAll(nodes => nodes.map(node => Number(node.tagName.slice(1))));
  assert.equal(mainHeadings[0], 1, `${spec.key}: heading empieza en H1`);
  for (let i = 1; i < mainHeadings.length; i += 1) {
    assert.ok(mainHeadings[i] <= mainHeadings[i - 1] + 1, `${spec.key}: salto de heading ${mainHeadings[i - 1]}→${mainHeadings[i]}`);
  }

  const schemas = await jsonLd(page);
  const nodes = flattenNodes(schemas);
  assert.ok(nodes.some(node => node['@type'] === 'CollectionPage'), `${spec.key}: CollectionPage`);
  assert.ok(nodes.some(node => node['@type'] === 'BreadcrumbList'), `${spec.key}: BreadcrumbList`);

  if (spec.kind === 'index') {
    assert.equal(documentTitle(await page.title()), 'Colecciones del Cuaderno | David Porto Díaz', `${spec.key}: title`);
    assert.equal(await page.locator('.cuaderno-topics-ledger > li').count(), 1, `${spec.key}: una colección real`);
    assert.equal(norm(await page.locator('.cuaderno-topics-entry h2').textContent()), 'Fantasía de portales', `${spec.key}: colección`);
    assert.equal(norm(await page.locator('.cuaderno-topics-entry__meta').textContent()), 'Colección · 3 piezas', `${spec.key}: contador real`);
    assert.equal(await page.locator('.cuaderno-topics-entry h2 a').getAttribute('href'), `${SITE}/cuaderno/temas/fantasia-de-portales/`, `${spec.key}: href colección`);
  } else {
    const itemList = nodes.find(node => node['@type'] === 'ItemList');
    assert.ok(itemList, `${spec.key}: ItemList`);
    assert.equal(itemList.itemListOrder, 'https://schema.org/ItemListUnordered', `${spec.key}: ItemList semantics`);
    const schemaItems = itemList.itemListElement.map(item => ({ position: item.position, href: item.url.replace(SITE, ''), title: item.name }));
    assert.deepEqual(schemaItems, expectedItems, `${spec.key}: ItemList intacto`);

    const visible = await page.locator('.cuaderno-topic-step').evaluateAll(nodes => nodes.map((node, index) => ({
      position: index + 1,
      href: node.querySelector('h2 a')?.getAttribute('href'),
      title: String(node.querySelector('h2')?.textContent || '').replace(/\s+/g, ' ').trim(),
    })));
    assert.deepEqual(visible, expectedItems, `${spec.key}: orden visual = schema 1/2/3`);
    assert.equal(norm(await page.locator('.cuaderno-topic-revision').textContent()), 'Revisión de esta colección: 2026-08-21', `${spec.key}: fecha preservada`);

    for (const item of expectedItems) {
      const response = await page.context().request.get(BASE + item.href, { maxRedirects: 3 });
      assert.ok(response.status() < 400, `${spec.key}: ${item.href} HTTP ${response.status()}`);
    }
  }

  await noOverflow(page, spec.key);
  report.core[spec.key] = { h1: norm(await page.locator('h1').textContent()), headings: mainHeadings };
}

function documentTitle(value) {
  return norm(value);
}

async function coreAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec);
    await assertCore(spec, page);
    await context.close();
  }
}

async function responsiveAudit() {
  for (const viewport of viewports) {
    const key = `${viewport.width}x${viewport.height}`;
    report.responsive[key] = {};
    for (const spec of routes) {
      const { context, page } = await open(spec, { viewport });
      await noOverflow(page, `${spec.key} ${key}`);
      const h1 = await page.locator('h1').boundingBox();
      assert.ok(h1 && h1.width > 0 && h1.height > 0, `${spec.key} ${key}: H1 visible`);
      const footer = await page.locator('.site-footer').boundingBox();
      assert.ok(footer && footer.width > 0, `${spec.key} ${key}: footer visible`);
      report.responsive[key][spec.key] = { h1Width: h1.width };
      await context.close();
    }
  }
}

async function noJsAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec, { javaScriptEnabled: false, viewport: { width: 390, height: 900 } });
    assert.equal(await page.locator('main h1').count(), 1, `${spec.key}: no-JS H1`);
    if (spec.kind === 'index') assert.equal(await page.locator('.cuaderno-topics-entry').count(), 1, `${spec.key}: no-JS ledger`);
    else assert.equal(await page.locator('.cuaderno-topic-step').count(), 3, `${spec.key}: no-JS itinerary`);
    await noOverflow(page, `${spec.key} no-JS`);
    report.noJs[spec.key] = 'PASS';
    await context.close();
  }
}

async function zoomAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec, { viewport: { width: 390, height: 900 } });
    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
    await page.waitForTimeout(100);
    const scale = await page.evaluate(() => window.visualViewport?.scale || 1);
    assert.ok(scale >= 1.9, `${spec.key}: zoom 200% no aplicado`);
    await noOverflow(page, `${spec.key} zoom 200%`);
    report.zoom[spec.key] = scale;
    await context.close();
  }
}

async function injectTextSpacing(context, page) {
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { frameTree } = await cdp.send('Page.getFrameTree');
  const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
  await cdp.send('CSS.setStyleSheetText', {
    styleSheetId,
    text: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}',
  });
}

async function textSpacingAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec, { viewport: { width: 390, height: 900 } });
    await injectTextSpacing(context, page);
    await noOverflow(page, `${spec.key} text-spacing`);
    report.textSpacing[spec.key] = 'PASS';
    await context.close();
  }
}

async function reducedMotionAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec, { reducedMotion: 'reduce', viewport: { width: 390, height: 900 } });
    await noOverflow(page, `${spec.key} reduced-motion`);
    report.reducedMotion[spec.key] = 'PASS';
    await context.close();
  }
}

async function focusAudit() {
  for (const spec of routes) {
    const { context, page } = await open(spec, { viewport: { width: 390, height: 900 } });
    const expected = await page.locator('main :is(.cuaderno-topics-entry h2 a,.cuaderno-topic-step h2 a,.cuaderno-topics-link)').evaluateAll(links => links.map(link => link.getAttribute('href')));
    assert.ok(expected.length >= 1, `${spec.key}: enlaces editoriales`);
    const seen = new Set();
    for (let i = 0; i < 120 && seen.size < expected.length; i += 1) {
      await page.keyboard.press('Tab');
      const active = await page.evaluate(() => {
        const el = document.activeElement;
        if (!(el instanceof HTMLAnchorElement)) return null;
        const style = getComputedStyle(el);
        return { href: el.getAttribute('href'), outlineStyle: style.outlineStyle, outlineWidth: style.outlineWidth };
      });
      if (!active || !expected.includes(active.href)) continue;
      assert.notEqual(active.outlineStyle, 'none', `${spec.key}: focus-visible ${active.href}`);
      assert.notEqual(active.outlineWidth, '0px', `${spec.key}: focus-visible width ${active.href}`);
      seen.add(active.href);
    }
    assert.deepEqual([...seen].sort(), [...new Set(expected)].sort(), `${spec.key}: todos los enlaces editoriales accesibles con Tab`);
    await context.close();
  }
}

async function screenshots() {
  for (const spec of routes) {
    for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 900 }]) {
      const { context, page } = await open(spec, { viewport });
      const name = `${spec.key}-${viewport.width}.png`;
      await page.screenshot({ path: path.join(OUT, name), fullPage: true });
      await context.close();
    }
  }
}

try {
  await coreAudit();
  await responsiveAudit();
  await noJsAudit();
  await zoomAudit();
  await textSpacingAudit();
  await reducedMotionAudit();
  await focusAudit();
  await screenshots();
  await fs.writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log('PASS cuaderno topics browser QA');
} finally {
  await browser.close();
}
