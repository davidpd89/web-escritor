import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT = process.cwd();
const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/content-parity-manecillas';
fs.mkdirSync(path.join(ROOT, OUT), { recursive: true });

const read = file => fs.readFileSync(path.join(ROOT, file), 'utf8');
const facts = JSON.parse(read('editorial-facts.json'));
const catalogHtml = read('libros/index.html');
const bookHtml = read('las-manecillas-del-recuerdo/index.html');
const fragmentsHtml = read('las-manecillas-del-recuerdo/fragmentos/index.html');
const shareJs = read('assets/manecillas-book.js');
const globalJs = read('script.js');

const manecillas = facts.books?.lasManecillasDelRecuerdo;
const samuel = facts.books?.samuelEntreMundos;
assert(manecillas, 'editorial-facts: falta books.lasManecillasDelRecuerdo');
assert(samuel, 'editorial-facts: falta books.samuelEntreMundos');
assert.equal(manecillas.purchaseUrl, null, 'purchaseUrl de Manecillas debe seguir null');
assert.equal(manecillas.format, 'Paperback', 'la autoridad actual debe confirmar Paperback');

function jsonLd(html) {
  return [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(match => JSON.parse(match[1]));
}
function flattenGraph(docs) {
  return docs.flatMap(doc => Array.isArray(doc['@graph']) ? doc['@graph'] : [doc]);
}
function hasType(node, type) {
  const value = node?.['@type'];
  return Array.isArray(value) ? value.includes(type) : value === type;
}
function hasOffer(value) {
  if (!value || typeof value !== 'object') return false;
  if (hasType(value, 'Offer') || Object.hasOwn(value, 'offers')) return true;
  return Object.values(value).some(hasOffer);
}

const catalogGraph = flattenGraph(jsonLd(catalogHtml));
const itemList = catalogGraph.find(node => hasType(node, 'ItemList'));
assert(itemList, 'catálogo: falta ItemList');
assert.equal(itemList.itemListElement?.length, 2, 'catálogo: deben existir exactamente dos libros públicos');
const catalogBooks = itemList.itemListElement.map(entry => entry.item);
assert.deepEqual(catalogBooks.map(book => book.name), [manecillas.title, samuel.title], 'catálogo: orden/jerarquía incorrecta');

const catManecillas = catalogBooks[0];
assert.equal(catManecillas.isbn, manecillas.isbn);
assert.equal(catManecillas.publisher?.name, manecillas.publisher);
assert.equal(catManecillas.numberOfPages, manecillas.numberOfPages);
assert.equal(catManecillas.datePublished, manecillas.publicationDate);
assert.equal(catManecillas.bookFormat, 'https://schema.org/Paperback');
assert.deepEqual(catManecillas.genre, manecillas.genres);
assert.match(catManecillas.image || '', /portada-las-manecillas-del-recuerdo-1024\.webp$/);
assert.equal(hasOffer(catManecillas), false, 'catálogo: Manecillas no puede tener Offer');

const catSamuel = catalogBooks[1];
assert.equal(catSamuel.isbn, samuel.isbn);
assert.equal(catSamuel.publisher?.name, samuel.publisher);
assert.equal(catSamuel.numberOfPages, samuel.numberOfPages);
assert.equal(String(catSamuel.datePublished), String(samuel.publicationYear));
assert.equal(catSamuel.bookFormat, 'https://schema.org/Paperback');
assert.match(catSamuel.image || '', /samuel-entre-mundos\.webp$/);

const bookGraph = flattenGraph(jsonLd(bookHtml));
const bookSchema = bookGraph.find(node => hasType(node, 'Book'));
assert(bookSchema, 'ficha: falta Book');
assert.equal(bookSchema.isbn, manecillas.isbn);
assert.equal(bookSchema.publisher?.name, manecillas.publisher);
assert.equal(bookSchema.numberOfPages, manecillas.numberOfPages);
assert.equal(bookSchema.datePublished, manecillas.publicationDate);
assert.equal(bookSchema.bookFormat, 'https://schema.org/Paperback');
assert.deepEqual(bookSchema.genre, manecillas.genres);
assert.equal(hasOffer(bookSchema), false, 'ficha: no puede haber Offer sin purchaseUrl');
assert(!/amazon\.es|amazon\.com/i.test(bookHtml), 'ficha Manecillas: no debe contener retailer externo/Amazon');
assert(!/data-purchase|comprar en amazon|comprar ahora/i.test(bookHtml), 'ficha Manecillas: no debe simular CTA comercial');
assert(!/book-crosspromo/.test(bookHtml), 'ficha Manecillas: no debe duplicar Samuel como upsell grande');
assert(/<dt>Formato<\/dt><dd>Tapa blanda<\/dd>/.test(bookHtml), 'ficha: falta formato autorizado visible');
assert(/PVP editorial/.test(bookHtml), 'ficha: el precio debe identificarse como dato editorial');
assert(/Publicada el 3 de septiembre de 2026/.test(bookHtml), 'ficha: falta copy estable de publicación');
assert(!/próximamente|en proceso de publicación/i.test(bookHtml), 'ficha: queda copy prelaunch');
assert(!/David Porto Díaz publica <em>Las manecillas/.test(catalogHtml), 'catálogo: queda copy verbal prelaunch');
assert(/publicada el 3 de septiembre de 2026/.test(catalogHtml), 'catálogo: falta estado publicado estable');

for (const anchor of ['aviso', 'muestra', 'sinopsis-editorial', 'newsletter-manecillas']) {
  assert(new RegExp(`id=["']${anchor}["']`).test(bookHtml), `ficha: se perdió anchor histórico #${anchor}`);
}
assert(/data-newsletter-source="manecillas"/.test(bookHtml), 'newsletter: se perdió source manecillas');
assert(/imagesrcset=/.test(bookHtml) && /imagesizes=/.test(bookHtml), 'portada: preload no es responsive');
assert(/data-book-share/.test(bookHtml), 'ficha: falta acción share/copy progresiva');
assert(!/\bfetch\s*\(/.test(shareJs), 'share local no debe hacer fetch');
assert(/STAGING_HOSTNAMES/.test(globalJs) && /david-porto-preview\.davidpd89\.workers\.dev/.test(globalJs), 'newsletter: se perdió safe mode de staging global');

const fragmentGraph = flattenGraph(jsonLd(fragmentsHtml));
const collection = fragmentGraph.find(node => hasType(node, 'Collection'));
assert.equal(collection?.collectionSize, 3, 'fragmentos: Collection debe contener 3 piezas');
const fragmentIds = ['fragmento-1', 'fragmento-2', 'fragmento-3'];
for (const id of fragmentIds) {
  assert(new RegExp(`id=["']${id}["']`).test(fragmentsHtml), `fragmentos: falta #${id}`);
  assert(fragmentGraph.some(node => node['@id']?.endsWith(`#${id}`)), `fragmentos: schema no contiene #${id}`);
}
assert.equal((fragmentsHtml.match(/class="excerpt-field"/g) || []).length, 3, 'fragmentos: deben existir exactamente 3 excerpt-field');

const report = {
  authority: {
    schemaVersion: facts.schemaVersion,
    lastReviewed: facts.lastReviewed,
    manecillasKey: 'lasManecillasDelRecuerdo',
    samuelKey: 'samuelEntreMundos',
    purchaseUrl: manecillas.purchaseUrl
  },
  schema: { catalogItems: 2, manecillasOffer: false, bookFormat: true, fragmentCollection: 3 },
  viewports: {},
  noJs: {},
  accessibility: {},
  navigation: {},
  share: {},
  consoleErrors: []
};
const writeReport = () => fs.writeFileSync(path.join(ROOT, OUT, 'content-parity-manecillas-report.json'), JSON.stringify(report, null, 2));
writeReport();

function watch(page, label) {
  const pageErrors = [];
  const consoleErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  return () => {
    assert.deepEqual(pageErrors, [], `${label}: pageerror ${pageErrors.join(' | ')}`);
    const appErrors = consoleErrors.filter(text => !/Failed to load resource/i.test(text));
    assert.deepEqual(appErrors, [], `${label}: console error ${appErrors.join(' | ')}`);
    report.consoleErrors.push({ label, count: appErrors.length });
  };
}

async function noOverflow(page, label) {
  const dimensions = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth,
    viewport: document.documentElement.clientWidth
  }));
  assert(dimensions.document <= dimensions.viewport + 1, `${label}: overflow ${dimensions.document}/${dimensions.viewport}`);
}

async function targetBelowHeader(page, id, label) {
  const position = await page.evaluate(targetId => {
    const target = document.getElementById(targetId);
    const heading = target?.matches('span') ? target.parentElement?.querySelector('h2') : target?.querySelector?.('h2') || target;
    const header = document.querySelector('[data-header]');
    return { top: heading?.getBoundingClientRect().top ?? -1, header: header?.getBoundingClientRect().bottom ?? 0 };
  }, id);
  assert(position.top >= position.header - 1, `${label}: target oculto por header (${position.top} < ${position.header})`);
}

const pages = [
  { key: 'catalog', url: '/libros/' },
  { key: 'book', url: '/las-manecillas-del-recuerdo/' },
  { key: 'fragments', url: '/las-manecillas-del-recuerdo/fragmentos/' }
];
const viewports = [
  { width: 320, height: 900 },
  { width: 390, height: 900 },
  { width: 768, height: 1000 },
  { width: 1024, height: 900 },
  { width: 1440, height: 1000 },
  { width: 1728, height: 1000 },
  { width: 844, height: 390 }
];

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  for (const viewport of viewports) {
    const viewportKey = `${viewport.width}x${viewport.height}`;
    report.viewports[viewportKey] = {};
    for (const route of pages) {
      const context = await browser.newContext({ viewport, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const verifyErrors = watch(page, `${route.key}-${viewportKey}`);
      await page.goto(`${ORIGIN}${route.url}`, { waitUntil: 'load' });
      await noOverflow(page, `${route.key}-${viewportKey}`);
      assert(await page.locator('main').isVisible(), `${route.key}: main no visible`);
      assert(await page.locator('h1').isVisible(), `${route.key}: h1 no visible`);
      verifyErrors();
      report.viewports[viewportKey][route.key] = { overflow: false, pageerror: 0 };
      await context.close();
    }
  }

  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'catalog-hierarchy');
    await page.goto(`${ORIGIN}/libros/`, { waitUntil: 'load' });
    const stages = page.locator('.books-stage');
    assert.equal(await stages.count(), 2, 'catálogo browser: deben existir exactamente 2 obras visibles');
    assert.match(await stages.nth(0).innerText(), /Las manecillas del recuerdo/);
    assert.match(await stages.nth(1).innerText(), /Samuel entre mundos/);
    const visibleMain = await page.locator('main').innerText();
    assert(!/Dónde empieza la jaula|PIEL/i.test(visibleMain), 'catálogo: fuga de obra gated');
    assert(await page.locator('a[href="/libros/samuel-entre-mundos/"]').count() > 0, 'Samuel dejó de ser accesible');
    verifyErrors();
    report.navigation.catalogHierarchy = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'book-deep-links');
    for (const id of ['aviso', 'muestra', 'sinopsis-editorial', 'newsletter-manecillas']) {
      await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/#${id}`, { waitUntil: 'load' });
      assert.equal(new URL(page.url()).hash, `#${id}`);
      await targetBelowHeader(page, id, `#${id}`);
    }
    verifyErrors();
    report.navigation.historicalAnchors = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'explore');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    const trigger = page.locator('[data-explore-open]');
    await trigger.focus();
    await page.keyboard.press('Enter');
    await page.locator('[data-explore-dialog]').waitFor({ state: 'visible' });
    assert.equal(await trigger.getAttribute('aria-expanded'), 'true');
    await page.keyboard.press('Escape');
    await page.locator('[data-explore-dialog]').waitFor({ state: 'hidden' });
    assert.equal(await trigger.getAttribute('aria-expanded'), 'false');
    verifyErrors();
    report.navigation.exploreKeyboard = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
    await context.addInitScript(() => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: async data => { window.__qaShared = data; } });
    });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'share');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    const share = page.locator('[data-book-share]');
    await share.waitFor({ state: 'visible' });
    await share.click();
    const shared = await page.evaluate(() => window.__qaShared);
    assert.equal(shared?.url, 'https://davidportodiaz.com/las-manecillas-del-recuerdo/');
    assert.match(shared?.title || '', /Las manecillas del recuerdo/);
    verifyErrors();
    report.share.native = true;
    await context.close();
  }

  for (const route of pages) {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${route.url}`, { waitUntil: 'load' });
    await noOverflow(page, `no-js-${route.key}`);
    assert(await page.locator('main').isVisible(), `no-JS ${route.key}: main no visible`);
    if (route.key === 'catalog') {
      assert.equal(await page.locator('.books-stage').count(), 2);
      assert(await page.locator('a[href="/las-manecillas-del-recuerdo/"]').count() > 0);
      assert(await page.locator('a[href="/libros/samuel-entre-mundos/"]').count() > 0);
    }
    if (route.key === 'book') {
      assert(await page.locator('#sinopsis').isVisible());
      assert(await page.locator('#disponibilidad').isVisible());
      assert(await page.locator('#newsletter-manecillas').isVisible());
      assert(await page.locator('[data-book-share]').isHidden(), 'no-JS: share progresivo no debe fingir funcionalidad');
    }
    if (route.key === 'fragments') {
      assert.equal(await page.locator('.excerpt-field').count(), 3);
      assert.equal(await page.locator('[data-fragment-index] a').count(), 3);
      assert.equal(await page.locator('.fragment-pager__link').count(), 5);
    }
    report.noJs[route.key] = true;
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 320, height: 900 } });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'a11y-reflow');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => ({ tag: document.activeElement?.tagName, text: document.activeElement?.textContent?.trim() }));
    assert.equal(focused.tag, 'A', 'Tab inicial debe alcanzar el skip link');
    const focusStyle = await page.locator(':focus').evaluate(el => {
      const style = getComputedStyle(el);
      return { outline: style.outlineStyle, width: parseFloat(style.outlineWidth) || 0 };
    });
    assert(focusStyle.outline !== 'none' && focusStyle.width >= 2, 'focus visible insuficiente');

    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 2 });
    await page.waitForTimeout(100);
    await noOverflow(page, 'zoom-200-book');
    assert(await page.locator('h1').isVisible());
    await cdp.send('Emulation.setPageScaleFactor', { pageScaleFactor: 1 });

    await page.addStyleTag({ content: `html *{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important} p{margin-bottom:2em!important}` });
    await page.waitForTimeout(100);
    await noOverflow(page, 'text-spacing-320-book');
    verifyErrors();
    report.accessibility = { keyboard: true, focusVisible: focusStyle, zoom200: true, textSpacing320: true };
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 1024, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    const verifyErrors = watch(page, 'reduced-print');
    await page.goto(`${ORIGIN}/las-manecillas-del-recuerdo/`, { waitUntil: 'load' });
    const transition = await page.locator('.primary-action').evaluate(el => parseFloat(getComputedStyle(el).transitionDuration) || 0);
    assert(transition <= 0.01, `reduced motion no respetado: ${transition}s`);
    await page.emulateMedia({ media: 'print', reducedMotion: 'reduce' });
    assert(await page.locator('h1').isVisible(), 'print: título desaparece');
    assert(await page.locator('#sinopsis').isVisible(), 'print: sinopsis desaparece');
    verifyErrors();
    report.accessibility.reducedMotion = true;
    report.accessibility.print = true;
    await context.close();
  }

  for (const shot of [
    { url: '/libros/', width: 1440, height: 1000, file: 'libros-1440.png' },
    { url: '/las-manecillas-del-recuerdo/', width: 1440, height: 1000, file: 'manecillas-1440.png' },
    { url: '/las-manecillas-del-recuerdo/', width: 390, height: 900, file: 'manecillas-390.png' },
    { url: '/las-manecillas-del-recuerdo/fragmentos/', width: 390, height: 900, file: 'fragmentos-390.png' }
  ]) {
    const context = await browser.newContext({ viewport: { width: shot.width, height: shot.height } });
    const page = await context.newPage();
    await page.goto(`${ORIGIN}${shot.url}`, { waitUntil: 'load' });
    await page.screenshot({ path: path.join(ROOT, OUT, shot.file), fullPage: false });
    await context.close();
  }
} finally {
  await browser.close();
}

writeReport();
console.log('CONTENT PARITY MANECILLAS QA: PASS');
