import assert from 'node:assert/strict';
import fs from 'node:fs';
import { chromium } from 'playwright';

const ORIGIN = process.env.QA_ORIGIN || process.env.QA_BASE_URL || 'http://127.0.0.1:4173';
const data = JSON.parse(fs.readFileSync('convocatorias-escritores/opportunities.json','utf8'));
const records = [...data.items, ...(data.watchlist || []), ...(data.expired || [])];
const browser = await chromium.launch({headless:true,...(process.env.QA_CHROMIUM_EXECUTABLE_PATH ? {executablePath:process.env.QA_CHROMIUM_EXECUTABLE_PATH} : {})});
try {
  const page = await browser.newPage();
  const response = await page.goto(`${ORIGIN}/convocatorias-escritores/`, {waitUntil:'domcontentloaded'});
  assert.ok(response?.ok(), '/convocatorias-escritores/: HTTP incorrecto');
  const cards = page.locator('[data-radar-item]');
  assert.equal(await cards.count(), records.length, '/convocatorias-escritores/: número de fichas diferente del JSON público');
  for (let i=0; i<records.length; i++) {
    const record = records[i];
    const card = cards.nth(i);
    const links = card.locator('a[data-radar-source]');
    assert.equal(await links.count(), 1, `/convocatorias-escritores/: ${record.title}: fuente ausente o duplicada`);
    const link = links.first();
    const name = await link.evaluate(el => {
      const labelledby = el.getAttribute('aria-labelledby');
      if (labelledby) return labelledby.split(/\s+/).map(id => document.getElementById(id)?.textContent || '').join(' ').trim();
      return (el.getAttribute('aria-label') || el.textContent || '').trim();
    });
    assert.ok(name, `/convocatorias-escritores/: ${record.title}: enlace sin nombre accesible`);
    assert.ok(name.toLocaleLowerCase('es').includes(record.title.toLocaleLowerCase('es')), `/convocatorias-escritores/: ${record.title}: nombre accesible sin identidad de convocatoria: ${name}`);
  }
} finally { await browser.close(); }