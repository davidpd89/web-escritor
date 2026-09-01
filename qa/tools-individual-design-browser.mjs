import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const BASE = process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const OUT = path.resolve(process.env.QA_OUT || 'qa-artifacts/tools-individual-design');

const TOOL_BLUE = 'rgb(29, 79, 150)';
const TOOL_BLUE_DEEP = 'rgb(13, 44, 87)';
const TOOL_GOLD = 'rgb(184, 134, 11)';

// Un representante por arquetipo (contrato TOOLS-INDIVIDUAL-VISUAL-UNIFICATION-2026-08-31):
// 1) textarea/analisis simple, 2) workspace complejo, 3) formulario multiopcion,
// 4) tabla/exportacion, 5) recurso fuera de /herramientas/, 6) visualizacion propia.
const representatives = [
  '/herramientas/contador-palabras/',
  '/herramientas/manuscrito/',
  '/herramientas/que-tipo-de-lector-eres/',
  '/herramientas/json-ld-escritores/',
  '/clubes-de-lectura/preparar-sesion/',
  '/recursos/ficha-historia-objeto-heredado/',
  '/herramientas/variedad-lexica/',
];

const outOfScope = ['/herramientas/', '/asistente/', '/editoriales/', '/convocatorias-escritores/', '/metodologia-editorial/'];

const viewports = [
  { width: 360, height: 800, key: '360' },
  { width: 390, height: 900, key: '390' },
  { width: 768, height: 1024, key: '768' },
  { width: 1440, height: 900, key: '1440' },
];

await fs.mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });

async function checkChrome(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: debe cargar 200`);

  const hasIdentity = await page.locator('link[href="/assets/v1-tools-identity.css"]').count();
  assert.equal(hasIdentity, 1, `${route}: debe cargar la capa de identidad v1-tools-identity.css`);

  const h1Color = await page.locator('.tool-hero h1').evaluate(el => getComputedStyle(el).color);
  assert.equal(h1Color, TOOL_BLUE, `${route}: h1 debe usar el azul editorial (${h1Color})`);

  const eyebrow = page.locator('.tool-hero .eyebrow');
  if (await eyebrow.count()) {
    const eyebrowColor = await eyebrow.evaluate(el => getComputedStyle(el).color);
    assert.equal(eyebrowColor, TOOL_GOLD, `${route}: eyebrow debe usar el dorado editorial (${eyebrowColor})`);
  }

  const note = page.locator('.tool-note').first();
  if (await note.count()) {
    const noteBorder = await note.evaluate(el => getComputedStyle(el).borderLeftColor);
    assert.equal(noteBorder, TOOL_BLUE, `${route}: tool-note no debe seguir con el azul legacy (${noteBorder})`);
  }

  // Los valores numericos del ledger no deben recolorearse: conservan semantica neutra.
  const summaryValue = page.locator('.tool-summary dd, .tool-summary > div > strong').first();
  if (await summaryValue.count()) {
    const valueColor = await summaryValue.evaluate(el => getComputedStyle(el).color);
    assert.notEqual(valueColor, TOOL_BLUE, `${route}: los valores del ledger no deben recolorearse de azul`);
    assert.notEqual(valueColor, TOOL_GOLD, `${route}: los valores del ledger no deben recolorearse de dorado`);
  }

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.equal(overflow, 0, `${route}: no debe haber overflow horizontal en 1440 (${overflow}px)`);

  await context.close();
}

async function checkTrustAndTable(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });

  const trust = page.locator('.tool-trust span').first();
  if (await trust.count()) {
    const border = await trust.evaluate(el => getComputedStyle(el).borderColor);
    assert.equal(border, TOOL_BLUE, `${route}: tool-trust debe usar el azul editorial (${border})`);
  }

  const table = page.locator('.tool-table thead th').first();
  if (await table.count()) {
    const border = await table.evaluate(el => getComputedStyle(el).borderBottomColor);
    assert.equal(border, TOOL_BLUE_DEEP, `${route}: cabecera de tabla debe usar el azul profundo (${border})`);
  }

  await context.close();
}

async function checkIsolation(route) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const response = await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' });
  assert.ok(response?.ok(), `${route}: debe cargar 200`);
  const hasIdentity = await page.locator('link[href="/assets/v1-tools-identity.css"]').count();
  assert.equal(hasIdentity, 0, `${route}: NO debe cargar v1-tools-identity.css (fuera de alcance #280)`);
  await context.close();
}

async function checkResponsive(route) {
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
  for (const route of representatives) await checkChrome(route);
  for (const route of representatives) await checkTrustAndTable(route);
  for (const route of outOfScope) await checkIsolation(route);
  for (const route of representatives) await checkResponsive(route);
  console.log('PASS tools individual design QA');
} finally {
  await browser.close();
}
