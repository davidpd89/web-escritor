import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const SITE = 'https://davidportodiaz.com';
const OUT = path.resolve('qa-artifacts/cuaderno');

const pages = [
  { key: 'index', route: '/cuaderno/', kind: 'index' },
  { key: 'feria', route: '/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/', kind: 'article' },
  { key: 'portal', route: '/cuaderno/que-es-el-portal-fantasy/', kind: 'article' },
  { key: 'comparativa', route: '/cuaderno/portal-fantasy-vs-fantasia-epica/', kind: 'article' },
  { key: 'magia', route: '/cuaderno/sistema-de-magia-noveris/', kind: 'article' },
  { key: 'fantasia', route: '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/', kind: 'article' },
  { key: 'libros', route: '/cuaderno/libros-fantasia-juvenil-espanola-2025-2026/', kind: 'article' },
  { key: 'worldbuilding', route: '/cuaderno/worldbuilding-noveris-ciudad-magica/', kind: 'article' },
];

const viewports = [
  { width: 320, height: 900 },
  { width: 390, height: 900 },
  { width: 768, height: 1000 },
  { width: 1024, height: 900 },
  { width: 1440, height: 1000 },
  { width: 1728, height: 1000 },
  { width: 844, height: 390 },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
const inventory = {};
const report = { pages: {}, responsive: {}, keyboard: {}, zoom: {}, textSpacing: {}, noJs: {}, reducedMotion: {}, share: {}, print: {} };

function norm(value = '') {
  return String(value).replace(/\s+/g, ' ').trim();
}

function flattenTypes(node, out = []) {
  if (Array.isArray(node)) {
    for (const item of node) flattenTypes(item, out);
    return out;
  }
  if (!node || typeof node !== 'object') return out;
  const type = node['@type'];
  if (typeof type === 'string') out.push(type);
  else if (Array.isArray(type)) out.push(...type.filter(v => typeof v === 'string'));
  for (const value of Object.values(node)) flattenTypes(value, out);
  return out;
}

function flattenNodes(node, out = []) {
  if (Array.isArray(node)) {
    for (const item of node) flattenNodes(item, out);
    return out;
  }
  if (!node || typeof node !== 'object') return out;
  out.push(node);
  if (Array.isArray(node['@graph'])) flattenNodes(node['@graph'], out);
  return out;
}

async function makeContext({ viewport = { width: 1440, height: 1000 }, javaScriptEnabled = true, reducedMotion = 'reduce', initScript } = {}) {
  const context = await browser.newContext({ viewport, javaScriptEnabled, reducedMotion });
  await context.route('**://gc.zgo.at/**', route => route.fulfill({ status: 200, contentType: 'application/javascript', body: '' }));
  await context.route('**://*.goatcounter.com/**', route => route.fulfill({ status: 204, body: '' }));
  if (javaScriptEnabled) {
    await context.addInitScript(() => {
      window.__qaCLS = 0;
      new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) window.__qaCLS += entry.value;
        }
      }).observe({ type: 'layout-shift', buffered: true });
    });
    if (initScript) await context.addInitScript(initScript);
  }
  return context;
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

async function applyInspectorStyles(context, page, cssText) {
  const cdp = await context.newCDPSession(page);
  await cdp.send('Page.enable');
  await cdp.send('DOM.enable');
  await cdp.send('CSS.enable');
  const { frameTree } = await cdp.send('Page.getFrameTree');
  const { styleSheetId } = await cdp.send('CSS.createStyleSheet', { frameId: frameTree.frame.id });
  await cdp.send('CSS.setStyleSheetText', { styleSheetId, text: cssText });
}

async function noOverflow(page, label) {
  const data = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  assert.ok(data.scrollWidth <= data.clientWidth + 1, `${label}: overflow ${data.scrollWidth}/${data.clientWidth}`);
}

async function extractInventory(page) {
  return page.evaluate(() => {
    const norm = value => String(value || '').replace(/\s+/g, ' ').trim();
    const scripts = [...document.querySelectorAll('script[type="application/ld+json"]')];
    const parsed = scripts.map(script => JSON.parse(script.textContent));
    const nodes = [];
    const visit = value => {
      if (Array.isArray(value)) return value.forEach(visit);
      if (!value || typeof value !== 'object') return;
      nodes.push(value);
      if (Array.isArray(value['@graph'])) value['@graph'].forEach(visit);
    };
    parsed.forEach(visit);
    const types = [];
    for (const node of nodes) {
      const t = node['@type'];
      if (typeof t === 'string') types.push(t);
      else if (Array.isArray(t)) types.push(...t.filter(v => typeof v === 'string'));
    }
    const article = nodes.find(node => ['Article', 'BlogPosting', 'NewsArticle'].includes(node['@type']));
    const main = document.querySelector('main');
    const hrefs = [...(main?.querySelectorAll('a[href]') || [])].map(a => a.getAttribute('href'));
    return {
      title: document.title,
      description: document.querySelector('meta[name="description"]')?.content || '',
      canonical: document.querySelector('link[rel="canonical"]')?.href || '',
      h1: [...document.querySelectorAll('h1')].map(h => norm(h.textContent)),
      headings: [...(main?.querySelectorAll('h2,h3') || [])].map(h => ({ level: h.tagName.toLowerCase(), id: h.id || '', text: norm(h.textContent) })),
      paragraphCount: main?.querySelectorAll('p').length || 0,
      mainText: norm(main?.innerText || ''),
      internalHrefs: [...new Set(hrefs.filter(href => href && (href.startsWith('/') || href.startsWith('#'))))].sort(),
      externalHrefs: [...new Set(hrefs.filter(href => /^https?:\/\//i.test(href)))].sort(),
      jsonLdTypes: [...new Set(types)].sort(),
      datePublished: article?.datePublished || '',
      dateModified: article?.dateModified || '',
      articleId: article?.['@id'] || '',
    };
  });
}

async function validateCore(spec, page) {
  const data = await extractInventory(page);
  inventory[spec.key] = data;
  assert.ok(data.title, `${spec.key}: title vacío`);
  assert.ok(data.description, `${spec.key}: description vacía`);
  assert.equal(data.canonical, SITE + spec.route, `${spec.key}: canonical`);
  assert.equal(data.h1.length, 1, `${spec.key}: debe existir un H1`);
  assert.ok(data.h1[0], `${spec.key}: H1 vacío`);
  assert.ok(data.mainText.length > 180, `${spec.key}: cuerpo visible insuficiente`);
  const ids = data.headings.map(h => h.id).filter(Boolean);
  assert.equal(new Set(ids).size, ids.length, `${spec.key}: heading ids duplicados`);
  if (spec.kind === 'index') {
    assert.ok(data.jsonLdTypes.includes('CollectionPage'), 'index: falta CollectionPage');
  } else {
    assert.ok(data.jsonLdTypes.includes('Article'), `${spec.key}: falta Article`);
    assert.ok(data.jsonLdTypes.includes('BreadcrumbList'), `${spec.key}: falta BreadcrumbList`);
    assert.ok(data.datePublished, `${spec.key}: falta datePublished`);
    assert.ok(data.dateModified, `${spec.key}: falta dateModified`);
    assert.equal(data.articleId, SITE + spec.route + '#article', `${spec.key}: @id Article`);
  }

  const parsed = await page.locator('script[type="application/ld+json"]').evaluateAll(nodes => nodes.map(node => JSON.parse(node.textContent)));
  assert.ok(parsed.length >= 1, `${spec.key}: JSON-LD ausente`);

  const duplicateIds = await page.evaluate(() => {
    const ids = [...document.querySelectorAll('[id]')].map(el => el.id).filter(Boolean);
    return ids.filter((id, index) => ids.indexOf(id) !== index);
  });
  assert.deepEqual(duplicateIds, [], `${spec.key}: IDs DOM duplicados`);

  const toc = page.locator('[data-article-toc]');
  if (await toc.count()) {
    const missing = await toc.locator('a[href^="#"]').evaluateAll(links => links.map(link => link.getAttribute('href')).filter(href => !document.querySelector(href)));
    assert.deepEqual(missing, [], `${spec.key}: TOC apunta a destino inexistente`);
  }

  const faqVisible = await page.locator('.article-faq details').evaluateAll(details => details.map(item => ({
    q: item.querySelector('summary')?.textContent.replace(/\s+/g, ' ').trim() || '',
    a: item.querySelector('p')?.textContent.replace(/\s+/g, ' ').trim() || '',
  })));
  const faqSchema = flattenNodes(parsed).find(node => node['@type'] === 'FAQPage');
  if (faqVisible.length || faqSchema) {
    assert.ok(faqSchema, `${spec.key}: FAQ visible sin FAQPage`);
    const schemaPairs = (faqSchema.mainEntity || []).map(item => ({ q: norm(item.name), a: norm(item.acceptedAnswer?.text) }));
    assert.deepEqual(schemaPairs, faqVisible.map(item => ({ q: norm(item.q), a: norm(item.a) })), `${spec.key}: FAQ visible/schema no coincide 1:1`);
  }

  const unsafeBlank = await page.locator('a[target="_blank"]').evaluateAll(links => links.filter(a => !/\bnoopener\b/.test(a.rel)).map(a => a.href));
  assert.deepEqual(unsafeBlank, [], `${spec.key}: target=_blank sin noopener`);

  const imageProblems = await page.locator('main img').evaluateAll(images => images.map(img => ({
    src: img.getAttribute('src'),
    alt: img.getAttribute('alt'),
    width: img.getAttribute('width'),
    height: img.getAttribute('height'),
    loading: img.getAttribute('loading'),
    top: img.getBoundingClientRect().top + window.scrollY,
  })).filter(item => item.alt === null || !item.width || !item.height));
  assert.deepEqual(imageProblems, [], `${spec.key}: imágenes sin alt/dimensiones`);

  const cls = await page.evaluate(() => window.__qaCLS || 0);
  assert.ok(cls <= 0.1, `${spec.key}: CLS ${cls}`);
  await noOverflow(page, spec.key);
  report.pages[spec.key] = { cls, h1: data.h1[0], paragraphs: data.paragraphCount, faq: faqVisible.length };
}

async function checkInternalLinks(spec, page, context) {
  const hrefs = await page.locator('main a[href]').evaluateAll(links => [...new Set(links.map(a => a.getAttribute('href')).filter(h => h && h.startsWith('/') && !h.startsWith('//'))) ]);
  const failures = [];
  for (const href of hrefs) {
    const url = new URL(href, BASE);
    url.hash = '';
    const response = await context.request.get(url.href, { maxRedirects: 3 });
    if (response.status() >= 400) failures.push(`${href}:${response.status()}`);
  }
  assert.deepEqual(failures, [], `${spec.key}: enlaces internos rotos`);
}

async function baseAudit() {
  for (const spec of pages) {
    const { context, page } = await open(spec);
    await validateCore(spec, page);
    await checkInternalLinks(spec, page, context);
    await context.close();
  }
  await fs.writeFile(path.join(OUT, 'inventory.json'), JSON.stringify(inventory, null, 2));
}

async function responsiveAudit() {
  for (const viewport of viewports) {
    const key = `${viewport.width}x${viewport.height}`;
    report.responsive[key] = {};
    for (const spec of pages) {
      const { context, page } = await open(spec, { viewport });
      await noOverflow(page, `${spec.key} ${key}`);
      const h1Box = await page.locator('h1').boundingBox();
      assert.ok(h1Box && h1Box.width > 0 && h1Box.height > 0, `${spec.key} ${key}: H1 no visible`);
      if (spec.kind === 'article') {
        const toc = page.locator('[data-article-toc]');
        if (await toc.count() && viewport.width <= 767) {
          const box = await toc.boundingBox();
          assert.ok(!box || box.height < viewport.height * 0.55, `${spec.key} ${key}: TOC ocupa demasiado alto`);
        }
        const tableOverflow = await page.locator('.article-prose table').evaluateAll(tables => tables.map(table => ({
          width: table.getBoundingClientRect().width,
          viewport: document.documentElement.clientWidth,
        })).filter(item => item.width > item.viewport + 1));
        assert.deepEqual(tableOverflow, [], `${spec.key} ${key}: tabla desborda página`);
      }
      report.responsive[key][spec.key] = true;
      await context.close();
    }
  }
}

async function noJsAudit() {
  for (const spec of pages) {
    const { context, page } = await open(spec, { viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    await noOverflow(page, `${spec.key} no-js`);
    assert.equal(await page.locator('h1').count(), 1, `${spec.key} no-js: H1`);
    assert.ok((await page.locator('main').innerText()).length > 180, `${spec.key} no-js: contenido`);
    assert.ok(await page.locator('main a[href]').count() > 0, `${spec.key} no-js: enlaces`);
    const missing = await page.locator('[data-article-toc] a[href^="#"]').evaluateAll(links => links.map(link => link.getAttribute('href')).filter(href => !document.querySelector(href)));
    assert.deepEqual(missing, [], `${spec.key} no-js: TOC`);
    report.noJs[spec.key] = true;
    await context.close();
  }
}

async function keyboardAudit() {
  const spec = pages.find(p => p.key === 'portal');
  const { context, page } = await open(spec);
  assert.equal(await page.locator('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])').count(), 0, 'teclado: tabindex positivo');
  await page.keyboard.press('Tab');
  assert.equal(await page.evaluate(() => document.activeElement?.classList.contains('skip-link')), true, 'teclado: skip link no es primer foco');
  await page.keyboard.press('Enter');
  assert.equal(new URL(page.url()).hash, '#contenido', 'teclado: skip link no salta a contenido');
  assert.equal(await page.locator('[data-share-url]:visible').count(), 1, 'teclado: compartir no disponible con JS');
  assert.equal(await page.locator('[data-print]:visible').count(), 1, 'teclado: imprimir no disponible con JS');
  report.keyboard.portal = true;
  await context.close();
}

async function zoomAudit() {
  for (const spec of [pages[0], pages.find(p => p.key === 'portal')]) {
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

async function textSpacingAudit() {
  const css = `*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}`;
  for (const spec of [pages[0], pages.find(p => p.key === 'portal')]) {
    const { context, page } = await open(spec, { viewport: { width: 320, height: 900 } });
    await applyInspectorStyles(context, page, css);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await noOverflow(page, `${spec.key} text-spacing`);
    report.textSpacing[spec.key] = true;
    await context.close();
  }
}

async function reducedMotionAudit() {
  for (const spec of [pages[0], pages.find(p => p.key === 'portal')]) {
    const { context, page } = await open(spec, { reducedMotion: 'reduce' });
    await page.waitForTimeout(100);
    const running = await page.evaluate(() => document.getAnimations().filter(animation => animation.playState === 'running').length);
    assert.equal(running, 0, `${spec.key}: animaciones activas con reduced motion`);
    report.reducedMotion[spec.key] = true;
    await context.close();
  }
}

async function shareAudit() {
  const spec = pages.find(p => p.key === 'portal');
  const expected = SITE + spec.route;
  {
    const { context, page } = await open(spec, { initScript: () => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: async payload => { window.__shared = payload; } });
    }});
    await page.click('[data-share-url]');
    const shared = await page.evaluate(() => window.__shared);
    assert.equal(shared?.url, expected, 'share: Web Share URL');
    assert.equal(norm(await page.locator('#article-share-status').innerText()), 'Compartido.', 'share: feedback Web Share');
    report.share.webShare = true;
    await context.close();
  }
  {
    const { context, page } = await open(spec, { initScript: () => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
      Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async text => { window.__copied = text; } } });
    }});
    await page.click('[data-share-url]');
    assert.equal(await page.evaluate(() => window.__copied), expected, 'share: fallback clipboard');
    assert.equal(norm(await page.locator('#article-share-status').innerText()), 'Enlace copiado.', 'share: feedback clipboard');
    report.share.fallback = true;
    await context.close();
  }
}

async function printAudit() {
  const spec = pages.find(p => p.key === 'portal');
  const { context, page } = await open(spec, { initScript: () => { window.print = () => { window.__printed = (window.__printed || 0) + 1; }; } });
  await page.click('[data-print]');
  assert.equal(await page.evaluate(() => window.__printed), 1, 'print: botón no llama window.print');
  await page.emulateMedia({ media: 'print' });
  const visible = await page.evaluate(() => ({
    header: getComputedStyle(document.querySelector('.site-header')).display,
    footer: getComputedStyle(document.querySelector('.site-footer')).display,
    toc: getComputedStyle(document.querySelector('.article-toc')).display,
    prose: getComputedStyle(document.querySelector('.article-prose')).display,
    articleEnd: getComputedStyle(document.querySelector('.article-end')).display,
  }));
  assert.equal(visible.header, 'none', 'print: header debe ocultarse');
  assert.equal(visible.footer, 'none', 'print: footer debe ocultarse');
  assert.equal(visible.toc, 'none', 'print: TOC debe ocultarse');
  assert.notEqual(visible.prose, 'none', 'print: prosa oculta');
  assert.equal(visible.articleEnd, 'none', 'print: cierre de navegación debe ocultarse');
  await page.screenshot({ path: path.join(OUT, 'article-print.png'), fullPage: true });
  report.print.portal = true;
  await context.close();
}

async function screenshots() {
  const shots = [
    [pages[0], { width: 1440, height: 1000 }, 'cuaderno-1440.png'],
    [pages[0], { width: 390, height: 900 }, 'cuaderno-390.png'],
    [pages.find(p => p.key === 'portal'), { width: 1440, height: 1000 }, 'article-long-1440.png'],
    [pages.find(p => p.key === 'portal'), { width: 390, height: 900 }, 'article-long-390.png'],
    [pages.find(p => p.key === 'feria'), { width: 1440, height: 1000 }, 'feria-1440.png'],
  ];
  for (const [spec, viewport, file] of shots) {
    const { context, page } = await open(spec, { viewport });
    await page.screenshot({ path: path.join(OUT, file), fullPage: true });
    await context.close();
  }
}

try {
  await baseAudit();
  await responsiveAudit();
  await noJsAudit();
  await keyboardAudit();
  await zoomAudit();
  await textSpacingAudit();
  await reducedMotionAudit();
  await shareAudit();
  await printAudit();
  await screenshots();
  await fs.writeFile(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log('CUADERNO QA PASS');
} catch (error) {
  await fs.writeFile(path.join(OUT, 'failure.txt'), `${error?.stack || error}\n`);
  throw error;
} finally {
  await browser.close();
}
