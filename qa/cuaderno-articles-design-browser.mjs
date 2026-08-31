import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve(process.env.QA_OUT || 'qa-artifacts/cuaderno-articles-design');

const CUADERNO_BLUE = 'rgb(29, 79, 150)';
const CUADERNO_GOLD = 'rgb(184, 134, 11)';

const articles = [
  '/cuaderno/que-es-el-portal-fantasy/',
  '/cuaderno/portal-fantasy-vs-fantasia-epica/',
  '/cuaderno/fantasia-juvenil-espanola-portales-magia-coste/',
  '/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/',
  '/cuaderno/worldbuilding-noveris-ciudad-magica/',
];

const topics = ['/cuaderno/temas/', '/cuaderno/temas/fantasia-de-portales/'];

const viewports = [
  { width: 390, height: 900, key: '390' },
  { width: 768, height: 1024, key: '768' },
  { width: 1440, height: 900, key: '1440' },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function checkArticleHeader(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: debe cargar 200`);

  const header = await page.locator('.article-header h1, .article-header .eyebrow, .article-prose > p:first-of-type').evaluateAll(nodes => nodes.map(n => ({
    tag: n.tagName,
    cls: n.className,
    color: getComputedStyle(n).color,
    fontFamily: getComputedStyle(n).fontFamily,
  })));
  const h1 = header.find(n => n.tag === 'H1');
  const eyebrow = header.find(n => n.cls.includes('eyebrow'));
  assert.equal(h1.color, CUADERNO_BLUE, `${route}: h1 debe usar el azul editorial (${h1.color})`);
  assert.equal(eyebrow.color, CUADERNO_GOLD, `${route}: eyebrow debe usar el dorado editorial (${eyebrow.color})`);
  assert.match(eyebrow.fontFamily, /Yellowtail/, `${route}: eyebrow debe usar Yellowtail (${eyebrow.fontFamily})`);

  const dropCapColor = await page.locator('.article-prose > p:first-of-type').evaluate(el => getComputedStyle(el, '::first-letter').color);
  assert.equal(dropCapColor, CUADERNO_BLUE, `${route}: capitular debe usar el azul editorial, no el azul legacy (${dropCapColor})`);

  const proseColor = await page.locator('.article-prose > p').first().evaluate(el => getComputedStyle(el).color);
  assert.notEqual(proseColor, CUADERNO_BLUE, `${route}: la prosa no debe recolorearse de azul`);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(overflow, 0, `${route}: no debe haber overflow horizontal en 1440 (${overflow}px)`);

  await context.close();
}

async function checkTopics(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: debe cargar 200`);

  const h1Color = await page.locator('.cuaderno-topics-hero h1').evaluate(el => getComputedStyle(el).color);
  const eyebrow = await page.locator('.cuaderno-topics-hero .eyebrow').evaluate(el => ({
    color: getComputedStyle(el).color,
    fontFamily: getComputedStyle(el).fontFamily,
  }));
  assert.equal(h1Color, CUADERNO_BLUE, `${route}: h1 debe usar el azul editorial (${h1Color})`);
  assert.equal(eyebrow.color, CUADERNO_GOLD, `${route}: eyebrow debe usar el dorado editorial (${eyebrow.color})`);
  assert.match(eyebrow.fontFamily, /Yellowtail/, `${route}: eyebrow debe usar Yellowtail (${eyebrow.fontFamily})`);

  const entryLinkColor = await page.locator('.cuaderno-topics-entry__body h2 a, .cuaderno-topic-step__body h2 a').first().evaluate(el => getComputedStyle(el).color);
  assert.equal(entryLinkColor, CUADERNO_BLUE, `${route}: los enlaces de la lista deben usar el azul editorial (${entryLinkColor})`);

  await context.close();
}

async function checkResponsive(route, isTopics) {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.equal(overflow, 0, `${route}: overflow horizontal en ${viewport.key}px (${overflow}px)`);
    await page.screenshot({ path: path.join(OUT, `${route.replace(/\//g, '_')}${viewport.key}.png`), fullPage: true });
    await context.close();
  }
}

try {
  for (const route of articles) await checkArticleHeader(route);
  for (const route of topics) await checkTopics(route);
  for (const route of [...articles, ...topics]) await checkResponsive(route);
  console.log('PASS cuaderno articles + topics design QA');
} finally {
  await browser.close();
}
