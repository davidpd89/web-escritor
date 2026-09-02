import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve(process.env.QA_OUT || 'qa-artifacts/editoriales-detail');

const EDITORIAL_BLUE = 'rgb(29, 79, 150)';

// Las 3 fichas reales, no una representante: el contrato exige cubrirlas
// todas porque el estado factual difiere (Minotauro/Nocturna abiertas,
// Duermevela cerrada) — ver data/editoriales.json.
const routes = [
  { path: '/editoriales/minotauro/', name: 'Minotauro', status: 'Acepta manuscritos' },
  { path: '/editoriales/nocturna-ediciones/', name: 'Nocturna Ediciones', status: 'Acepta manuscritos' },
  { path: '/editoriales/duermevela-ediciones/', name: 'Duermevela Ediciones', status: 'Recepción cerrada' },
];

const outOfScope = ['/editoriales/', '/convocatorias-escritores/', '/metodologia-editorial/'];

const viewports = [
  { width: 320, height: 800, key: '320' },
  { width: 360, height: 800, key: '360' },
  { width: 390, height: 900, key: '390' },
  { width: 768, height: 1024, key: '768' },
  { width: 1024, height: 900, key: '1024' },
  { width: 1280, height: 900, key: '1280' },
  { width: 1440, height: 900, key: '1440' },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function checkFacts(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route.path}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route.path}: debe cargar 200`);

  const hasIdentity = await page.locator('link[href^="/assets/v1-editoriales-detail.css"]').count();
  assert.equal(hasIdentity, 1, `${route.path}: debe cargar v1-editoriales-detail.css`);

  const h1 = await page.locator('.tool-hero h1').innerText();
  assert.equal(h1, route.name, `${route.path}: h1 debe ser el nombre exacto de la editorial (${h1})`);
  const h1Color = await page.locator('.tool-hero h1').evaluate(el => getComputedStyle(el).color);
  assert.equal(h1Color, EDITORIAL_BLUE, `${route.path}: h1 debe usar el azul editorial (${h1Color})`);

  const eyebrowColor = await page.locator('.tool-hero .eyebrow').evaluate(el => getComputedStyle(el).color);
  assert.equal(eyebrowColor, 'rgb(184, 134, 11)', `${route.path}: eyebrow debe usar el dorado editorial (${eyebrowColor})`);

  // El estado debe leerse como texto, no solo como color (contrato: sin
  // semaforo de app). Comprobamos el texto exacto del badge de estado.
  const statusText = await page.locator('.editorial-fact:has(dt:text-is("Estado de originales")) dd').innerText();
  assert.equal(statusText, route.status, `${route.path}: estado de originales no coincide con el dataset (${statusText})`);

  const sources = await page.locator('.tool-source-list a').count();
  assert.ok(sources > 0, `${route.path}: debe listar al menos una fuente`);

  const verifiedAt = await page.locator('.editorial-fact:has(dt:text-is("Última comprobación")) time').getAttribute('datetime');
  assert.match(verifiedAt || '', /^\d{4}-\d{2}-\d{2}$/, `${route.path}: fecha de verificación ausente o mal formada`);

  const canonical = await page.locator('link[rel="canonical"]').getAttribute('href');
  assert.equal(canonical, `https://davidportodiaz.com${route.path}`, `${route.path}: canonical incorrecto (${canonical})`);

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(overflow, 0, `${route.path}: overflow horizontal en 1440 (${overflow}px)`);

  await context.close();
}

async function checkNoJs(route) {
  const context = await browser.newContext({ viewport: { width: 1024, height: 900 }, javaScriptEnabled: false });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route.path}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route.path}: debe cargar 200 sin JS`);
  const h1 = await page.locator('.tool-hero h1').innerText();
  assert.equal(h1, route.name, `${route.path}: h1 debe renderizar sin JS (${h1})`);
  const sourcesVisible = await page.locator('.tool-source-list a').first().isVisible();
  assert.ok(sourcesVisible, `${route.path}: fuentes deben ser visibles sin JS`);
  await context.close();
}

async function checkIsolation(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: debe cargar 200`);
  const hasIdentity = await page.locator('link[href^="/assets/v1-editoriales-detail.css"]').count();
  assert.equal(hasIdentity, 0, `${route}: NO debe cargar v1-editoriales-detail.css (fuera de alcance #281)`);
  await context.close();
}

async function checkResponsive(route) {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height } });
    const page = await context.newPage();
    await page.goto(`${BASE}${route.path}`, { waitUntil: 'domcontentloaded' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.equal(overflow, 0, `${route.path}: overflow horizontal en ${viewport.key}px (${overflow}px)`);
    await page.screenshot({ path: path.join(OUT, `${route.path.replace(/\//g, '_')}${viewport.key}.png`), fullPage: true });
    await context.close();
  }
}

async function checkZoomAndTextSpacing(route) {
  // Mismo patron que qa/awards-evidence-browser.mjs: 200% de zoom se simula
  // con font-size, no con la propiedad CSS zoom (que no refluye de forma fiable).
  {
    // bypassCSP: la ficha exige style-src 'self' en producción; addStyleTag
    // inyecta un <style> inline que solo el arnés de QA necesita saltarse.
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, bypassCSP: true });
    const page = await context.newPage();
    await page.goto(`${BASE}${route.path}`, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: 'html{font-size:200% !important}' });
    await page.waitForTimeout(100);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 1, `${route.path}: overflow horizontal a zoom 200% (${overflow}px)`);
    await context.close();
  }
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, bypassCSP: true });
    const page = await context.newPage();
    await page.goto(`${BASE}${route.path}`, { waitUntil: 'domcontentloaded' });
    await page.addStyleTag({ content: '*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important;} p{margin-bottom:2em!important;}' });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.ok(overflow <= 1, `${route.path}: overflow horizontal con text-spacing WCAG (${overflow}px)`);
    await context.close();
  }
}

try {
  for (const route of routes) await checkFacts(route);
  for (const route of routes) await checkNoJs(route);
  for (const route of outOfScope) await checkIsolation(route);
  for (const route of routes) await checkResponsive(route);
  for (const route of routes) await checkZoomAndTextSpacing(route);
  console.log('PASS editoriales detail QA');
} finally {
  await browser.close();
}
