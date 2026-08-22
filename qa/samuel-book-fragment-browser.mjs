import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const OUT = process.env.QA_OUT || 'qa-artifacts/samuel-ecosystem';
const BASE_SHA = process.env.PR_BASE_SHA || process.env.BASE_SHA;
const VIEWPORTS = [
  [320, 900], [390, 900], [768, 1000], [1024, 900],
  [1440, 1000], [1728, 1000], [844, 390],
];
const ROUTES = [
  ['/libros/samuel-entre-mundos/', 'https://davidportodiaz.com/libros/samuel-entre-mundos/'],
  ['/fragmento/', 'https://davidportodiaz.com/fragmento/'],
];

await fs.mkdir(OUT, { recursive: true });

// The literary chapter is immutable in this task.
if (BASE_SHA) {
  const current = await fs.readFile('fragmento/index.html', 'utf8');
  const before = execFileSync('git', ['show', `${BASE_SHA}:fragmento/index.html`], { encoding: 'utf8' });
  const pattern = /<article class="fragment-reading fragment-text" data-nosnippet>([\s\S]*?)<\/article>/;
  const currentText = current.match(pattern)?.[1];
  const baseText = before.match(pattern)?.[1];
  assert.ok(currentText && baseText, 'fragment literary article missing');
  assert.equal(currentText, baseText, 'fragment literary prose changed byte-for-byte');
}

const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
const failures = [];
const check = (condition, message) => { if (!condition) failures.push(message); };

function watch(page) {
  const errors = [];
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
  return errors;
}

async function overflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
}

async function open(context, route) {
  const page = await context.newPage();
  const errors = watch(page);
  const response = await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
  check(response?.ok(), `${route}: HTTP ${response?.status()}`);
  await page.waitForTimeout(150);
  return { page, errors };
}

for (const [width, height] of VIEWPORTS) {
  for (const [route, canonical] of ROUTES) {
    const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' });
    const { page, errors } = await open(context, route);
    check(await overflow(page) <= 1, `${route} ${width}x${height}: horizontal overflow ${await overflow(page)}px`);
    check(await page.locator('h1').count() === 1, `${route} ${width}x${height}: H1 count`);
    check(await page.locator('link[rel="canonical"]').getAttribute('href') === canonical, `${route} ${width}x${height}: canonical drift`);
    check((await page.locator('meta[name="robots"]').getAttribute('content') || '').startsWith('index, follow'), `${route} ${width}x${height}: robots drift`);
    check(errors.length === 0, `${route} ${width}x${height}: ${errors.join(' | ')}`);
    if ((width === 390 || width === 1440) && height !== 390) {
      const name = route.includes('fragmento') ? 'fragmento' : 'samuel';
      await page.screenshot({ path: path.join(OUT, `${name}-${width}x${height}.png`), fullPage: true });
    }
    await context.close();
  }
}

// Book schema, verified commerce and ecosystem routes.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  const { page, errors } = await open(context, '/libros/samuel-entre-mundos/');
  const book = await page.evaluate(() => {
    const docs = [...document.querySelectorAll('script[type="application/ld+json"]')]
      .map(node => { try { return JSON.parse(node.textContent); } catch { return null; } })
      .filter(Boolean);
    const nodes = docs.flatMap(doc => Array.isArray(doc['@graph']) ? doc['@graph'] : [doc]);
    return nodes.find(node => node['@type'] === 'Book') || null;
  });
  check(book?.isbn === '9791387659776', 'book schema: ISBN');
  check(book?.datePublished === '2025', 'book schema: publication year');
  check(book?.numberOfPages === 422, 'book schema: pages');
  check(!Object.hasOwn(book || {}, 'award'), 'book schema: unverified Juan Andrés Teno attribution');
  check(!Object.hasOwn(book || {}, 'aggregateRating'), 'book schema: aggregate rating must remain absent');
  check(!Object.hasOwn(book || {}, 'typicalAgeRange'), 'book schema: age range must remain absent');

  const publisher = page.locator('#comprar a[href="https://librosindie.net/product/samuel-entre-mundos/"]');
  const amazon = page.locator('#comprar a[href="https://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21"]');
  const casa = page.locator('#comprar a[href^="https://www.casadellibro.com/libro-samuel-entre-mundos/9791387659776"]');
  check(await publisher.count() === 1, 'commerce: publisher URL missing');
  check(await amazon.count() === 1, 'commerce: Amazon URL missing');
  check(await casa.count() === 1, 'commerce: Casa del Libro URL missing');
  const amazonRel = new Set(((await amazon.getAttribute('rel')) || '').split(/\s+/));
  for (const token of ['sponsored', 'nofollow', 'noopener', 'noreferrer']) check(amazonRel.has(token), `commerce: Amazon rel missing ${token}`);
  for (const href of ['/fragmento/', '/universo/noveris/', '/clubes-de-lectura/samuel-entre-mundos/']) {
    check(await page.locator(`a[href="${href}"]`).count() > 0, `book ecosystem link missing: ${href}`);
  }
  check(errors.length === 0, `book contract: ${errors.join(' | ')}`);
  await context.close();
}

// innerText devuelve el texto *renderizado*, y .quiz-step-label lleva
// text-transform:uppercase, asi que lo que llega es "PREGUNTA 1 DE 5" y la
// comparacion contra "Pregunta 1 de 5" no casaba nunca: el quiz funciona, lo
// que fallaba era la comparacion. Se compara sin distinguir mayusculas para no
// atar la QA a una decision tipografica del CSS.
const stepLabel = async (page) => (await page.locator('[data-quiz-step]').innerText()).toLocaleLowerCase('es');
const stepIs = async (page, n) => (await stepLabel(page)).includes(`pregunta ${n} de 5`);
// Quiz: five questions, keyboard, result, explicit share and reset. No quiz-triggered network.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, hasTouch: true });
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'share', { configurable: true, value: async payload => { globalThis.__qaShare = payload; } });
  });
  const page = await context.newPage();
  const errors = watch(page);
  const external = [];
  page.on('request', request => {
    const url = new URL(request.url());
    if (url.origin !== locationOriginForQA(request.url(), ORIGIN)) external.push({ url: request.url(), method: request.method() });
  });
  await page.goto(`${ORIGIN}/libros/samuel-entre-mundos/#quiz-noveris`, { waitUntil: 'load' });
  await page.waitForTimeout(200);
  const baselineExternal = external.length;
  check(await page.locator('[data-samuel-quiz]').count() === 1, 'quiz: local app missing');
  check(await page.locator('#quiz-subscribe-form').count() === 0, 'quiz: newsletter form must be absent');
  check((await page.locator('#quiz-noveris').innerText()).includes('no se envían a terceros'), 'quiz: local privacy disclosure missing');

  for (let index = 0; index < 5; index += 1) {
    check(await stepIs(page, index + 1), `quiz: step ${index + 1}`);
    const options = page.locator('[data-quiz-options] .quiz-option');
    check(await options.count() === 4, `quiz: question ${index + 1} option count`);
    const target = options.first();
    const box = await target.boundingBox();
    check(Boolean(box && box.height >= 44), `quiz: touch target below 44px on question ${index + 1}`);
    await target.focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(30);
  }
  check(await page.locator('[data-quiz-result]').isVisible(), 'quiz: result not visible');
  const result = (await page.locator('[data-quiz-result-name]').innerText()).trim();
  check(['El Mensajero', 'El Sabio del Espejo', 'La Silenciadora', 'El Guardián'].includes(result), `quiz: invalid result ${result}`);
  check(await page.locator('[data-quiz-result]').evaluate(el => el === document.activeElement), 'quiz: focus must move to result');
  check(external.length === baselineExternal, `quiz: interaction caused external network ${JSON.stringify(external.slice(baselineExternal))}`);

  await page.locator('[data-quiz-share]').click();
  const shared = await page.evaluate(() => globalThis.__qaShare?.text || '');
  check(shared.includes('/libros/samuel-entre-mundos/#quiz-noveris'), `quiz: shared URL drift ${shared}`);
  check(!shared.includes('/universo/noveris/#quiz'), 'quiz: stale share URL');
  check(external.length === baselineExternal, 'quiz: explicit share mock caused network');

  await page.locator('[data-quiz-restart]').click();
  check(await page.locator('[data-quiz-result]').isHidden(), 'quiz: result not hidden after reset');
  check(await stepIs(page, 1), 'quiz: reset did not return to question 1');
  check(await page.locator('[data-quiz-options] .quiz-option').first().evaluate(el => el === document.activeElement), 'quiz: reset focus');
  check(errors.length === 0, `quiz: ${errors.join(' | ')}`);
  await context.close();
}

function locationOriginForQA(_url, origin) {
  return new URL(origin).origin;
}

// Fragment: full reading remains reachable and global reading progress still works.
{
  const context = await browser.newContext({ viewport: { width: 390, height: 900 } });
  const { page, errors } = await open(context, '/fragmento/');
  check(await page.locator('.fragment-reading.fragment-text[data-nosnippet]').count() === 1, 'fragment: literary article missing');
  check((await page.locator('.fragment-reading').innerText()).length > 5000, 'fragment: literary text unexpectedly short');
  check(await page.locator('a[href="/libros/samuel-entre-mundos/"]').count() > 0, 'fragment: route back to book missing');
  check(await page.locator('.reading-progress').count() === 1, 'fragment: reading progress missing');
  await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight * 0.65));
  await page.waitForTimeout(150);
  const width = await page.locator('.reading-progress').evaluate(el => parseFloat(el.style.width) || 0);
  check(width > 20, `fragment: reading progress did not advance (${width})`);
  check(errors.length === 0, `fragment: ${errors.join(' | ')}`);
  await context.close();
}

// No-JS: book/fragment stay useful; quiz explains its limitation rather than becoming a dead blank widget.
for (const route of ['/libros/samuel-entre-mundos/', '/fragmento/']) {
  const context = await browser.newContext({ viewport: { width: 390, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(`${ORIGIN}${route}`, { waitUntil: 'load' });
  check(await page.locator('h1').isVisible(), `${route} no-JS: H1 unavailable`);
  check(await overflow(page) <= 1, `${route} no-JS: overflow ${await overflow(page)}px`);
  if (route.includes('samuel-entre-mundos')) {
    check((await page.locator('noscript').innerText()).includes('necesita JavaScript'), 'book no-JS: quiz fallback missing');
    check(await page.locator('a[href="/fragmento/"]').count() > 0, 'book no-JS: fragment route missing');
  } else {
    check((await page.locator('.fragment-reading').innerText()).length > 5000, 'fragment no-JS: literary text unavailable');
  }
  await context.close();
}

// 200% text and WCAG text-spacing pressure on both routes.
for (const [label, css] of [
  ['text-200', 'html{font-size:200% !important}'],
  ['text-spacing', '*{line-height:1.5 !important;letter-spacing:.12em !important;word-spacing:.16em !important}p{margin-bottom:2em !important}'],
]) {
  for (const [route] of ROUTES) {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    const { page, errors } = await open(context, route);
    await page.addStyleTag({ content: css });
    await page.waitForTimeout(100);
    check(await overflow(page) <= 1, `${route} ${label}: overflow ${await overflow(page)}px`);
    check(errors.length === 0, `${route} ${label}: ${errors.join(' | ')}`);
    await context.close();
  }
}

await browser.close();
if (failures.length) {
  console.error('Samuel book/fragment browser QA FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}
console.log('samuel-book-fragment-browser: OK (2 routes, 7 viewports, local quiz, fragment parity, no-JS, reflow)');
