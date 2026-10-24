import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import fs from 'node:fs';

const origin = process.env.QA_ORIGIN || 'http://127.0.0.1:4173';
const data = JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json', 'utf8'));
const browser = await chromium.launch({ headless: true, ...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.QA_CHROMIUM_EXECUTABLE_PATH } : {}) });
try {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  await context.addInitScript(today => { window.__DP_RADAR_TODAY__ = today; }, data.generated_for);
  const page = await context.newPage();
  const response = await page.goto(`${origin}/convocatorias-escritores/`, { waitUntil: 'load' });
  assert.ok(response?.ok());
  const search = page.locator('[data-radar-search]');
  const count = page.locator('[data-radar-count]');
  const items = page.locator('[data-radar-item]:visible');
  const initial = await items.count();
  assert.ok(initial > 0, 'El radar no tiene fichas iniciales');
  async function verify(label) {
    const visible = await items.count();
    const text = (await count.textContent()).trim();
    assert.match(text, new RegExp(`^${visible} convocatori(?:a|as) visible(?:s)?$`), `${label}: contador incoherente: ${text}`);
    assert.equal(await page.locator('[data-radar-filter-empty]').isVisible(), visible === 0, `${label}: estado vacío incoherente`);
  }
  await verify('inicio');
  await search.fill('zzzzsinresultados987654');
  await verify('sin resultados');
  assert.equal(await items.count(), 0);
  await page.locator('[data-radar-empty-clear]').click();
  await verify('limpiar vacío');
  assert.equal(await search.inputValue(), '');
  assert.equal(await items.count(), initial);
  const type = page.locator('[data-radar-type]');
  const values = await type.locator('option').evaluateAll(nodes => nodes.map(n => n.value).filter(Boolean));
  if (values.length) {
    await type.selectOption(values[0]);
    await verify('tipo');
    await search.fill('zzzzsinresultados987654');
    await verify('tipo más búsqueda');
    await page.locator('[data-radar-clear]').click();
    await verify('limpieza global');
    assert.equal(await type.inputValue(), '');
    assert.equal(await items.count(), initial);
  }
  await context.close();
  console.log('PASS: filtros combinados y recuperación');
} finally {
  await browser.close();
}
